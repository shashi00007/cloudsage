"""
LLM Provider Abstraction and Local Reasoning Engine for CloudSage.
Supports OpenAI, Gemini, RAG retrieval routing, and intelligent local deterministic tool-calling.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.config import get_settings
from app.ai.prompts import CLOUDSAGE_SYSTEM_PROMPT

logger = logging.getLogger("cloudsage.ai")


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: List[ToolCall] = []
    retrieval_query: Optional[str] = None
    is_knowledge_query: bool = False


class LLMClient:
    """
    Provider-agnostic LLM interface with seamless fallback.
    """

    def __init__(self):
        self.settings = get_settings()

    def generate_tool_calls_or_response(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        context_state: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Processes conversation history and tools to determine if operational tool calls,
        RAG knowledge retrieval, or direct conversational replies are required.
        """
        # Check for OpenAI key
        openai_key = self.settings.OPENAI_API_KEY or self.settings.LLM_API_KEY
        if openai_key and openai_key.startswith("sk-") and self.settings.LLM_PROVIDER == "openai":
            try:
                return self._call_openai(messages, tools, openai_key)
            except Exception as e:
                logger.warning(f"OpenAI API call failed, falling back to local reasoning engine: {e}")

        # Check for Gemini key
        gemini_key = self.settings.GEMINI_API_KEY or (self.settings.LLM_API_KEY if self.settings.LLM_PROVIDER == "gemini" else None)
        if gemini_key and (self.settings.LLM_PROVIDER == "gemini" or gemini_key.startswith("AIza")):
            try:
                return self._call_gemini(messages, tools, gemini_key)
            except Exception as e:
                logger.warning(f"Gemini API call failed, falling back to local reasoning engine: {e}")

        # Default / Local Reasoning Engine
        return self._local_reasoning_tool_selection(messages, tools, context_state)

    def synthesize_final_response(
        self,
        messages: List[Dict[str, str]],
        tool_results: List[Dict[str, Any]],
        rag_context: Optional[str] = None
    ) -> str:
        """
        Synthesizes the final natural language answer incorporating tool execution data and optional RAG context.
        """
        openai_key = self.settings.OPENAI_API_KEY or self.settings.LLM_API_KEY
        if openai_key and openai_key.startswith("sk-") and self.settings.LLM_PROVIDER == "openai":
            try:
                return self._call_openai_synthesis(messages, tool_results, openai_key, rag_context)
            except Exception as e:
                logger.warning(f"OpenAI synthesis failed, falling back to local synthesizer: {e}")

        gemini_key = self.settings.GEMINI_API_KEY or (self.settings.LLM_API_KEY if self.settings.LLM_PROVIDER == "gemini" else None)
        if gemini_key and (self.settings.LLM_PROVIDER == "gemini" or gemini_key.startswith("AIza")):
            try:
                return self._call_gemini_synthesis(messages, tool_results, gemini_key, rag_context)
            except Exception as e:
                logger.warning(f"Gemini synthesis failed, falling back to local synthesizer: {e}")

        return self._local_synthesis(messages, tool_results, rag_context)

    # ==========================================================================
    # Local Reasoning & Tool/RAG Selection Fallback
    # ==========================================================================

    def _local_reasoning_tool_selection(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        context_state: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Deterministic intent classifier for local development.
        Recognizes operational tools, RAG knowledge questions, and hybrid queries.
        """
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "").lower()
                break

        ctx = context_state or {}
        tool_calls: List[ToolCall] = []

        # 1. Multi-tool queries: infrastructure & cost summary / cloud health overview
        if any(w in last_user_msg for w in [
            "summary", "overview", "health", "all resources", "everything",
            "infrastructure and cost", "infrastructure & cost", "cloud infrastructure",
            "infrastructure summary", "health check"
        ]):
            tool_calls.append(ToolCall(id="call_ec2_1", name="inspect_ec2", arguments={}))
            tool_calls.append(ToolCall(id="call_s3_1", name="explore_s3", arguments={}))
            if any(w in last_user_msg for w in ["cost", "spend", "spending", "health", "summary", "overview", "infrastructure"]):
                tool_calls.append(ToolCall(id="call_cost_1", name="analyze_cloud_cost", arguments={"days": 30}))
            return LLMResponse(content=None, tool_calls=tool_calls)

        # 2. Combined EC2 + CloudWatch questions ("Which EC2 instances are running and what is their CPU utilization?")
        if ("ec2" in last_user_msg or "instance" in last_user_msg) and any(w in last_user_msg for w in ["cpu", "utilization", "metric", "telemetry"]) and any(w in last_user_msg for w in ["running", "and", "their", "all", "which"]):
            tool_calls.append(ToolCall(id="call_ec2_1", name="inspect_ec2", arguments={}))
            instance_id = ctx.get("last_instance_id") or "i-03fa78bc91204d8ef"
            tool_calls.append(ToolCall(id="call_cw_1", name="get_cloudwatch_metrics", arguments={"instance_id": instance_id, "hours": 1}))
            return LLMResponse(content=None, tool_calls=tool_calls)

        # 3. Hybrid Queries (e.g., "Analyze my AWS costs and explain how I could reduce them")
        if ("cost" in last_user_msg or "spending" in last_user_msg or "bill" in last_user_msg) and any(
            w in last_user_msg for w in ["reduce", "save", "cut", "optimize", "optimization", "explain", "how can", "ways"]
        ):
            tool_calls.append(ToolCall(id="call_cost_1", name="analyze_cloud_cost", arguments={"days": 30}))
            return LLMResponse(
                content=None,
                tool_calls=tool_calls,
                retrieval_query=last_user_msg,
                is_knowledge_query=True
            )

        # 4. Operational CloudWatch Metric queries ("What is the CPU utilization of instance i-...", "What is the CPU of that instance?")
        import re
        inst_match = re.search(r"i-[0-9a-fA-F]{8,17}", last_user_msg)
        if inst_match or (any(w in last_user_msg for w in ["cpu", "utilization", "telemetry"]) and (
            "instance" in last_user_msg or "that" in last_user_msg or "my" in last_user_msg or "current" in last_user_msg or ctx.get("last_instance_id")
        ) and not any(w in last_user_msg for w in ["cause", "causes", "why is cpu", "troubleshoot cpu", "what are common causes"])):
            instance_id = inst_match.group(0) if inst_match else (ctx.get("last_instance_id") or "i-03fa78bc91204d8ef")
            hours = 24 if ("24" in last_user_msg or "day" in last_user_msg) else (6 if "6" in last_user_msg else 1)
            tool_calls.append(ToolCall(id="call_cw_1", name="get_cloudwatch_metrics", arguments={"instance_id": instance_id, "hours": hours}))
            return LLMResponse(content=None, tool_calls=tool_calls)

        # 5. Operational EC2 queries ("What EC2 instances are running?", "What EC2 instances do I have?")
        if any(w in last_user_msg for w in ["instances are running", "instances do i have", "my ec2", "running ec2", "running instance", "what ec2 instances", "show me ec2", "list ec2", "list instances"]):
            tool_calls.append(ToolCall(id="call_ec2_1", name="inspect_ec2", arguments={}))
            return LLMResponse(content=None, tool_calls=tool_calls)

        # 6. Operational S3 queries ("Show me my S3 buckets", "What S3 buckets do I have?")
        if any(w in last_user_msg for w in ["my s3", "my buckets", "show me my s3", "show me s3", "list s3", "list buckets", "what s3 buckets"]):
            tool_calls.append(ToolCall(id="call_s3_1", name="explore_s3", arguments={}))
            return LLMResponse(content=None, tool_calls=tool_calls)

        # 7. Operational Cost queries ("How much am I spending?", "Which AWS service is costing me the most?")
        if any(w in last_user_msg for w in ["how much am i spending", "how much am i spend", "spending", "my cost", "costing me the most", "analyze cloud cost", "cost summary"]):
            days = 7 if ("7" in last_user_msg or "week" in last_user_msg) else (90 if ("90" in last_user_msg or "quarter" in last_user_msg) else 30)
            tool_calls.append(ToolCall(id="call_cost_1", name="analyze_cloud_cost", arguments={"days": days}))
            return LLMResponse(content=None, tool_calls=tool_calls)

        # 8. Pure Knowledge / Conceptual Questions (RAG Knowledge Base)
        knowledge_phrases = [
            "what is", "what are", "how does", "how do", "explain", "difference between",
            "compare", "why does", "concept", "causes of", "cause of", "least privilege",
            "security group", "storage class", "storage classes", "glacier", "intelligent-tiering",
            "lifecycle policy", "availability zone", "well-architected", "how can i reduce",
            "how to reduce", "ways to reduce", "reduce costs", "cost optimization", "monitoring work"
        ]
        if any(kp in last_user_msg for kp in knowledge_phrases) or any(topic in last_user_msg for topic in ["security group", "least privilege", "storage class", "glacier", "availability zone"]):
            return LLMResponse(
                content=None,
                tool_calls=[],
                retrieval_query=last_user_msg,
                is_knowledge_query=True
            )

        # Fallback operational routing
        if any(w in last_user_msg for w in ["ec2", "instance", "server", "vm"]):
            tool_calls.append(ToolCall(id="call_ec2_1", name="inspect_ec2", arguments={}))
            return LLMResponse(content=None, tool_calls=tool_calls)

        if any(w in last_user_msg for w in ["s3", "bucket"]):
            tool_calls.append(ToolCall(id="call_s3_1", name="explore_s3", arguments={}))
            return LLMResponse(content=None, tool_calls=tool_calls)

        if any(w in last_user_msg for w in ["cost", "spend", "bill", "billing"]):
            tool_calls.append(ToolCall(id="call_cost_1", name="analyze_cloud_cost", arguments={"days": 30}))
            return LLMResponse(content=None, tool_calls=tool_calls)

        # ----------------------------------------------------------------------
        # I. General conversational greeting or system capability question
        # ----------------------------------------------------------------------
        return LLMResponse(
            content=(
                "Hello! I am **CloudSage**, your GenAI Cloud Operations & Knowledge Assistant. "
                "I can inspect live AWS infrastructure, analyze telemetry and costs, and answer cloud architecture and security questions grounded in official AWS documentation.\n\n"
                "**Try asking me:**\n"
                "- *What is an EC2 security group?*\n"
                "- *Explain AWS IAM least privilege.*\n"
                "- *What is the difference between S3 Standard and S3 Glacier?*\n"
                "- *What EC2 instances are currently running?*\n"
                "- *Analyze my AWS costs and explain how I could reduce them.*"
            ),
            tool_calls=[]
        )

    def _local_synthesis(
        self,
        messages: List[Dict[str, str]],
        tool_results: List[Dict[str, Any]],
        rag_context: Optional[str] = None
    ) -> str:
        """
        Synthesizes clear natural language response with mock/real attribution and optional RAG knowledge context.
        """
        if not tool_results and not rag_context:
            return "I was unable to retrieve data to answer your question."

        is_mock = any(tr.get("data_source") == "mock" for tr in tool_results)
        disclaimer = "\n\n> ℹ️ *Development mock data is being used because AWS is not connected.*" if is_mock else ""

        sections: List[str] = []

        for tr in tool_results:
            tool_name = tr.get("tool_name")
            data = tr.get("data", {})
            success = tr.get("success", True)

            if not success or data.get("error"):
                sections.append(f"⚠️ **Error with {tool_name}**: {data.get('error') or tr.get('error')}")
                continue

            if tool_name == "inspect_ec2":
                instances = data.get("instances", [])
                count = data.get("count", len(instances))
                region = data.get("region", "us-east-1")
                
                running = [i for i in instances if i.get("state") == "running"]
                stopped = [i for i in instances if i.get("state") == "stopped"]

                inst_lines = []
                for i in instances:
                    name_str = f" (`{i.get('name')}`)" if i.get("name") else ""
                    public_ip = f", Public IP: `{i.get('public_ip')}`" if i.get("public_ip") else ""
                    inst_lines.append(
                        f"- **{i.get('instance_id')}**{name_str}: {i.get('state').upper()} • Type: `{i.get('instance_type')}` • AZ: `{i.get('availability_zone')}`{public_ip}"
                    )

                ec2_sec = (
                    f"### 🖥️ EC2 Instances Overview ({region})\n"
                    f"Found **{count} instance(s)** ({len(running)} running, {len(stopped)} stopped):\n"
                    + "\n".join(inst_lines)
                )
                sections.append(ec2_sec)

            elif tool_name == "explore_s3":
                buckets = data.get("buckets", [])
                count = data.get("count", len(buckets))

                b_lines = [f"- **`{b.get('name')}`** (Created: {b.get('creation_date')[:10] if b.get('creation_date') else 'N/A'})" for b in buckets]
                s3_sec = f"### 🪣 S3 Storage Buckets\nFound **{count} bucket(s)** in your account:\n" + "\n".join(b_lines)
                sections.append(s3_sec)

            elif tool_name == "get_cloudwatch_metrics":
                instance_id = data.get("instance_id", "Unknown")
                avg_cpu = data.get("average_cpu")
                max_cpu = data.get("max_cpu")
                min_cpu = data.get("min_cpu")
                points = data.get("datapoints", [])

                cw_sec = (
                    f"### 📊 CloudWatch CPU Telemetry (`{instance_id}`)\n"
                    f"- **Average CPU Utilization:** `{avg_cpu}%`\n"
                    f"- **Peak Utilization:** `{max_cpu}%` (Min: `{min_cpu}%`)\n"
                    f"- **Telemetry Window:** Last {len(points)} recorded datapoints."
                )
                sections.append(cw_sec)

            elif tool_name == "analyze_cloud_cost":
                from app.services import currency as curr_service
                
                orig_currency = data.get("currency", "USD")
                total_val = float(data.get("total_cost", 0.0))
                start = data.get("start_date")
                end = data.get("end_date")
                top_svc = data.get("top_service", "N/A")
                services = data.get("services", [])

                if orig_currency == "USD":
                    conv_data = curr_service.convert_cost_summary(data)
                    total_formatted = conv_data["total_cost_formatted"]
                    svc_lines = [
                        f"- **{s.get('service')}**: `{s.get('cost_formatted')}` ({s.get('percentage')}%)"
                        for s in conv_data.get("services", [])
                    ]
                    rate_note = f" *(Converted at ₹{conv_data['exchange_rate']:.2f}/USD)*"
                else:
                    total_formatted = curr_service.format_inr(total_val)
                    svc_lines = [
                        f"- **{s.get('service')}**: `{curr_service.format_inr(s.get('cost', 0.0))}` ({s.get('percentage')}%)"
                        for s in services
                    ]
                    rate_note = ""

                cost_sec = (
                    f"### 💰 AWS Cost & Spending Breakdown\n"
                    f"**Total Estimated Spend:** `{total_formatted}` (Period: `{start}` to `{end}`){rate_note}\n"
                    f"**Highest Cost Driver:** **{top_svc}**\n\n"
                    f"**Top Service Breakdown:**\n"
                    + "\n".join(svc_lines)
                )
                sections.append(cost_sec)

        # Incorporate Grounded RAG Documentation Knowledge
        if rag_context:
            sections.append(f"### 📚 AWS Knowledge & Optimization Insights\n{rag_context}")
        elif any(tr.get("tool_name") == "analyze_cloud_cost" for tr in tool_results):
            sections.append(
                "💡 **FinOps Recommendation**: Consider rightsizing compute resources and reviewing storage lifecycle policies on high-spend services."
            )

        return "\n\n".join(sections) + disclaimer

    # ==========================================================================
    # OpenAI Provider Implementation
    # ==========================================================================

    def _call_openai(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], api_key: str) -> LLMResponse:
        import httpx
        system_msg = {"role": "system", "content": CLOUDSAGE_SYSTEM_PROMPT}
        full_messages = [system_msg] + [m for m in messages if m.get("role") != "system"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.settings.LLM_MODEL or "gpt-4o-mini",
            "messages": full_messages,
            "tools": tools,
            "tool_choice": "auto"
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]
        tool_calls_raw = choice.get("tool_calls", [])

        tool_calls: List[ToolCall] = []
        for tc in tool_calls_raw:
            func = tc.get("function", {})
            try:
                args = json.loads(func.get("arguments", "{}"))
            except Exception:
                args = {}
            tool_calls.append(ToolCall(id=tc.get("id", "call_1"), name=func.get("name", ""), arguments=args))

        return LLMResponse(content=choice.get("content"), tool_calls=tool_calls)

    def _call_openai_synthesis(
        self,
        messages: List[Dict[str, str]],
        tool_results: List[Dict[str, Any]],
        api_key: str,
        rag_context: Optional[str] = None
    ) -> str:
        import httpx
        system_msg = {"role": "system", "content": CLOUDSAGE_SYSTEM_PROMPT}
        
        tool_content = json.dumps(tool_results, indent=2)
        rag_block = f"\n\nRetrieved AWS Documentation Context:\n{rag_context}" if rag_context else ""
        synthesis_prompt = (
            f"Here are the tool execution results from AWS tools:\n```json\n{tool_content}\n```{rag_block}\n\n"
            "Please provide a comprehensive, friendly, and structured answer to the user based on these results."
        )

        full_messages = [system_msg] + [m for m in messages if m.get("role") != "system"] + [
            {"role": "user", "content": synthesis_prompt}
        ]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.settings.LLM_MODEL or "gpt-4o-mini",
            "messages": full_messages
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]

    def _call_direct_generation(self, system_prompt: str, user_prompt: str) -> str:
        """
        Executes direct grounded generation with a given prompt.
        """
        import httpx
        openai_key = self.settings.OPENAI_API_KEY or self.settings.LLM_API_KEY
        if openai_key and openai_key.startswith("sk-") and self.settings.LLM_PROVIDER == "openai":
            headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.settings.LLM_MODEL or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            with httpx.Client(timeout=30.0) as client:
                resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

        gemini_key = self.settings.GEMINI_API_KEY or (self.settings.LLM_API_KEY if self.settings.LLM_PROVIDER == "gemini" else None)
        if gemini_key and (self.settings.LLM_PROVIDER == "gemini" or gemini_key.startswith("AIza")):
            model = self.settings.LLM_MODEL if "gemini" in self.settings.LLM_MODEL.lower() else "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}]
            }
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
            candidate = data.get("candidates", [{}])[0].get("content", {})
            parts = candidate.get("parts", [])
            return "".join([p.get("text", "") for p in parts if "text" in p])

        raise RuntimeError("No external LLM provider available for direct generation.")

    # ==========================================================================
    # Google Gemini Provider Implementation
    # ==========================================================================

    def _call_gemini(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], api_key: str) -> LLMResponse:
        import httpx
        
        gemini_functions = []
        for t in tools:
            func = t.get("function", {})
            gemini_functions.append({
                "name": func.get("name"),
                "description": func.get("description"),
                "parameters": func.get("parameters", {"type": "object", "properties": {}})
            })

        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.get("content", "")}]
            })

        payload = {
            "systemInstruction": {
                "parts": [{"text": CLOUDSAGE_SYSTEM_PROMPT}]
            },
            "contents": contents,
            "tools": [{"functionDeclarations": gemini_functions}]
        }

        model = self.settings.LLM_MODEL if "gemini" in self.settings.LLM_MODEL.lower() else "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidate = data.get("candidates", [{}])[0].get("content", {})
        parts = candidate.get("parts", [])

        tool_calls: List[ToolCall] = []
        text_content: Optional[str] = None

        for part in parts:
            if "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(ToolCall(
                    id=f"call_{fc.get('name')}",
                    name=fc.get("name", ""),
                    arguments=fc.get("args", {})
                ))
            elif "text" in part:
                text_content = part["text"]

        return LLMResponse(content=text_content, tool_calls=tool_calls)

    def _call_gemini_synthesis(
        self,
        messages: List[Dict[str, str]],
        tool_results: List[Dict[str, Any]],
        api_key: str,
        rag_context: Optional[str] = None
    ) -> str:
        import httpx
        tool_content = json.dumps(tool_results, indent=2)
        rag_block = f"\n\nRetrieved AWS Documentation Context:\n{rag_context}" if rag_context else ""
        prompt = (
            f"Here are the tool execution results from AWS tools:\n```json\n{tool_content}\n```{rag_block}\n\n"
            "Please provide a comprehensive, friendly, and structured answer to the user based on these results."
        )

        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "systemInstruction": {"parts": [{"text": CLOUDSAGE_SYSTEM_PROMPT}]},
            "contents": contents
        }

        model = self.settings.LLM_MODEL if "gemini" in self.settings.LLM_MODEL.lower() else "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidate = data.get("candidates", [{}])[0].get("content", {})
        parts = candidate.get("parts", [])
        return "".join([p.get("text", "") for p in parts if "text" in p])


_llm_client_singleton: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Singleton accessor for LLMClient."""
    global _llm_client_singleton
    if _llm_client_singleton is None:
        _llm_client_singleton = LLMClient()
    return _llm_client_singleton
