import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.services.pexels_service import PexelsService


def test_pexels_service_availability():
    service = PexelsService(api_key="test_key")
    assert service.is_available is True
    no_key = PexelsService(api_key=None)
    assert no_key.is_available is False


def test_pexels_search_filters_portrait_videos():
    service = PexelsService(api_key="test_key")

    mock_data = {
        "videos": [
            {
                "id": 101,
                "duration": 8,
                "image": "https://images.pexels.com/preview.jpg",
                "video_files": [
                    # Landscape file - should be ignored
                    {"width": 1920, "height": 1080, "link": "https://videos.pexels.com/landscape.mp4"},
                    # Portrait file - should be preferred
                    {"width": 1080, "height": 1920, "link": "https://videos.pexels.com/portrait.mp4"},
                ],
            }
        ]
    }

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        import json
        mock_resp.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        results = service.search_videos("healthy food")
        assert len(results) == 1
        assert results[0]["id"] == "pexels_101"
        assert results[0]["download_url"] == "https://videos.pexels.com/portrait.mp4"
        assert results[0]["width"] == 1080
        assert results[0]["height"] == 1920


def test_pexels_download_security_check(tmp_path):
    service = PexelsService(api_key="test_key")
    with pytest.raises(ValueError, match="Security/Licensing rejection"):
        service.download_video("https://unverified-scraped.com/vid.mp4", tmp_path / "vid.mp4")
