"""
Embedding Provider Abstraction for CloudSage RAG.
Supports fast deterministic local semantic embeddings and pluggable OpenAI embeddings.
"""

import abc
import math
import re
import hashlib
from typing import List, Optional
import httpx

from app.config import get_settings


class BaseEmbeddings(abc.ABC):
    """Abstract Base Class for text embedding models."""

    @abc.abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generates an embedding vector for a single query text."""
        pass

    @abc.abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a batch of document texts."""
        pass

    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        """Returns the dimensionality of the embedding vectors."""
        pass


class LocalSemanticEmbeddings(BaseEmbeddings):
    """
    Lightweight, deterministic local semantic embedding engine.
    Uses subword n-gram hashing and term-frequency projection with L2 normalization.
    Requires 0 external downloads, 0 GPUs, 0 C++ binaries, and runs in <1ms.
    """

    def __init__(self, dim: int = 384):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def _tokenize_and_hash(self, text: str) -> List[float]:
        vector = [0.0] * self._dim
        clean_text = text.lower()
        # Extract word tokens
        words = re.findall(r"[a-z0-9_\-\.]+", clean_text)
        if not words:
            return vector

        # Build feature weights (words + character 3-grams)
        features = {}
        for w in words:
            features[w] = features.get(w, 0.0) + 1.5
            # Subword character trigrams for semantic prefix/suffix matching
            if len(w) >= 3:
                for i in range(len(w) - 2):
                    tri = w[i:i+3]
                    features[tri] = features.get(tri, 0.0) + 0.5

        for feat, weight in features.items():
            # Deterministic MD5 hash to 2 projection buckets
            h = hashlib.md5(feat.encode("utf-8")).digest()
            idx1 = int.from_bytes(h[:4], "big") % self._dim
            idx2 = int.from_bytes(h[4:8], "big") % self._dim
            sign = 1.0 if (h[8] % 2 == 0) else -1.0
            
            vector[idx1] += weight
            vector[idx2] += sign * (weight * 0.5)

        # L2 Vector Normalization
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [round(x / norm, 6) for x in vector]

        return vector

    def embed_text(self, text: str) -> List[float]:
        return self._tokenize_and_hash(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._tokenize_and_hash(t) for t in texts]


class OpenAIEmbeddings(BaseEmbeddings):
    """
    OpenAI text-embedding-3-small provider.
    """

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self._dim = 1536

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        res = self.embed_documents([text])
        return res[0] if res else [0.0] * self._dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": texts
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        embeddings = [item["embedding"] for item in data["data"]]
        return embeddings


_embedding_singleton: Optional[BaseEmbeddings] = None


def get_embedding_model() -> BaseEmbeddings:
    """
    Factory returning the configured embedding provider.
    Defaults to LocalSemanticEmbeddings for deterministic, zero-cost operation.
    """
    global _embedding_singleton
    if _embedding_singleton is None:
        settings = get_settings()
        openai_key = settings.OPENAI_API_KEY or settings.LLM_API_KEY
        if openai_key and openai_key.startswith("sk-") and settings.LLM_PROVIDER == "openai":
            try:
                _embedding_singleton = OpenAIEmbeddings(api_key=openai_key)
            except Exception:
                _embedding_singleton = LocalSemanticEmbeddings()
        else:
            _embedding_singleton = LocalSemanticEmbeddings()
    return _embedding_singleton
