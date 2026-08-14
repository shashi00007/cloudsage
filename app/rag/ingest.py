"""
Ingestion Pipeline for CloudSage RAG Knowledge Base.
Loads curated AWS documentation, chunks texts, computes semantic embeddings,
and builds the persistent local vector index.

Usage:
    python -m app.rag.ingest
"""

import sys
import logging
from typing import Optional, Tuple

from app.config import get_settings
from app.rag.documents import get_all_documents
from app.rag.chunker import DocumentChunker
from app.rag.embeddings import get_embedding_model, BaseEmbeddings
from app.rag.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cloudsage.rag.ingest")


def build_knowledge_base(
    vector_store: Optional[VectorStore] = None,
    embedding_model: Optional[BaseEmbeddings] = None
) -> Tuple[int, int, str]:
    """
    Builds or updates the persistent local vector store index from curated documents.
    Returns (num_documents, num_chunks, saved_index_path).
    """
    settings = get_settings()
    store = vector_store or VectorStore(storage_path=settings.VECTOR_STORE_PATH)
    embedder = embedding_model or get_embedding_model()

    # 1. Load documents
    documents = get_all_documents()
    num_docs = len(documents)
    logger.info(f"Loaded {num_docs} curated knowledge documents.")

    # 2. Split documents into semantic chunks
    chunker = DocumentChunker(target_chunk_size=180, chunk_overlap=40)
    chunks = chunker.chunk_documents(documents)
    num_chunks = len(chunks)
    logger.info(f"Generated {num_chunks} semantic chunks.")

    # 3. Compute vector embeddings
    chunk_texts = [f"{c.title} {c.category} {' '.join(c.keywords)} {c.content}" for c in chunks]
    embeddings = embedder.embed_documents(chunk_texts)
    logger.info(f"Computed {len(embeddings)} embedding vectors (dim={embedder.dimension}).")

    # 4. Populate and persist vector store
    store.clear()
    store.add_chunks(chunks, embeddings)
    saved_path = store.save()
    logger.info(f"Successfully saved vector store index to: {saved_path}")

    return num_docs, num_chunks, saved_path


if __name__ == "__main__":
    print("=== CloudSage RAG Knowledge Base Ingestion ===")
    num_docs, num_chunks, saved_path = build_knowledge_base()
    print(f"Ingestion complete: {num_docs} documents -> {num_chunks} chunks indexed.")
    print(f"Index location: {saved_path}")
