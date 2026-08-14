"""
Vector Store for CloudSage RAG Knowledge Base.
Provides in-memory cosine similarity search and persistent serialization to disk.
"""

import json
import os
import math
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.rag.chunker import DocumentChunk


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    category: str
    source: str
    url: str
    content: str
    score: float
    keywords: List[str] = Field(default_factory=list)


class VectorRecord(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    category: str
    source: str
    url: str
    content: str
    keywords: List[str] = Field(default_factory=list)
    embedding: List[float]


class VectorStore:
    """
    Lightweight vector store with cosine similarity ranking and file-based persistence.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "./data/vector_store"
        self._records: List[VectorRecord] = []

    def count(self) -> int:
        """Returns the number of indexed chunks."""
        return len(self._records)

    def clear(self) -> None:
        """Clears all records in the vector store."""
        self._records = []

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        """
        Adds document chunks along with their precomputed embeddings to the store.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunk count ({len(chunks)}) does not match embedding count ({len(embeddings)})")

        for chunk, emb in zip(chunks, embeddings):
            record = VectorRecord(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                title=chunk.title,
                category=chunk.category,
                source=chunk.source,
                url=chunk.url,
                content=chunk.content,
                keywords=chunk.keywords,
                embedding=emb
            )
            self._records.append(record)

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 3,
        min_score: float = 0.05
    ) -> List[SearchResult]:
        """
        Performs semantic cosine similarity search against indexed vector records.
        """
        if not self._records:
            return []

        scored_results: List[SearchResult] = []

        for rec in self._records:
            sim = self._cosine_similarity(query_vector, rec.embedding)
            if sim >= min_score:
                scored_results.append(SearchResult(
                    chunk_id=rec.chunk_id,
                    document_id=rec.document_id,
                    title=rec.title,
                    category=rec.category,
                    source=rec.source,
                    url=rec.url,
                    content=rec.content,
                    score=round(float(sim), 4),
                    keywords=rec.keywords
                ))

        # Sort descending by similarity score
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:top_k]

    def save(self, directory_path: Optional[str] = None) -> str:
        """
        Serializes indexed records and metadata to index.json.
        """
        target_dir = Path(directory_path or self.storage_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        index_file = target_dir / "index.json"

        data = {
            "version": "1.0",
            "total_chunks": len(self._records),
            "records": [r.model_dump() for r in self._records]
        }

        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return str(index_file)

    def load(self, directory_path: Optional[str] = None) -> bool:
        """
        Loads vector store index from index.json if present.
        """
        target_dir = Path(directory_path or self.storage_path)
        index_file = target_dir / "index.json"

        if not index_file.exists():
            return False

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_records = data.get("records", [])
            self._records = [VectorRecord(**r) for r in raw_records]
            return True
        except Exception:
            return False
