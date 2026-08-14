"""
End-to-end verification script for CloudSage Final UI Polish & INR Localization.
"""

import sys
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def test_verification():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        print("1. Testing GET /health...")
        r = client.get("/health")
        assert r.status_code == 200, f"Health failed: {r.status_code}"
        print(f"   [OK] Health response: {r.json()}")

        print("2. Testing GET / (Frontend HTML)...")
        r = client.get("/")
        assert r.status_code == 200, f"Frontend HTML failed: {r.status_code}"
        assert "CloudSage" in r.text
        assert "GenAI Cloud Operations & Knowledge Assistant" in r.text
        assert "₹" in r.text
        print("   [OK] Frontend HTML served with updated branding and INR markers.")

        print("3. Testing GET /css/style.css...")
        r = client.get("/css/style.css")
        assert r.status_code == 200, f"CSS failed: {r.status_code}"
        assert "--bg-page: #f8fafc;" in r.text
        assert "--surface: #ffffff;" in r.text
        print("   [OK] CSS served with clean light SaaS design tokens.")

        print("4. Testing GET /js/app.js...")
        r = client.get("/js/app.js")
        assert r.status_code == 200, f"JS failed: {r.status_code}"
        assert "formatInrCurrency" in r.text
        print("   [OK] JavaScript controller served with INR currency formatter.")

        print("5. Testing GET /api/aws/status...")
        r = client.get("/api/aws/status")
        assert r.status_code == 200
        print(f"   [OK] AWS Status: {r.json()}")

        print("6. Testing GET /api/aws/cost/summary...")
        r = client.get("/api/aws/cost/summary?days=30")
        assert r.status_code == 200
        data = r.json()
        print(f"   [OK] Cost Summary Endpoint returned: success={data.get('success')}, error={data.get('error')}")

        print("7. Testing POST /api/chat (Cost Query)...")
        r = client.post("/api/chat", json={"message": "How much am I spending on AWS and which service costs the most?"})
        assert r.status_code == 200
        chat_data = r.json()
        answer = chat_data["answer"]
        print("   --- AI Cost Query Answer ---")
        print(answer)
        print("   ----------------------------")
        assert "₹" in answer, "Missing INR symbol ₹ in answer"
        assert "40,995.50" in answer or "20,833.50" in answer, "Missing expected INR converted amounts"
        assert "$482.30" not in answer, "Found unexpected $482.30 in answer"
        assert "$245.10" not in answer, "Found unexpected $245.10 in answer"
        print("   [OK] Chat cost response formatted in INR (₹) without stray USD symbols.")

        print("8. Testing POST /api/chat (RAG Query)...")
        r = client.post("/api/chat", json={"message": "What is an EC2 security group?"})
        assert r.status_code == 200
        rag_data = r.json()
        assert rag_data["retrieval_used"] is True or rag_data["data_source"] == "knowledge_base"
        assert len(rag_data["sources"]) > 0
        print(f"   [OK] RAG Query successful with {len(rag_data['sources'])} source citations.")

        print("9. Testing POST /api/chat (Hybrid Query)...")
        r = client.post("/api/chat", json={"message": "Analyze my AWS costs and explain how I could reduce them."})
        assert r.status_code == 200
        hybrid_data = r.json()
        assert "₹" in hybrid_data["answer"]
        assert len(hybrid_data["sources"]) > 0 or hybrid_data["retrieval_used"] is True
        print("   [OK] Hybrid Query successful with INR spend and grounded FinOps guidance.")

        print("10. Testing POST /api/chat/reset...")
        r = client.post("/api/chat/reset", json={"session_id": hybrid_data["session_id"]})
        assert r.status_code == 200
        print("   [OK] Chat memory reset endpoint verified.")

    print("\nALL E2E VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_verification()
