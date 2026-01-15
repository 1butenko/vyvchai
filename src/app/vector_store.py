import os

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from .lapa_config import get_lapa_embeddings

from .data_loader import load_textbook_pages


def create_vector_store():
    """
    Creates an in-memory vector store from the textbook pages.

    Returns:
        An InMemoryVectorStore instance.
    """
    # Ensure the GOOGLE_API_KEY is set
    # Ensure the GOOGLE_API_KEY is set - DEPRECATED for Lapa
    # if "GOOGLE_API_KEY" not in os.environ:
    #     raise ValueError("GOOGLE_API_KEY environment variable not set.")

    # Load the textbook pages
    pages_df = load_textbook_pages()

    # Create LangChain Document objects
    documents = []
    for _, row in pages_df.iterrows():
        metadata = {
            "book_page_number": row["book_page_number"],
            "topic_title": row["topic_title"],
            "global_discipline_id": row["global_discipline_id"],
        }
        doc = Document(page_content=row["page_text"], metadata=metadata)
        documents.append(doc)

    # Initialize the embedding model
    embeddings = get_lapa_embeddings()

    # Create the in-memory vector store
    vector_store = InMemoryVectorStore.from_documents(documents, embedding=embeddings)

    return vector_store


if __name__ == "__main__":
    # Example usage:
    # Make sure to set the GOOGLE_API_KEY environment variable
    # For example:
    # os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"

    # Create a dummy data directory and file for testing
    DATA_PATH = "data"
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    # Dummy textbook data
    pages_df = pd.DataFrame(
        {
            "page_text": [
                "Intro to AI.",
                "Deep Learning basics.",
                "Natural Language Processing.",
            ],
            "book_page_number": [10, 25, 50],
            "topic_title": ["Artificial Intelligence", "Neural Networks", "NLP"],
            "global_discipline_id": ["CS101", "CS202", "CS303"],
        }
    )
    pages_df.to_parquet(os.path.join(DATA_PATH, "pages_for_hackathon (gemini).parquet"))

    os.environ["DATA_PATH"] = DATA_PATH

    # This part will fail if GOOGLE_API_KEY is not set.
    # You need a valid key to test the embedding and vector store creation.
    if os.environ.get("GOOGLE_API_KEY"):
        print("--- Creating vector store ---")
        vector_store = create_vector_store()
        print("Vector store created successfully.")

        print("\n--- Performing a similarity search ---")
        query = "What is artificial intelligence?"
        results = vector_store.similarity_search(query, k=1)

        print(f"Query: '{query}'")
        print("Top result:")
        for doc in results:
            print(f"  Page Content: {doc.page_content}")
            print(f"  Metadata: {doc.metadata}")
    else:
        print("Skipping vector store creation because GOOGLE_API_KEY is not set.")

    # Clean up dummy files
    os.remove(os.path.join(DATA_PATH, "pages_for_hackathon (gemini).parquet"))
    if DATA_PATH == "data":
        os.rmdir(DATA_PATH)
