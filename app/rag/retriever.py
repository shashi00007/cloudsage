"""
Retriever Module for CloudSage RAG Knowledge Base.
Provides semantic retrieval over indexed AWS documentation chunks.
"""

from typing import List, Optional
from app.config import get_settings
from app.rag.embeddings import get_embedding_model, BaseEmbeddings
from app.rag.vector_store import VectorStore, SearchResult


class KnowledgeRetriever:
    """
    Retrieves the most relevant AWS documentation chunks for a given query.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_model: Optional[BaseEmbeddings] = None
    ):
        settings = get_settings()
        self.embedding_model = embedding_model or get_embedding_model()
        
        if vector_store is not None:
            self.vector_store = vector_store
        else:
            self.vector_store = VectorStore(storage_path=settings.VECTOR_STORE_PATH)
            # Try to load existing index
            loaded = self.vector_store.load()
            if not loaded or self.vector_store.count() == 0:
                # Lazy auto-ingest if index file not built yet
                from app.rag.ingest import build_knowledge_base
                build_knowledge_base(self.vector_store, self.embedding_model)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.05
    ) -> List[SearchResult]:
        """
        Retrieves top-k relevant document chunks for the input query string.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        # Generate query embedding
        query_vector = self.embedding_model.embed_text(clean_query)

        # Query vector store
        results = self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            min_score=min_score
        )

        return results


_retriever_singleton: Optional[KnowledgeRetriever] = None


def get_retriever() -> KnowledgeRetriever:
    """Singleton accessor for KnowledgeRetriever."""
    global _retriever_singleton
    if _retriever_singleton is None:
        _retriever_singleton = KnowledgeRetriever()
    return _retriever_singleton
