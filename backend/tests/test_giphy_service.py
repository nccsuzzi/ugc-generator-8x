import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.services.giphy_service import GiphyService


def test_giphy_service_availability():
    service = GiphyService(api_key="test_key")
    assert service.is_available is True
    no_key = GiphyService(api_key=None)
    assert no_key.is_available is False


def test_giphy_catalog_filter_rejects_foreign_domains():
    service = GiphyService(api_key="test_key")
    # Mock response containing a foreign domain
    mock_response = {
        "data": [
            {
                "id": "legit_1",
                "title": "Excited",
                "images": {
                    "downsized": {"url": "https://media.giphy.com/media/legit_1/giphy.gif"}
                },
            },
            {
                "id": "unverified_2",
                "title": "Scraped",
                "images": {
                    "downsized": {"url": "https://scraped-celebrity-images.com/unverified.gif"}
                },
            },
        ]
    }

    with patch.object(service, "_fetch_and_parse") as mock_fetch:
        mock_fetch.return_value = [
            {"id": "giphy_legit_1", "download_url": "https://media.giphy.com/media/legit_1/giphy.gif"}
        ]
        results = service.search_gifs("excited")
        assert len(results) == 1
        assert "giphy.com" in results[0]["download_url"]


def test_download_gif_security_check(tmp_path):
    service = GiphyService(api_key="test_key")
    # Should reject non-giphy download URL
    with pytest.raises(ValueError, match="Security/Licensing rejection"):
        service.download_gif("https://evil-site.com/fake.gif", tmp_path / "test.gif")
