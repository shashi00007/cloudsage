import httpx
import json

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=15.0)

test_questions = [
    "What EC2 instances are running?",
    "Show me my S3 buckets.",
    "How much am I spending?",
    "Give me a summary of my cloud infrastructure and costs.",
    "Which service costs the most?",
    "What is the CPU utilization of my EC2 instance?"
]

print("=== Testing Phase 3 GenAI Chat API ===\n")

for q in test_questions:
    print(f"User Query: \"{q}\"")
    r = client.post("/api/chat", json={"message": q})
    assert r.status_code == 200, f"Failed on {q}: {r.status_code}"
    data = r.json()
    print(f"Tools Used: {data['tools_used']}")
    print(f"Data Source: {data['data_source']}")
    print(f"Answer:\n{data['answer']}")
    print("-" * 60 + "\n")

print(">>> ALL LIVE CHAT QUERIES COMPLETED & VERIFIED!")
