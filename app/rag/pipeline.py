"""
RAG Grounded Generation Pipeline for CloudSage.
Retrieves relevant knowledge chunks, constructs grounded prompts,
and formats answers with verified source citations.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.rag.retriever import get_retriever, KnowledgeRetriever
from app.rag.vector_store import SearchResult


class SourceCitation(BaseModel):
    title: str
    source: str
    category: str
    url: str
    score: float


class RAGResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceCitation] = Field(default_factory=list)
    retrieved_chunks: List[SearchResult] = Field(default_factory=list)
    retrieval_used: bool = True
    data_source: str = "knowledge_base"


class RAGPipeline:
    """
    Retrieves knowledge context and executes grounded response generation.
    """

    def __init__(self, retriever: Optional[KnowledgeRetriever] = None):
        self.retriever = retriever or get_retriever()

    def generate(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.05
    ) -> RAGResponse:
        """
        Executes full RAG workflow: Retrieve -> Ground -> Cite.
        """
        # 1. Retrieve relevant chunks
        chunks = self.retriever.retrieve(query, top_k=top_k, min_score=min_score)

        if not chunks:
            return RAGResponse(
                query=query,
                answer="I searched the CloudSage AWS Knowledge Base, but could not find specific documentation matching your query. Please verify the cloud topic or ask about EC2, S3, CloudWatch, IAM, or Cost Optimization.",
                sources=[],
                retrieved_chunks=[],
                retrieval_used=True,
                data_source="knowledge_base"
            )

        # 2. Extract unique source citations
        unique_sources: Dict[str, SourceCitation] = {}
        for c in chunks:
            if c.title not in unique_sources:
                unique_sources[c.title] = SourceCitation(
                    title=c.title,
                    source=c.source,
                    category=c.category,
                    url=c.url,
                    score=c.score
                )
        sources_list = list(unique_sources.values())

        # 3. Synthesize grounded answer
        answer = self._synthesize_grounded_answer(query, chunks)

        return RAGResponse(
            query=query,
            answer=answer,
            sources=sources_list,
            retrieved_chunks=chunks,
            retrieval_used=True,
            data_source="knowledge_base"
        )

    def _synthesize_grounded_answer(self, query: str, chunks: List[SearchResult]) -> str:
        """
        Synthesizes a clear, well-structured, authoritative explanation grounded in retrieved chunks.
        """
        from app.config import get_settings
        settings = get_settings()

        # Build grounding context block
        context_blocks = []
        for i, c in enumerate(chunks, 1):
            context_blocks.append(f"--- Document [{i}]: {c.title} ({c.category}) ---\nSource: {c.source}\n{c.content}")
        combined_context = "\n\n".join(context_blocks)

        # Check if OpenAI / Gemini is configured for live LLM generation
        if settings.LLM_PROVIDER in ["openai", "gemini"]:
            api_key = settings.OPENAI_API_KEY if settings.LLM_PROVIDER == "openai" else settings.GEMINI_API_KEY
            if api_key and (api_key.startswith("sk-") or api_key.startswith("AIza")):
                try:
                    from app.ai.llm import get_llm_client
                    llm = get_llm_client()
                    grounded_system = (
                        "You are CloudSage, an expert AWS cloud operations assistant. "
                        "Answer the user's question accurately using ONLY the provided AWS Documentation Context below. "
                        "Do NOT invent facts not present in the context. "
                        "Format your response with clear Markdown headings, bullet points, and bold text."
                    )
                    prompt = f"AWS Documentation Context:\n{combined_context}\n\nUser Question:\n{query}"
                    return llm._call_direct_generation(system_prompt=grounded_system, user_prompt=prompt)
                except Exception:
                    pass  # Fallback to local grounded synthesis

        # Deterministic local grounded synthesis
        return self._local_grounded_synthesis(query, chunks)

    def _local_grounded_synthesis(self, query: str, chunks: List[SearchResult]) -> str:
        """
        Constructs an informative, structured explanation from the top retrieved knowledge chunks.
        """
        primary = chunks[0]
        paragraphs = [p.strip() for p in primary.content.split("\n\n") if p.strip()]

        parts = [f"### 📖 {primary.title}"]
        
        # Primary summary
        if paragraphs:
            parts.append(paragraphs[0])

        # Additional detailed sections / points
        for para in paragraphs[1:]:
            parts.append(para)

        # If there are supplementary chunks from other documents, append relevant insights
        supplementary = [c for c in chunks[1:] if c.document_id != primary.document_id]
        if supplementary:
            parts.append("\n**Related Cloud Concepts & Best Practices:**")
            for supp in supplementary[:2]:
                supp_paras = [p.strip() for p in supp.content.split("\n\n") if p.strip()]
                summary_line = supp_paras[0] if supp_paras else supp.content[:150]
                parts.append(f"- **{supp.title}**: {summary_line}")

        return "\n\n".join(parts)


_pipeline_singleton: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Singleton accessor for RAGPipeline."""
    global _pipeline_singleton
    if _pipeline_singleton is None:
        _pipeline_singleton = RAGPipeline()
    return _pipeline_singleton
