import json
import pytest
from unittest.mock import patch, MagicMock
from app.services.epidemic_service import EpidemicService


def test_epidemic_service_auth_and_headers():
    service = EpidemicService(api_key="epi_key_123", partner_user_id="test_partner")
    headers = service._get_headers()
    assert headers["Authorization"] == "Bearer epi_key_123"
    assert headers["x-partner-user-id"] == "test_partner"


def test_epidemic_prototype_vs_production_tier():
    proto_service = EpidemicService(api_key="epi_key", tier="PROTOTYPE")
    assert proto_service.is_prototype is True

    prod_service = EpidemicService(api_key="epi_key", tier="PRODUCTION")
    assert prod_service.is_prototype is False


def test_epidemic_create_version_job():
    service = EpidemicService(api_key="epi_key")
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "status": "PENDING",
            "jobId": "test_job_123"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        job_id = service.create_version_job(track_id="4c20406f-6937-49f7-8dcb-39647af926a4", duration_seconds=7.0)
        assert job_id == "test_job_123"


def test_epidemic_poll_version_job_completed():
    service = EpidemicService(api_key="epi_key")
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "status": "COMPLETED",
            "results": [
                {"previewUrl": "https://audiocdn.epidemicsound.com/track_7s.mp3"}
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        url = service.poll_version_job("test_job_123", max_timeout_sec=2)
        assert url == "https://audiocdn.epidemicsound.com/track_7s.mp3"
