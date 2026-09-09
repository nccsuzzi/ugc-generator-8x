import json
import logging
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
from app.core.config import settings

logger = logging.getLogger(__name__)


class GiphyService:
    """
    Client for retrieving licensed reaction GIFs via the official Giphy API.
    Enforces content filtering: only accepts items hosted on official Giphy CDNs (*.giphy.com).
    """

    BASE_URL = "https://api.giphy.com/v1/gifs"

    def __init__(self, api_key: Optional[str] = "__DEFAULT__"):
        if api_key == "__DEFAULT__":
            self.api_key = settings.GIPHY_API_KEY
        else:
            self.api_key = api_key

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def search_gifs(self, query: str, limit: int = 15, rating: str = "pg") -> List[Dict[str, Any]]:
        """
        Queries Giphy search endpoint by mood / reaction keywords.
        Fetches top 15 results to enable randomized asset rotation.
        """
        if not self.is_available:
            logger.warning("Giphy API key not configured.")
            return []

        params = urllib.parse.urlencode({
            "api_key": self.api_key,
            "q": query,
            "limit": limit,
            "rating": rating,
            "lang": "en",
        })
        url = f"{self.BASE_URL}/search?{params}"
        return self._fetch_and_parse(url, default_mood=query)

    def get_trending(self, limit: int = 15, rating: str = "pg") -> List[Dict[str, Any]]:
        """
        Queries Giphy trending endpoint for high-engagement viral reaction GIFs.
        """
        if not self.is_available:
            logger.warning("Giphy API key not configured.")
            return []

        params = urllib.parse.urlencode({
            "api_key": self.api_key,
            "limit": limit,
            "rating": rating,
        })
        url = f"{self.BASE_URL}/trending?{params}"
        return self._fetch_and_parse(url, default_mood="trending")

    def _fetch_and_parse(self, request_url: str, default_mood: str) -> List[Dict[str, Any]]:
        try:
            req = urllib.request.Request(
                request_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; UGCGenerator/1.0)"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Giphy API request error: {e}")
            return []

        results = []
        for item in data.get("data", []):
            images = item.get("images", {})
            # Prefer downsized or original url
            gif_url = (
                images.get("downsized", {}).get("url")
                or images.get("original", {}).get("url")
            )
            if not gif_url:
                continue

            # Content filter: Reject any GIF whose source isn't Giphy's licensed CDN
            parsed_url = urllib.parse.urlparse(gif_url)
            if not parsed_url.netloc.endswith("giphy.com"):
                logger.warning(f"Rejected non-Giphy CDN asset: {gif_url}")
                continue

            results.append({
                "id": f"giphy_{item.get('id')}",
                "type": "gif",
                "giphy_id": item.get("id"),
                "title": item.get("title", "Reaction GIF"),
                "description": item.get("title", "Reaction GIF"),
                "source_url": item.get("url"),
                "download_url": gif_url,
                "mood": default_mood,
                "tags": [t.strip().lower() for t in (item.get("title", "") + " " + default_mood).split() if len(t) > 2],
            })

        return results

    def download_gif(self, download_url: str, destination_path: Path) -> Path:
        """
        Downloads the animated GIF to disk and verifies it is an animated loop (multiple frames).
        """
        # Validate CDN domain before downloading
        parsed = urllib.parse.urlparse(download_url)
        if not parsed.netloc.endswith("giphy.com"):
            raise ValueError(f"Security/Licensing rejection: URL {download_url} is not hosted on giphy.com")

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; UGCGenerator/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp, open(destination_path, "wb") as f:
            f.write(resp.read())

        # Verify GIF file integrity and check for animation frames
        with Image.open(destination_path) as im:
            if not getattr(im, "is_animated", False) and im.n_frames <= 1:
                logger.warning(f"Downloaded GIF at {destination_path} only has 1 frame (static).")

        return destination_path


giphy_service = GiphyService()
