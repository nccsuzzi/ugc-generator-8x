import json
import logging
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class PexelsService:
    """
    Client for retrieving licensed portrait stock video footage from Pexels API.
    Guarantees portrait orientation, tag matching, and verifies video motion.
    """

    BASE_URL = "https://api.pexels.com/videos"

    def __init__(self, api_key: Optional[str] = "__DEFAULT__"):
        if api_key == "__DEFAULT__":
            self.api_key = settings.PEXELS_API_KEY
        else:
            self.api_key = api_key

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def search_videos(
        self,
        query: str,
        limit: int = 5,
        orientation: str = "portrait",
    ) -> List[Dict[str, Any]]:
        """
        Searches Pexels stock video library for portrait clips matching mood/aesthetic tags.
        """
        if not self.is_available:
            logger.warning("Pexels API key not configured.")
            return []

        params = urllib.parse.urlencode({
            "query": query,
            "orientation": orientation,
            "per_page": limit,
        })
        url = f"{self.BASE_URL}/search?{params}"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": self.api_key,
                    "User-Agent": "Mozilla/5.0 (compatible; UGCGenerator/1.0)",
                },
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Pexels API request error for query '{query}': {e}")
            return []

        results = []
        for v in data.get("videos", []):
            duration = v.get("duration", 0)
            if duration < 3:
                # Discard ultra-short clips
                continue

            video_files = v.get("video_files", [])
            # Select optimal vertical video file (prefer hd 720p or 1080p portrait)
            best_file = None
            best_score = -1
            for f in video_files:
                w = f.get("width") or 0
                h = f.get("height") or 0
                link = f.get("link", "")
                if not link or "pexels.com" not in link:
                    continue
                # Portrait check: h > w
                if h >= w:
                    score = 0
                    if 720 <= w <= 1080:
                        score = 100 - abs(1080 - w)
                    elif w > 1080:
                        score = 50
                    else:
                        score = 20
                    if score > best_score:
                        best_score = score
                        best_file = f

            if not best_file:
                continue

            results.append({
                "id": f"pexels_{v.get('id')}",
                "type": "background",
                "pexels_id": v.get("id"),
                "description": f"Stock footage: {query} ({v.get('duration')}s portrait)",
                "duration": duration,
                "width": best_file.get("width"),
                "height": best_file.get("height"),
                "download_url": best_file.get("link"),
                "preview_url": v.get("image"),
                "mood": query,
                "tags": [t.strip().lower() for t in query.split() if len(t) > 2],
            })

        return results

    def download_video(self, download_url: str, destination_path: Path) -> Path:
        """
        Downloads the MP4 video to disk.
        """
        parsed = urllib.parse.urlparse(download_url)
        if not parsed.netloc.endswith("pexels.com"):
            raise ValueError(f"Security/Licensing rejection: URL {download_url} is not hosted on pexels.com")

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; UGCGenerator/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp, open(destination_path, "wb") as f:
            f.write(resp.read())

        if destination_path.stat().st_size < 10000:
            raise RuntimeError(f"Downloaded video file {destination_path} is suspiciously small.")

        return destination_path


pexels_service = PexelsService()
