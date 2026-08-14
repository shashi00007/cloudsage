"""
CloudSage GenAI Agent Orchestrator.
Manages tool-calling loops, RAG knowledge retrieval, multi-tool execution,
hybrid synthesis, and conversation memory context.
"""

import uuid
import logging
from typing import Any, Dict, List, Optional

from app.ai.llm import LLMClient, get_llm_client
from app.ai.tool_router import ToolRouter
from app.rag.pipeline import RAGPipeline, get_rag_pipeline

logger = logging.getLogger("cloudsage.agent")


class CloudSageAgent:
    """
    GenAI Cloud Operations & Knowledge Intelligence Assistant Agent.
    """

    def __init__(self, mock_mode: Optional[bool] = None):
        self.llm_client = get_llm_client()
        self.tool_router = ToolRouter(mock_mode=mock_mode)
        self.rag_pipeline = get_rag_pipeline()
        # In-memory session store: session_id -> { "messages": [...], "context": {...} }
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Ensures a valid session ID exists in memory."""
        sid = session_id or str(uuid.uuid4())
        if sid not in self._sessions:
            self._sessions[sid] = {
                "messages": [],
                "context": {
                    "last_instance_id": None,
                    "instances": [],
                    "last_tool": None
                }
            }
        return sid

    def clear_session(self, session_id: str) -> bool:
        """Resets the conversation history for a given session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def ask(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the agent workflow:
        1. Context loading
        2. Tool / RAG requirement determination
        3. Tool and/or RAG execution
        4. Grounded response synthesis with citations
        5. Memory persistence
        """
        sid = self.get_or_create_session(session_id)
        session_data = self._sessions[sid]
        messages = session_data["messages"]
        context_state = session_data["context"]

        # Append user message
        messages.append({"role": "user", "content": message})

        # Trim conversation window to last 10 messages for memory efficiency
        if len(messages) > 10:
            messages = messages[-10:]
            session_data["messages"] = messages

        tools = self.tool_router.get_available_tools()

        try:
            # 1. Ask LLM to determine tool calls, RAG retrieval, or conversational reply
            llm_response = self.llm_client.generate_tool_calls_or_response(
                messages=messages,
                tools=tools,
                context_state=context_state
            )

            # ------------------------------------------------------------------
            # Case A: Pure RAG Knowledge Query (No operational tools required)
            # ------------------------------------------------------------------
            if llm_response.is_knowledge_query and not llm_response.tool_calls:
                rag_query = llm_response.retrieval_query or message
                rag_result = self.rag_pipeline.generate(query=rag_query, top_k=3)
                
                messages.append({"role": "assistant", "content": rag_result.answer})
                return {
                    "answer": rag_result.answer,
                    "tools_used": [],
                    "data_source": "knowledge_base",
                    "sources": [s.model_dump() for s in rag_result.sources],
                    "retrieval_used": True,
                    "session_id": sid,
                    "tool_results": []
                }

            # ------------------------------------------------------------------
            # Case B: Direct Conversational Reply (No tools or RAG needed)
            # ------------------------------------------------------------------
            if not llm_response.tool_calls and not llm_response.is_knowledge_query:
                answer = llm_response.content or "How can I assist you with your AWS cloud operations or architecture today?"
                messages.append({"role": "assistant", "content": answer})
                return {
                    "answer": answer,
                    "tools_used": [],
                    "data_source": "system",
                    "sources": [],
                    "retrieval_used": False,
                    "session_id": sid,
                    "tool_results": []
                }

            # ------------------------------------------------------------------
            # Case C: Operational Tool Calls (Pure Tool or Hybrid Tool + RAG)
            # ------------------------------------------------------------------
            tools_used: List[str] = []
            tool_results: List[Dict[str, Any]] = []
            data_sources: List[str] = []

            for tc in llm_response.tool_calls:
                tool_name = tc.name
                tools_used.append(tool_name)
                
                # Execute operational tool
                res = self.tool_router.execute_tool(tool_name, tc.arguments)
                tool_results.append(res)
                data_sources.append(res.get("data_source", "mock"))

                # Update context state from tool output
                if tool_name == "inspect_ec2" and res.get("success"):
                    instances = res.get("data", {}).get("instances", [])
                    if instances:
                        context_state["instances"] = instances
                        context_state["last_instance_id"] = instances[0].get("instance_id")

                if tool_name == "get_cloudwatch_metrics" and tc.arguments.get("instance_id"):
                    context_state["last_instance_id"] = tc.arguments.get("instance_id")

                context_state["last_tool"] = tool_name

            # Check if RAG context is also needed for Hybrid synthesis
            rag_context_str: Optional[str] = None
            sources_list: List[Dict[str, Any]] = []
            retrieval_used = False

            if llm_response.is_knowledge_query or llm_response.retrieval_query:
                rag_query = llm_response.retrieval_query or message
                rag_result = self.rag_pipeline.generate(query=rag_query, top_k=2)
                rag_context_str = rag_result.answer
                sources_list = [s.model_dump() for s in rag_result.sources]
                retrieval_used = True

            # Synthesize final answer incorporating tool execution data & RAG context
            final_answer = self.llm_client.synthesize_final_response(
                messages=messages,
                tool_results=tool_results,
                rag_context=rag_context_str
            )

            # Determine aggregate data source
            if retrieval_used and tools_used:
                overall_source = "hybrid"
            elif "mock" in data_sources:
                overall_source = "mock"
            else:
                overall_source = "aws"

            # Append assistant message to conversation history
            messages.append({"role": "assistant", "content": final_answer})

            return {
                "answer": final_answer,
                "tools_used": tools_used,
                "data_source": overall_source,
                "sources": sources_list,
                "retrieval_used": retrieval_used,
                "session_id": sid,
                "tool_results": tool_results
            }

        except Exception as e:
            logger.error(f"Error in CloudSage agent execution: {e}", exc_info=True)
            err_msg = f"I encountered an error processing your request: {str(e)}"
            return {
                "answer": err_msg,
                "tools_used": [],
                "data_source": "error",
                "sources": [],
                "retrieval_used": False,
                "session_id": sid,
                "tool_results": []
            }
