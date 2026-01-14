import os

# Assuming vector_store is created and available.
from .vector_store import create_vector_store

# Initialize the vector store once when the module is loaded.
print("Initializing vector store for RAG node...")
if os.environ.get("GOOGLE_API_KEY"):
    VECTOR_STORE = create_vector_store()
    print("Vector store initialized.")
else:
    VECTOR_STORE = None
    print("WARNING: GOOGLE_API_KEY not set. RAG node will not work.")


def retrieve_context_node(state: dict) -> dict:
    """
    Performs a filtered similarity search in the vector store.
    """
    print("---NODE: RETRIEVING CONTEXT---")
    if VECTOR_STORE is None:
        print("ERROR: Vector store not initialized.")
        return {"context": "Помилка: Векторна база даних не ініціалізована."}

    user_query = state["messages"][-1].content
    topic_details = state.get("topic_details")

    # Build a filter for the search
    search_kwargs = {"k": 3}
    if topic_details:
        start_page = topic_details.get("topic_start_page")
        end_page = topic_details.get("topic_end_page")
        if start_page is not None and end_page is not None:
            print(f"Applying filter: pages {start_page}-{end_page}")
            search_kwargs["filter"] = {
                "book_page_number": {"$gte": start_page, "$lte": end_page}
            }

    # Perform the similarity search with the filter
    results = VECTOR_STORE.similarity_search(user_query, **search_kwargs)

    # Format the results
    context_parts = []
    for doc in results:
        metadata = doc.metadata
        source_str = f"Джерело: стор. {metadata.get('book_page_number', 'N/A')}"
        topic_str = f"Тема: {metadata.get('topic_title', 'N/A')}"
        text_str = f"Текст: {doc.page_content}"
        context_parts.append(f"{source_str}, {topic_str}\n{text_str}")

    formatted_context = (
        "\n\n".join(context_parts)
        if context_parts
        else "На жаль, релевантної інформації в підручнику не знайдено."
    )

    print(f"Retrieved context:\n{formatted_context}")
    return {"context": formatted_context}


if __name__ == "__main__":
    # Example usage requires GOOGLE_API_KEY and dummy data
    pass
