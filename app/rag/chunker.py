"""
Document Chunker for CloudSage RAG Knowledge Base.
Splits knowledge documents into semantic chunks with metadata preservation and overlap.
"""

from typing import List
from pydantic import BaseModel, Field
from app.rag.documents import KnowledgeDocument


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    category: str
    source: str
    url: str
    content: str
    keywords: List[str] = Field(default_factory=list)


class DocumentChunker:
    """
    Splits text documents into semantically coherent chunks with overlap.
    """

    def __init__(self, target_chunk_size: int = 180, chunk_overlap: int = 40):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: KnowledgeDocument) -> List[DocumentChunk]:
        """
        Splits a single KnowledgeDocument into one or more DocumentChunks.
        Uses paragraph and section boundary awareness.
        """
        text = document.content.strip()
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks: List[DocumentChunk] = []
        current_words: List[str] = []
        chunk_idx = 0

        for para in paragraphs:
            para_words = para.split()
            
            # If adding this paragraph exceeds target chunk size and we already have words
            if len(current_words) + len(para_words) > self.target_chunk_size and current_words:
                chunk_text = " ".join(current_words)
                chunks.append(DocumentChunk(
                    chunk_id=f"{document.document_id}_chunk_{chunk_idx}",
                    document_id=document.document_id,
                    title=document.title,
                    category=document.category,
                    source=document.source,
                    url=document.url,
                    content=chunk_text,
                    keywords=document.keywords
                ))
                chunk_idx += 1
                
                # Keep overlap from the end of current_words
                overlap_count = min(self.chunk_overlap, len(current_words))
                current_words = current_words[-overlap_count:] + para_words
            else:
                current_words.extend(para_words)

        # Remaining words
        if current_words:
            chunk_text = " ".join(current_words)
            chunks.append(DocumentChunk(
                chunk_id=f"{document.document_id}_chunk_{chunk_idx}",
                document_id=document.document_id,
                title=document.title,
                category=document.category,
                source=document.source,
                url=document.url,
                content=chunk_text,
                keywords=document.keywords
            ))

        return chunks

    def chunk_documents(self, documents: List[KnowledgeDocument]) -> List[DocumentChunk]:
        """
        Processes a list of KnowledgeDocuments into a flat list of DocumentChunks.
        """
        all_chunks: List[DocumentChunk] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks
