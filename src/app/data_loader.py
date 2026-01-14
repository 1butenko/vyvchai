import os

import pandas as pd

# Assume DATA_PATH is set as an environment variable, default to 'data' for local testing
DATA_PATH = os.environ.get("DATA_PATH", "data")


def load_textbook_pages():
    """
    Loads the 'pages_for_hackathon (gemini).parquet' file.
    """
    file_path = os.path.join(DATA_PATH, "pages_for_hackathon (gemini).parquet")
    columns_to_load = [
        "page_text",
        "book_page_number",
        "topic_title",
        "global_discipline_id",
    ]
    df = pd.read_parquet(file_path, engine="pyarrow", columns=columns_to_load)
    return df


def load_student_data(student_id: int):
    """
    Loads benchmark scores and absences for a specific student_id using filtering.
    """
    scores_path = os.path.join(DATA_PATH, "benchmark_scores.parquet")
    absences_path = os.path.join(DATA_PATH, "benchmark_absences.parquet")

    filters = [("student_id", "==", student_id)]

    try:
        scores_df = pd.read_parquet(
            scores_path,
            filters=filters,
            engine="pyarrow",
            columns=["score_numeric", "topic_name"],
        )
    except Exception:
        # If file or columns don't exist, return an empty DataFrame with expected columns
        scores_df = pd.DataFrame(columns=["score_numeric", "topic_name"])

    try:
        absences_df = pd.read_parquet(
            absences_path,
            filters=filters,
            engine="pyarrow",
            columns=["absence_reason", "topic_name"],
        )
    except Exception:
        absences_df = pd.DataFrame(columns=["absence_reason", "topic_name"])

    return scores_df, absences_df


if __name__ == "__main__":
    # Example usage:
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    # Dummy data
    pd.DataFrame(
        {
            "page_text": ["Intro to AI."],
            "book_page_number": [10],
            "topic_title": ["AI"],
            "global_discipline_id": ["CS101"],
        }
    ).to_parquet(os.path.join(DATA_PATH, "pages_for_hackathon (gemini).parquet"))

    pd.DataFrame(
        {
            "student_id": [123, 123],
            "score_numeric": [5, 8],
            "topic_name": ["Алгебра: Рівняння", "Алгебра: Функції"],
        }
    ).to_parquet(os.path.join(DATA_PATH, "benchmark_scores.parquet"))

    pd.DataFrame(
        {
            "student_id": [123],
            "absence_reason": ["Sick"],
            "topic_name": ["Алгебра: Рівняння"],
        }
    ).to_parquet(os.path.join(DATA_PATH, "benchmark_absences.parquet"))

    print("--- Loading data for student_id=123 ---")
    student_scores, student_absences = load_student_data(student_id=123)

    print("\nScores:")
    print(student_scores)

    print("\nAbsences:")
    print(student_absences)

    # Clean up
    os.remove(os.path.join(DATA_PATH, "pages_for_hackathon (gemini).parquet"))
    os.remove(os.path.join(DATA_PATH, "benchmark_scores.parquet"))
    os.remove(os.path.join(DATA_PATH, "benchmark_absences.parquet"))
    if DATA_PATH == "data":
        os.rmdir(DATA_PATH)
