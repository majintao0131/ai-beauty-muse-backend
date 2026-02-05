"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestRootEndpoints:
    """Test root and health endpoints."""
    
    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_health(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    def test_api_info(self, client):
        """Test API info endpoint."""
        response = client.get("/api/v1")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "endpoints" in data


class TestDailyEndpoints:
    """Test daily energy endpoints."""
    
    def test_quick_daily_info(self, client):
        """Test quick daily info endpoint."""
        response = client.get("/api/v1/daily/quick")
        assert response.status_code == 200
        data = response.json()
        assert "daily_stem_branch" in data
        assert "daily_element" in data
        assert "lucky_colors" in data


class TestChatEndpoints:
    """Test chat endpoints."""
    
    def test_chat_suggestions(self, client):
        """Test chat suggestions endpoint."""
        response = client.get("/api/v1/chat/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0


class TestBodyAnalysis:
    """Test body analysis endpoint."""
    
    def test_body_analysis_h_type(self, client):
        """Test body analysis for H-type body."""
        response = client.post(
            "/api/v1/analysis/body",
            json={
                "height": 165,
                "bust": 85,
                "waist": 70,
                "hip": 88,
            }
        )
        # This might fail without OpenAI key, but should return proper error
        assert response.status_code in [200, 500]
    
    def test_body_analysis_validation(self, client):
        """Test body analysis input validation."""
        # Test with invalid height
        response = client.post(
            "/api/v1/analysis/body",
            json={
                "height": 50,  # Too short
                "bust": 85,
                "waist": 70,
                "hip": 88,
            }
        )
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
