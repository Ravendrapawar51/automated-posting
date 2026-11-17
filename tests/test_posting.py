import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app, posting_service
from app.config import settings
from app.schemas import extract_and_validate_cta_url, PlatformResult


client = TestClient(app)


class TestInputValidation:
    """Tests for input validation rules on message and CTA URL."""

    def test_valid_message_single_url(self):
        msg = "Check out our latest business platform and grow your online visibility. https://example.com"
        url = extract_and_validate_cta_url(msg)
        assert url == "https://example.com"

    def test_valid_message_with_query_params(self):
        msg = "Join our community today! https://platform.io/signup?ref=abc_123&source=web"
        url = extract_and_validate_cta_url(msg)
        assert url == "https://platform.io/signup?ref=abc_123&source=web"

    def test_trailing_punctuation_stripped(self):
        msg = "Visit our site at https://example.com/growth."
        url = extract_and_validate_cta_url(msg)
        assert url == "https://example.com/growth"

    def test_exceeding_200_characters(self):
        long_message = "A" * 180 + " https://example.com"  # 180 + 20 = 200 (exact)
        assert len(long_message) == 200
        assert extract_and_validate_cta_url(long_message) == "https://example.com"

        over_message = "A" * 181 + " https://example.com"  # 201 characters
        with pytest.raises(ValueError, match="must not exceed 200 characters"):
            extract_and_validate_cta_url(over_message)

    def test_missing_cta_link(self):
        msg = "Check out our latest business platform and grow your visibility with no link."
        with pytest.raises(ValueError, match="Message must contain exactly one CTA link, but none was found"):
            extract_and_validate_cta_url(msg)

    def test_multiple_cta_links(self):
        msg = "Visit https://example.com and check https://second.org for more!"
        with pytest.raises(ValueError, match="Message must contain exactly one CTA link, but 2 were found"):
            extract_and_validate_cta_url(msg)

    def test_unsupported_scheme(self):
        msg = "Download via ftp: ftp://files.example.com/update.zip"
        # ftp scheme is detected as URL but rejected during validation
        with pytest.raises(ValueError, match="uses unsupported scheme 'ftp'"):
            extract_and_validate_cta_url(msg)

    def test_missing_scheme_www(self):
        msg = "Visit www.example.com to register."
        with pytest.raises(ValueError, match="missing an HTTP/HTTPS protocol scheme"):
            extract_and_validate_cta_url(msg)

    def test_empty_message(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            extract_and_validate_cta_url("   ")


class TestAPIEndpoints:
    """Tests for FastAPI endpoints."""

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Automated Multi-Platform Posting System"
        assert "supported_platforms" in data
        assert len(data["supported_platforms"]) >= 5

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_api_validation_error_over_200_chars(self):
        payload = {"message": "X" * 190 + " https://example.com"}  # > 200 chars
        response = client.post("/posting", json=payload)
        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert "must not exceed 200 characters" in str(body)

    def test_api_validation_error_no_cta_link(self):
        payload = {"message": "Here is an announcement without any link at all."}
        response = client.post("/posting", json=payload)
        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert "must contain exactly one CTA link" in str(body)

    def test_api_validation_error_multiple_cta_links(self):
        payload = {"message": "See https://first.com and https://second.com"}
        response = client.post("/posting", json=payload)
        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert "exactly one CTA link" in str(body)

    def test_posting_in_mock_mode(self):
        # Enable mock mode temporarily
        original_mock = settings.MOCK_MODE
        for p in posting_service.platforms:
            p.mock_mode = True

        try:
            payload = {
                "message": "Check out our latest business platform and grow your online visibility. https://example.com"
            }
            response = client.post("/posting", json=payload)
            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert len(data["results"]) >= 5

            for res in data["results"]:
                assert "platform" in res
                assert res["status"] == "success"
                assert res["posted_url"] is not None
                assert res["posted_url"].startswith("http")
                assert res["date"] is not None
                assert res["time"] is not None
                assert res["error"] is None
        finally:
            for p in posting_service.platforms:
                p.mock_mode = original_mock

    def test_unconfigured_platforms_fail_gracefully(self):
        """When credentials are not supplied, unconfigured platforms should report 'failed' without crashing."""
        for p in posting_service.platforms:
            p.mock_mode = False

        payload = {
            "message": "Check out our latest business platform. https://example.com"
        }
        response = client.post("/posting", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert len(data["results"]) >= 5

        # All unconfigured platforms should report failed with error details
        for res in data["results"]:
            assert res["status"] == "failed"
            assert res["posted_url"] is None
            assert res["error"] is not None
            assert "Missing" in res["error"] or "Authentication" in res["error"]

    def test_fault_isolation_partial_failure(self):
        """Verify that a failure in one platform does not prevent other platforms from succeeding."""
        # Force platform 0 to succeed and platform 1 to fail
        p0 = posting_service.platforms[0]
        p1 = posting_service.platforms[1]

        async def mock_success(message, cta_url, client):
            return "https://example.com/success-post/123", True

        async def mock_fail(message, cta_url, client):
            raise Exception("Simulated network timeout")

        with patch.object(p0, "_publish", side_effect=mock_success), \
             patch.object(p0, "is_configured", return_value=True), \
             patch.object(p1, "_publish", side_effect=mock_fail), \
             patch.object(p1, "is_configured", return_value=True):

            p0.mock_mode = False
            p1.mock_mode = False

            payload = {
                "message": "Check out our multi-platform service: https://example.com"
            }
            response = client.post("/posting", json=payload)
            assert response.status_code == 200
            data = response.json()

            results = {r["platform"]: r for r in data["results"]}
            # Platform 0 must succeed
            assert results[p0.name]["status"] == "success"
            assert results[p0.name]["posted_url"] == "https://example.com/success-post/123"
            assert results[p0.name]["error"] is None

            # Platform 1 must fail gracefully
            assert results[p1.name]["status"] == "failed"
            assert results[p1.name]["posted_url"] is None
            assert "Simulated network timeout" in results[p1.name]["error"]

            # Overall success is True because at least one succeeded
            assert data["success"] is True
