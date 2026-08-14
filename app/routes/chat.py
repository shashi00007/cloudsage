"""
Chat Route Handler for CloudSage GenAI Operations & Knowledge Assistant.
Exposes the POST /api/chat endpoint for natural language interactions.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.agent import CloudSageAgent

router = APIRouter(tags=["Chat"])

# Agent Singleton
_agent_instance: Optional[CloudSageAgent] = None


def get_agent() -> CloudSageAgent:
    """Returns the shared CloudSage agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = CloudSageAgent()
    return _agent_instance


# ==============================================================================
# Schemas
# ==============================================================================

class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User question, operational query, or cloud knowledge inquiry")
    session_id: Optional[str] = Field(default=None, description="Optional session UUID for conversation memory")


class ChatMessageResponse(BaseModel):
    answer: str
    tools_used: List[str] = []
    data_source: str = "mock"
    sources: List[Dict[str, Any]] = []
    retrieval_used: bool = False
    session_id: str
    tool_results: List[Any] = []


class ResetSessionRequest(BaseModel):
    session_id: str


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post("/chat", response_model=ChatMessageResponse)
async def chat_endpoint(payload: ChatMessageRequest) -> ChatMessageResponse:
    """
    Primary GenAI assistant endpoint.
    Processes user questions, automatically calls appropriate AWS tools,
    performs RAG knowledge retrieval from official AWS documentation when needed,
    and returns a factual natural language response with source citations.
    """
    user_msg = payload.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    agent = get_agent()
    result = agent.ask(message=user_msg, session_id=payload.session_id)

    return ChatMessageResponse(
        answer=result.get("answer", ""),
        tools_used=result.get("tools_used", []),
        data_source=result.get("data_source", "mock"),
        sources=result.get("sources", []),
        retrieval_used=result.get("retrieval_used", False),
        session_id=result.get("session_id", ""),
        tool_results=result.get("tool_results", [])
    )


@router.post("/chat/reset")
async def reset_chat_session(payload: ResetSessionRequest):
    """
    Clears the conversation memory for a given session ID.
    """
    agent = get_agent()
    cleared = agent.clear_session(payload.session_id)
    return {"success": cleared, "message": "Conversation memory reset"}
