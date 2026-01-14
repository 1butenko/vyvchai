import os

import phoenix as px
from dotenv import load_dotenv
from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import HumanMessage

# Load environment variables from .env file
load_dotenv()

# Import the compiled agent app from your existing agent file
# We assume the agent.py file contains the compiled `app`
from app.agent import app


def main():
    """
    Main function to run the AI Tutor agent with tracing and cost evaluation.
    """
    # 1. Initialize Phoenix for tracing
    # This will automatically start collecting traces if env vars are set
    print("🚀 Initializing Phoenix for tracing...")
    px.launch_app()
    print("Phoenix is running. Traces will be sent to the Phoenix UI.")

    # Simulate an initial state for the agent
    initial_state = {
        "messages": [
            HumanMessage(
                content="Розкажи мені про квадратні рівняння та дай кілька завдань."
            )
        ],
        "student_id": 123,
        "grade": 8,
        "global_discipline_id": 72,  # Algebra
    }

    # 2. Run the agent and evaluate token usage
    print("\n🤖 Running the AI Tutor agent...")

    total_tokens = 0
    total_cost = 0

    with get_openai_callback() as cb:
        # The `stream` method will execute the graph step-by-step
        for i, step in enumerate(app.stream(initial_state)):
            print(f"\n--- Iteration {i+1} ---")
            print(step)

        # After the run, the callback will have the token and cost info
        total_tokens = cb.total_tokens
        total_cost = cb.total_cost

    # 3. Print the cost evaluation report
    print("\n--- 📊 Cost Evaluation Report ---")
    print(f"Total Tokens Used: {total_tokens}")
    print(f"Estimated Cost (USD): ${total_cost:.6f}")
    print("------------------------------------")

    print(
        "\n✅ Agent run complete. Check Phoenix UI for detailed traces at http://localhost:6006"
    )
    print("Press Ctrl+C to exit.")

    # Keep the script running to allow Phoenix to send all data
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nExiting.")


if __name__ == "__main__":
    # Ensure all required dummy data exists before running
    # This is a placeholder for a real data check
    if not all(
        [
            os.path.exists("data/toc_for_hackathon_with_subtopics.parquet"),
            os.path.exists("data/benchmark_scores.parquet"),
            os.path.exists("data/benchmark_absences.parquet"),
            os.path.exists("data/pages_for_hackathon (gemini).parquet"),
        ]
    ):
        print(
            "ERROR: One or more required data files are missing in the 'data' directory."
        )
        print(
            "Please run the individual node files (`topic_router_node.py`, etc.) to create dummy data first."
        )
    else:
        main()
