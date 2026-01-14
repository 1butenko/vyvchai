import ast
import os
from typing import List, Optional, TypedDict

import numpy as np
import pandas as pd
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

# --- Pre-load data and models for efficiency ---

DATA_PATH = os.environ.get("DATA_PATH", "data")
TOC_FILE_PATH = os.path.join(DATA_PATH, "toc_for_hackathon_with_subtopics.parquet")

print("Loading TOC data for Topic Router...")
try:
    TOC_DF = pd.read_parquet(TOC_FILE_PATH)
    # Stack all topic embeddings into a single matrix for fast computation
    TOC_EMBEDDINGS = np.vstack(TOC_DF["topic_embedding"].values)
    print("TOC data loaded successfully.")
except FileNotFoundError:
    print(f"ERROR: TOC file not found at {TOC_FILE_PATH}. The router will not work.")
    TOC_DF = pd.DataFrame()  # Empty dataframe to prevent crashes

# Initialize the embedding model once
if os.environ.get("GOOGLE_API_KEY"):
    EMBEDDING_MODEL = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
else:
    print(
        "WARNING: GOOGLE_API_KEY not set. Topic router will not be able to embed queries."
    )
    EMBEDDING_MODEL = None


# --- Define State structures ---
# This helps with type hinting and clarity
class TopicDetails(TypedDict):
    selected_topic_title: str
    subtopics_list: List[str]
    topic_start_page: int
    topic_end_page: int


class RouterState(TypedDict):
    """Input state for the router node."""

    messages: List[object]  # Using generic object for simplicity
    grade: int
    global_discipline_id: int
    # The output of this node will be added to the main AgentState
    topic_details: Optional[TopicDetails]


# --- The Router Node ---


def topic_router_node(state: RouterState) -> dict:
    """
    Acts as a ToolPlanner to find the most relevant topic for a given query.
    Performs a filtered semantic search on the Table of Contents.
    """
    print("---NODE: TOPIC ROUTER---")
    if TOC_DF.empty or EMBEDDING_MODEL is None:
        print("ERROR: Node cannot operate. Missing data or model.")
        return {"topic_details": None}

    user_query = state["messages"][-1].content
    grade = state["grade"]
    discipline_id = state["global_discipline_id"]

    # 1. Filter the DataFrame based on grade and discipline
    filtered_df = TOC_DF[
        (TOC_DF["grade"] == grade) & (TOC_DF["global_discipline_id"] == discipline_id)
    ].copy()

    if filtered_df.empty:
        print(
            f"WARNING: No topics found for grade={grade} and discipline={discipline_id}."
        )
        return {"topic_details": None}

    # 2. Get embeddings for the filtered topics
    filtered_indices = filtered_df.index
    filtered_embeddings = TOC_EMBEDDINGS[filtered_indices]

    # 3. Embed the user's query
    query_embedding = EMBEDDING_MODEL.embed_query(user_query)

    # 4. Perform semantic search
    similarities = cosine_similarity([query_embedding], filtered_embeddings)[0]
    best_match_index_in_filtered = np.argmax(similarities)

    # Get the original index from the filtered DataFrame
    original_index = filtered_df.index[best_match_index_in_filtered]

    # 5. Extract the details of the winning topic
    best_topic_series = TOC_DF.loc[original_index]

    # Safely parse the subtopics list (it's stored as a string)
    try:
        subtopics = ast.literal_eval(best_topic_series.get("subtopics", "[]"))
    except (ValueError, SyntaxError):
        subtopics = []

    # 6. Prepare the result to be added to the main agent state
    topic_details = {
        "selected_topic_title": best_topic_series.get("topic_title"),
        "subtopics_list": subtopics,
        "topic_start_page": best_topic_series.get("topic_start_page"),
        "topic_end_page": best_topic_series.get("topic_end_page"),
    }

    print(
        f"Query '{user_query}' routed to topic: '{topic_details['selected_topic_title']}'"
    )
    return {"topic_details": topic_details}


# --- Example Usage ---
if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    # Create dummy data for a full run
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    # Dummy TOC data
    dummy_toc_df = pd.DataFrame(
        {
            "topic_title": [
                "Вступ до Алгебри",
                "Рівняння",
                "Історія України: Визвольна війна",
            ],
            "grade": [8, 8, 9],
            "global_discipline_id": [72, 72, 107],
            "topic_embedding": [np.random.rand(768) for _ in range(3)],
            "subtopics": [
                "['Змінні', 'Константи']",
                "['Лінійні', 'Квадратні']",
                "['Передумови', 'Наслідки']",
            ],
            "topic_start_page": [5, 20, 150],
            "topic_end_page": [19, 45, 175],
        }
    )
    dummy_toc_df.to_parquet(TOC_FILE_PATH)

    if os.environ.get("GOOGLE_API_KEY"):
        print("\n--- Testing Topic Router Node ---")

        # Reload the router's data with the dummy file
        TOC_DF = pd.read_parquet(TOC_FILE_PATH)
        TOC_EMBEDDINGS = np.vstack(TOC_DF["topic_embedding"].values)

        # Simulate an initial state for an 8th grader studying Algebra
        initial_state = {
            "messages": [HumanMessage(content="Як розв'язувати квадратні рівняння?")],
            "grade": 8,
            "global_discipline_id": 72,
            "topic_details": None,  # Initially empty
        }

        router_output = topic_router_node(initial_state)

        print("\n--- Router Output ---")
        import json

        print(json.dumps(router_output, indent=2, ensure_ascii=False))

    else:
        print("\nSkipping router test: GOOGLE_API_KEY is not set.")

    # Clean up
    os.remove(TOC_FILE_PATH)
    if DATA_PATH == "data":
        os.rmdir(DATA_PATH)
