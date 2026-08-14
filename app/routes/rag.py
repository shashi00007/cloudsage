"""
RAG (Knowledge Search) API Routes for CloudSage.
Provides endpoints for direct semantic search against the local AWS knowledge base.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.rag.retriever import get_retriever
from app.rag.pipeline import get_rag_pipeline

rag_router = APIRouter()


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    category: str
    source: str
    url: str
    score: float
    content: str


class KnowledgeSearchResponse(BaseModel):
    query: str
    count: int
    results: List[SearchResultItem]


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language AWS knowledge question")
    top_k: int = Field(default=3, ge=1, le=10)


class KnowledgeQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    data_source: str = "knowledge_base"


@rag_router.get("/search", response_model=KnowledgeSearchResponse, summary="Direct Semantic Search in AWS Knowledge Base")
async def search_knowledge(
    q: str = Query(..., description="Search query or keyword phrase", min_length=1),
    top_k: int = Query(default=3, ge=1, le=10, description="Maximum number of chunks to return")
):
    """
    Performs semantic vector search against curated AWS cloud documentation chunks.
    """
    try:
        retriever = get_retriever()
        results = retriever.retrieve(query=q, top_k=top_k)
        
        items = [
            SearchResultItem(
                chunk_id=r.chunk_id,
                document_id=r.document_id,
                title=r.title,
                category=r.category,
                source=r.source,
                url=r.url,
                score=r.score,
                content=r.content
            )
            for r in results
        ]

        return KnowledgeSearchResponse(
            query=q,
            count=len(items),
            results=items
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge retrieval error: {str(exc)}")


@rag_router.post("/query", response_model=KnowledgeQueryResponse, summary="Grounded Knowledge Question Answering")
async def query_knowledge(request: KnowledgeQueryRequest):
    """
    Answers a cloud architecture, security, or FinOps question using grounded RAG.
    """
    try:
        pipeline = get_rag_pipeline()
        rag_resp = pipeline.generate(query=request.query, top_k=request.top_k)
        
        return KnowledgeQueryResponse(
            query=rag_resp.query,
            answer=rag_resp.answer,
            sources=[s.model_dump() for s in rag_resp.sources],
            data_source=rag_resp.data_source
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG generation error: {str(exc)}")
