from typing import Any, Dict, List, Optional

import structlog

from src.app.vector_store import create_vector_store
from src.core.config import get_settings

logger = structlog.get_logger()


class RAGTool:
    """
    Tool for retrieving relevant context from vector store.
    """

    def __init__(self):
        settings = get_settings()
        self.vector_store = None

        if settings.QDRANT_URL:
            try:
                self.vector_store = create_vector_store()
                logger.info("rag_tool_initialized")
            except Exception as e:
                logger.error("rag_tool_initialization_failed", error=str(e))

    async def retrieve_context(
        self,
        query: str,
        subject: str,
        grade: int,
        matched_topics: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from vector store.

        Args:
            query: Search query
            subject: Subject filter
            grade: Grade filter
            matched_topics: Topic filters
            limit: Max results

        Returns:
            List of retrieved documents
        """
        if not self.vector_store:
            logger.warning("rag_tool_not_available")
            return []

        try:
            # Build search filter
            search_kwargs = {"k": limit}

            # Add filters if available
            filter_conditions = {}
            if matched_topics:
                filter_conditions["topic_title"] = {"$in": matched_topics}

            if filter_conditions:
                search_kwargs["filter"] = filter_conditions

            # Perform search
            results = self.vector_store.similarity_search(query, **search_kwargs)

            # Format results
            documents = []
            for doc in results:
                metadata = doc.metadata
                documents.append(
                    {
                        "content": doc.page_content,
                        "source": f"Page {metadata.get('book_page_number', 'N/A')}",
                        "topic": metadata.get("topic_title", "N/A"),
                        "subject": subject,
                        "grade": grade,
                        "score": getattr(doc, "score", None),  # If available
                    }
                )

            logger.info("rag_retrieval_completed", count=len(documents))

            return documents

        except Exception as e:
            logger.error("rag_retrieval_failed", error=str(e))
            return []
