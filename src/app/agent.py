import os
import json
from typing import TypedDict, Annotated, List, Optional, Literal
import operator

from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# Import all our custom nodes
from .topic_router_node import topic_router_node, TopicDetails
from .learner_modeling import learner_modeling_node, MasteryVector
from .solver_validator_node import solver_validator_node, GeneratedTask, ValidationResult

# --- 1. Define the unified Agent State ---
class AgentState(TypedDict):
    """The complete, unified state for the AI Tutor agent with a feedback loop."""
    messages: Annotated[List[AnyMessage], operator.add]
    student_id: int
    grade: int
    global_discipline_id: int
    
    # Node outputs
    topic_details: Optional[TopicDetails]
    mastery_vector: Optional[MasteryVector]
    generated_tasks: Optional[List[GeneratedTask]]
    
    # State for the validation loop
    validation_status: Optional[Literal["VALIDATED", "REGENERATE"]]
    feedback_for_regeneration: Optional[List[dict]]
    validated_tasks: Optional[List[GeneratedTask]]

# --- 2. Initialize the LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)

# --- 3. Define Graph Nodes ---

def task_generator_node(state: AgentState) -> dict:
    """
    Placeholder node to generate tasks.
    In a real scenario, this would use an LLM.
    """
    print("---NODE: TASK GENERATOR---")
    
    # If the solver requested regeneration, print the feedback
    if state.get("feedback_for_regeneration"):
        print("Regenerating tasks based on feedback:")
        print(state["feedback_for_regeneration"])

    # For this example, we generate dummy tasks, including one with a wrong key
    # to trigger the validation loop.
    print("Generating a new set of tasks...")
    tasks = [
        {"task_text": "Знайди x, якщо 2x + 3 = 11.", "answer_key": "4"},
        {"task_text": "Знайди x, якщо x^2 - 16 = 0.", "answer_key": "4"}, # Deliberately incorrect key
        {"task_text": "Спрости вираз: 2(a+b) - 2a", "answer_key": "2b"}
    ]
    
    return {"generated_tasks": tasks}

def present_tasks_node(state: AgentState) -> dict:
    """
    Final node to present the validated tasks to the user.
    """
    print("---NODE: PRESENTING VALIDATED TASKS---")
    validated_tasks = state.get("validated_tasks", [])
    
    if not validated_tasks:
        final_message = "На жаль, не вдалося згенерувати коректні завдання."
    else:
        tasks_str = "\n".join([f"- {t['task_text']}" for t in validated_tasks])
        final_message = f"Ось кілька завдань для тебе:\n{tasks_str}"
        
    print(final_message)
    return {"messages": [HumanMessage(content=final_message)]}

def decide_after_validation(state: AgentState) -> str:
    """
    Conditional edge to decide whether to regenerate tasks or finish.
    """
    print("---DECISION: AFTER VALIDATION---")
    if state.get("validation_status") == "REGENERATE":
        print("Decision: Regenerate tasks.")
        return "regenerate"
    else:
        print("Decision: Tasks are valid. Present to student.")
        return "present"

# --- 4. Build the final graph with the feedback loop ---
workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("topic_router", topic_router_node)
workflow.add_node("learner_modeling", learner_modeling_node)
workflow.add_node("task_generator", task_generator_node)
workflow.add_node("solver_validator", solver_validator_node)
workflow.add_node("present_tasks", present_tasks_node)

# Define the execution flow
workflow.set_entry_point("topic_router")
workflow.add_edge("topic_router", "learner_modeling")
# For this example, we assume we always generate tasks for algebra
workflow.add_edge("learner_modeling", "task_generator")
workflow.add_edge("task_generator", "solver_validator")

# Add the conditional feedback loop
workflow.add_conditional_edges(
    "solver_validator",
    decide_after_validation,
    {
        "regenerate": "task_generator",  # Go back to regenerate
        "present": "present_tasks"       # Move forward
    }
)
workflow.add_edge("present_tasks", END)

# Compile the graph
app = workflow.compile()

# --- Example Usage ---
if __name__ == '__main__':
    if os.environ.get("GOOGLE_API_KEY") and os.path.exists("data/toc_for_hackathon_with_subtopics.parquet"):
        print("\n--- Running Agent with Solver/Validator Loop ---")
        
        # Simulate a state for an 8th grader studying Algebra
        initial_state = {
            "messages": [HumanMessage(content="Дай мені кілька завдань на квадратні рівняння.")],
            "student_id": 123,
            "grade": 8,
            "global_discipline_id": 72, # Critical for triggering the solver
        }
        
        for output in app.stream(initial_state):
            for key, value in output.items():
                print(f"--- Output from node: {key} ---")
                if isinstance(value, dict):
                    print(json.dumps(value, indent=2, ensure_ascii=False))
                else:
                    print(value)
                print("\n")
    else:
        print("\nSkipping pipeline test: GOOGLE_API_KEY not set or dummy data missing.")
        print("Please run `topic_router_node.py` and `learner_modeling.py` directly first to create dummy data.")
