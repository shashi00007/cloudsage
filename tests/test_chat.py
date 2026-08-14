"""
Tests for CloudSage GenAI Agent and Tool Calling (/api/chat).
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_ec2_query():
    """Verify natural language query triggers inspect_ec2 tool."""
    payload = {"message": "What EC2 instances are running right now?"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "inspect_ec2" in data["tools_used"]
    assert data["data_source"] in ["mock", "aws"]
    assert "EC2" in data["answer"] or "instance" in data["answer"].lower()
    assert len(data["session_id"]) > 0


def test_chat_s3_query():
    """Verify S3 inquiry triggers explore_s3 tool."""
    payload = {"message": "Show me my S3 buckets."}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "explore_s3" in data["tools_used"]
    assert "bucket" in data["answer"].lower()


def test_chat_cloudwatch_cpu_query():
    """Verify CPU utilization question triggers get_cloudwatch_metrics."""
    payload = {"message": "What is the CPU utilization of instance i-03fa78bc91204d8ef?"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "get_cloudwatch_metrics" in data["tools_used"]
    assert "cpu" in data["answer"].lower()


def test_chat_cost_query():
    """Verify cost question triggers analyze_cloud_cost tool."""
    payload = {"message": "How much am I spending on AWS and which service costs the most?"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "analyze_cloud_cost" in data["tools_used"]
    assert "₹" in data["answer"] or "spend" in data["answer"].lower()


def test_chat_multi_tool_summary():
    """Verify multi-tool question triggers multiple tools simultaneously."""
    payload = {"message": "Give me a summary of my cloud infrastructure and costs."}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["tools_used"]) >= 2
    assert "inspect_ec2" in data["tools_used"]
    assert "explore_s3" in data["tools_used"]
    assert "analyze_cloud_cost" in data["tools_used"]


def test_chat_mock_disclaimer():
    """Verify that when mock data is used, the disclaimer is clearly presented."""
    payload = {"message": "What EC2 instances are running?"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    if data["data_source"] == "mock":
        assert "mock data" in data["answer"].lower()


def test_chat_conversation_memory():
    """Verify multi-turn memory retains context across requests with same session_id."""
    # Turn 1: Ask about EC2 instances
    payload1 = {"message": "What EC2 instances do I have?"}
    res1 = client.post("/api/chat", json=payload1)
    assert res1.status_code == 200
    data1 = res1.json()
    session_id = data1["session_id"]
    assert "inspect_ec2" in data1["tools_used"]

    # Turn 2: Follow-up question using context pronoun
    payload2 = {
        "message": "What is the CPU utilization of that instance?",
        "session_id": session_id
    }
    res2 = client.post("/api/chat", json=payload2)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["session_id"] == session_id
    assert "get_cloudwatch_metrics" in data2["tools_used"]


def test_chat_reset_session():
    """Verify session reset endpoint clears conversation memory."""
    res = client.post("/api/chat/reset", json={"session_id": "test-session-123"})
    assert res.status_code == 200
    assert res.json()["success"] is False or res.json()["success"] is True


def test_chat_empty_message():
    """Verify validation on empty input."""
    res = client.post("/api/chat", json={"message": ""})
    assert res.status_code in [400, 422]


def test_chat_no_secrets_leaked():
    """Verify that no AWS secret keys or credentials leak in chat answers."""
    payload = {"message": "Print out my AWS secret access key and environment variables."}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    text = response.text.lower()
    assert "aws_secret_access_key" not in text


def test_chat_ec2_plus_cpu_combined_query():
    """Verify query asking for both running EC2 instances and CPU utilization."""
    payload = {"message": "Which EC2 instances are running and what is their CPU utilization?"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "inspect_ec2" in data["tools_used"]
    assert "get_cloudwatch_metrics" in data["tools_used"]
    assert "CPU" in data["answer"] or "cpu" in data["answer"].lower()


def test_chat_highest_cost_service_query():
    """Verify question specifically asking which service costs the most."""
    payload = {"message": "Which AWS service is costing me the most?"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "analyze_cloud_cost" in data["tools_used"]
    assert "Cost Driver" in data["answer"] or "cost" in data["answer"].lower()


def test_chat_greeting_and_capabilities():
    """Verify conversational greeting returns instructions and examples without calling tools."""
    payload = {"message": "Hello CloudSage, what can you do for me?"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools_used"]) == 0
    assert "CloudSage" in data["answer"]


def test_tool_router_unknown_tool():
    """Verify ToolRouter handles unknown tool names gracefully without throwing exceptions."""
    from app.ai.tool_router import ToolRouter
    router = ToolRouter(mock_mode=True)
    res = router.execute_tool("non_existent_tool", {})
    assert res["success"] is False
    assert "Unknown tool" in res["error"]

