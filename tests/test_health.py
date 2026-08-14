"""
Tests for CloudSage Health Check & Core Endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings

client = TestClient(app)


def test_health_endpoint_direct():
    """Verify that /health returns HTTP 200 with healthy status."""
    settings = get_settings()
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "CloudSage"
    assert data["version"] == settings.APP_VERSION
    assert "timestamp" in data
    assert "environment" in data


def test_health_endpoint_api_prefix():
    """Verify that /api/health returns HTTP 200 with identical schema."""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "CloudSage"


def test_frontend_static_serving():
    """Verify that root / serves the frontend HTML dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "CloudSage" in response.text
    assert "<!DOCTYPE html>" in response.text or "<html" in response.text


def test_settings_singleton():
    """Verify settings configuration loading."""
    settings = get_settings()
    assert settings.APP_NAME == "CloudSage"
    assert settings.APP_VERSION is not None
    assert settings.AWS_DEFAULT_REGION == "us-east-1"
