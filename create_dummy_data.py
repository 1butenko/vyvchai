import os
import pandas as pd
import numpy as np

DATA_PATH = "data"

def create_all_dummy_data():
    """
    Generates all necessary dummy .parquet files for the project to run.
    """
    print(f"Creating dummy data in '{DATA_PATH}' directory...")

    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    # --- 1. toc_for_hackathon_with_subtopics.parquet ---
    # For the topic_router_node
    toc_df = pd.DataFrame({
        "topic_title": ["Вступ до Алгебри", "Квадратні рівняння", "Історія України: Визвольна війна"],
        "grade": [8, 8, 9],
        "global_discipline_id": [72, 72, 107],
        # Gemini embeddings are 768-dimensional
        "topic_embedding": [np.random.rand(768).tolist() for _ in range(3)],
        "subtopics": ["['Змінні', 'Константи']", "['Дискримінант', 'Теорема Вієта']", "['Передумови', 'Наслідки']"],
        "topic_start_page": [5, 20, 150],
        "topic_end_page": [19, 45, 175],
    })
    toc_path = os.path.join(DATA_PATH, "toc_for_hackathon_with_subtopics.parquet")
    toc_df.to_parquet(toc_path)
    print(f"✅ Created '{os.path.basename(toc_path)}'")

    # --- 2. benchmark_scores.parquet ---
    # For the learner_modeling_node (low score scenario)
    scores_df = pd.DataFrame({
        "student_id": [123, 123],
        "score_numeric": [5, 6],  # Average < 7 to trigger scaffolding
        "topic_name": ["Квадратні рівняння", "Квадратні рівняння"]
    })
    scores_path = os.path.join(DATA_PATH, "benchmark_scores.parquet")
    scores_df.to_parquet(scores_path)
    print(f"✅ Created '{os.path.basename(scores_path)}'")

    # --- 3. benchmark_absences.parquet ---
    # For the learner_modeling_node (recap scenario)
    absences_df = pd.DataFrame({
        "student_id": [123],
        "absence_reason": ["Sick"],
        "topic_name": ["Квадратні рівняння"]  # Missed this topic
    })
    absences_path = os.path.join(DATA_PATH, "benchmark_absences.parquet")
    absences_df.to_parquet(absences_path)
    print(f"✅ Created '{os.path.basename(absences_path)}'")

    # --- 4. pages_for_hackathon (gemini).parquet ---
    # For the vector_store and RAG nodes
    pages_df = pd.DataFrame({
        "page_text": [
            "Квадратні рівняння — це рівняння виду ax^2 + bx + c = 0, де a ≠ 0.",
            "Для розв'язання квадратних рівнянь часто використовують дискримінант. Формула дискримінанта: D = b^2 - 4ac.",
            "Якщо D > 0, рівняння має два різні дійсні корені. Якщо D = 0, рівняння має один дійсний корінь. Якщо D < 0, рівняння не має дійсних коренів."
        ],
        "book_page_number": [21, 22, 23],  # Within the 20-45 page range from TOC
        "topic_title": ["Квадратні рівняння", "Квадратні рівняння", "Квадратні рівняння"],
        "global_discipline_id": [72, 72, 72],
    })
    pages_path = os.path.join(DATA_PATH, "pages_for_hackathon (gemini).parquet")
    pages_df.to_parquet(pages_path)
    print(f"✅ Created '{os.path.basename(pages_path)}'")
    
    print("\nDummy data generation complete. You can now run the main application.")

if __name__ == "__main__":
    create_all_dummy_data()
