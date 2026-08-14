"""
RAG (Retrieval-Augmented Generation) Knowledge Base for AWS Documentation.
"""

from app.rag.documents import KnowledgeDocument, get_all_documents, get_document_by_id
from app.rag.chunker import DocumentChunk, DocumentChunker
from app.rag.embeddings import BaseEmbeddings, LocalSemanticEmbeddings, OpenAIEmbeddings, get_embedding_model
from app.rag.vector_store import VectorStore, SearchResult, VectorRecord
from app.rag.retriever import KnowledgeRetriever, get_retriever
from app.rag.pipeline import RAGPipeline, RAGResponse, SourceCitation, get_rag_pipeline
from app.rag.ingest import build_knowledge_base

__all__ = [
    "KnowledgeDocument",
    "get_all_documents",
    "get_document_by_id",
    "DocumentChunk",
    "DocumentChunker",
    "BaseEmbeddings",
    "LocalSemanticEmbeddings",
    "OpenAIEmbeddings",
    "get_embedding_model",
    "VectorStore",
    "SearchResult",
    "VectorRecord",
    "KnowledgeRetriever",
    "get_retriever",
    "RAGPipeline",
    "RAGResponse",
    "SourceCitation",
    "get_rag_pipeline",
    "build_knowledge_base",
]
