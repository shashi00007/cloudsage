"""
Unit Tests for CloudSage Currency Localization and Conversion Service.
Tests USD -> INR conversions, Indian numbering formatting, configuration overrides,
and ensures no accidental '$' occurs in user-facing cost responses.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.services.currency import (
    convert_usd_to_inr,
    format_inr,
    convert_and_format_cost,
    convert_cost_summary,
    get_configured_exchange_rate,
    get_currency_symbol,
    get_default_currency,
)
from app.ai.mock_data import get_mock_cost_summary

client = TestClient(app)


def test_currency_constants_and_defaults():
    """Verify default currency symbol and exchange rate configuration."""
    assert get_currency_symbol() == "₹"
    assert get_default_currency() == "INR"
    assert get_configured_exchange_rate() == 85.0


def test_usd_to_inr_conversion():
    """Verify USD to INR numeric conversions."""
    # Test with default rate 85.0
    assert convert_usd_to_inr(1.0) == 85.0
    assert convert_usd_to_inr(482.30) == 40995.50
    assert convert_usd_to_inr(245.10) == 20833.50
    assert convert_usd_to_inr(142.50) == 12112.50
    assert convert_usd_to_inr(54.20) == 4607.00
    assert convert_usd_to_inr(40.50) == 3442.50

    # Test with explicit rate override
    assert convert_usd_to_inr(100.0, rate=80.0) == 8000.0
    assert convert_usd_to_inr(10.55, rate=83.25) == 878.29


def test_inr_formatting_indian_numbering():
    """Verify Indian numbering format (comma grouping)."""
    assert format_inr(500.00) == "₹500.00"
    assert format_inr(40995.50) == "₹40,995.50"
    assert format_inr(20833.50) == "₹20,833.50"
    assert format_inr(142500.00) == "₹1,42,500.00"
    assert format_inr(10000000.00) == "₹1,00,00,000.00"
    assert format_inr(40995.50, symbol=False) == "40,995.50"


def test_convert_and_format_cost():
    """Verify end-to-end USD conversion and formatted string output."""
    assert convert_and_format_cost(482.30) == "₹40,995.50"
    assert convert_and_format_cost(245.10) == "₹20,833.50"


def test_convert_cost_summary_structure_and_percentages():
    """Verify convert_cost_summary transforms mock data while preserving percentages."""
    mock_data = get_mock_cost_summary(days=30)
    converted = convert_cost_summary(mock_data, rate=85.0)

    assert converted["success"] is True
    assert converted["currency"] == "INR"
    assert converted["currency_symbol"] == "₹"
    assert converted["total_cost"] == 40995.50
    assert converted["total_cost_formatted"] == "₹40,995.50"
    assert len(converted["services"]) == 4

    # Verify each service conversion and percentage retention
    ec2_svc = converted["services"][0]
    assert ec2_svc["service"] == "Amazon Elastic Compute Cloud - Compute"
    assert ec2_svc["cost"] == 20833.50
    assert ec2_svc["cost_formatted"] == "₹20,833.50"
    assert ec2_svc["percentage"] == 50.8

    rds_svc = converted["services"][1]
    assert rds_svc["cost"] == 12112.50
    assert rds_svc["percentage"] == 29.5


def test_chat_cost_query_returns_inr_and_no_stray_dollars():
    """Verify chat cost response displays '₹' and does not use '$' for main spend numbers."""
    payload = {"message": "How much am I spending on AWS and which service costs the most?"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    answer = data["answer"]

    # Must contain INR symbol and proper converted value
    assert "₹" in answer
    assert "40,995.50" in answer or "20,833.50" in answer
    # Must NOT have $ in main cost lines
    assert "$482.30" not in answer
    assert "$245.10" not in answer


def test_chat_hybrid_cost_optimization_inr():
    """Verify hybrid query response formats spend in INR."""
    payload = {"message": "Analyze my AWS costs and explain how I could reduce them."}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    answer = data["answer"]
    assert "₹" in answer
    assert "$482.30" not in answer
