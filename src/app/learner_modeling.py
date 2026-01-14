import os
from typing import Optional, TypedDict

import pandas as pd

from .data_loader import load_student_data

# --- Define State structures for clarity ---


class MasteryVector(TypedDict):
    """
    Represents the student's mastery of a specific topic.
    Implements a simplified Bayesian Knowledge Tracing (BKT) concept.
    """

    # P(L): Probability that the learner knows the skill. We use normalized score.
    probability_known: float
    # P(T): Probability of transitioning from not-known to known. Fixed for simplicity.
    probability_transit: float
    # P(S): Probability of slipping (making a mistake when knowing the skill).
    probability_slip: float
    # P(G): Probability of guessing correctly when not knowing theskill.
    probability_guess: float


class LearnerState(TypedDict):
    """The output of this node, to be merged into the main AgentState."""

    mastery_vector: Optional[MasteryVector]
    requires_recap: bool
    enable_scaffolding: bool


# --- The Learner Modeling Node ---


def learner_modeling_node(state: dict) -> dict:
    """
    Analyzes student logs to build a dynamic mastery vector for a given topic.
    """
    print("---NODE: LEARNER MODELING---")

    student_id = state.get("student_id")
    topic_details = state.get("topic_details")

    if not student_id or not topic_details:
        print(
            "WARNING: Missing student_id or topic_details in state. Skipping modeling."
        )
        return {
            "mastery_vector": None,
            "requires_recap": False,
            "enable_scaffolding": False,
        }

    selected_topic = topic_details["selected_topic_title"]

    # 1. Load student's historical data
    scores_df, absences_df = load_student_data(student_id)

    # 2. Calculate Mastery for the selected topic
    topic_scores = scores_df[scores_df["topic_name"] == selected_topic]["score_numeric"]

    if not topic_scores.empty:
        # Normalize score from 0-12 to 0-1 scale to represent probability
        average_score = topic_scores.mean()
        mastery_prob = average_score / 12.0
    else:
        # If no scores, assume a default low starting probability (prior knowledge)
        mastery_prob = 0.25

    # 3. Check for absences on this topic
    requires_recap = not absences_df[absences_df["topic_name"] == selected_topic].empty

    # 4. Determine if Scaffolding is needed
    # If mastery is below 60% (approx < 7.2/12), enable step-by-step help
    enable_scaffolding = mastery_prob < 0.6

    # 5. Create the Mastery Vector (simplified BKT)
    mastery_vector = {
        "probability_known": mastery_prob,
        "probability_transit": 0.15,  # Fixed: Chance to learn in one step
        "probability_slip": 0.10,  # Fixed: Chance of error even if known
        "probability_guess": 0.20,  # Fixed: Chance of guessing right
    }

    print(f"Mastery for '{selected_topic}': {mastery_prob:.2f}")
    if requires_recap:
        print("RECAP REQUIRED due to absences.")
    if enable_scaffolding:
        print("SCAFFOLDING ENABLED due to low mastery.")

    return {
        "mastery_vector": mastery_vector,
        "requires_recap": requires_recap,
        "enable_scaffolding": enable_scaffolding,
    }


# --- Example Usage ---
if __name__ == "__main__":
    DATA_PATH = "data"
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    # Dummy data for a student who struggles with Algebra
    pd.DataFrame(
        {
            "student_id": [123, 123],
            "score_numeric": [5, 6],  # Average < 7
            "topic_name": ["Алгебра: Рівняння", "Алгебра: Рівняння"],
        }
    ).to_parquet(os.path.join(DATA_PATH, "benchmark_scores.parquet"))

    pd.DataFrame(
        {
            "student_id": [123],
            "absence_reason": ["Sick"],
            "topic_name": ["Алгебра: Рівняння"],  # Missed this topic
        }
    ).to_parquet(os.path.join(DATA_PATH, "benchmark_absences.parquet"))

    os.environ["DATA_PATH"] = DATA_PATH

    print("\n--- Testing Learner Modeling Node ---")

    # Simulate the state after the topic router has run
    initial_state = {
        "student_id": 123,
        "topic_details": {
            "selected_topic_title": "Алгебра: Рівняння",
            # other fields from router...
        },
    }

    learner_state_output = learner_modeling_node(initial_state)

    print("\n--- Learner Modeling Output ---")
    import json

    print(json.dumps(learner_state_output, indent=2, ensure_ascii=False))

    # Clean up
    os.remove(os.path.join(DATA_PATH, "benchmark_scores.parquet"))
    os.remove(os.path.join(DATA_PATH, "benchmark_absences.parquet"))
    if DATA_PATH == "data":
        os.rmdir(DATA_PATH)
