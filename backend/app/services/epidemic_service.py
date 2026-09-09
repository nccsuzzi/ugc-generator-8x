import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EpidemicService:
    """
    Client for Epidemic Sound Partner Content API.
    Handles:
    - Server-side Bearer authentication & partner-user tracking
    - Search & Soundmatch candidate retrieval
    - Duration fitting via asynchronous Track Versions API (POST /v0/tracks/versions)
    - Polling GET /v0/tracks/versions/{jobId}
    - Download of fitted audio edit
    - Licensing Tier validation (PROTOTYPE vs PRODUCTION)
    """

    BASE_URL = "https://partner-content-api.epidemicsound.com/v0"

    def __init__(
        self,
        api_key: Optional[str] = "__DEFAULT__",
        partner_user_id: Optional[str] = None,
        tier: Optional[str] = None,
    ):
        if api_key == "__DEFAULT__":
            self.api_key = settings.EPIDEMIC_API_KEY
        else:
            self.api_key = api_key
        self.partner_user_id = partner_user_id or settings.EPIDEMIC_PARTNER_USER_ID
        self.tier = (tier or settings.EPIDEMIC_TIER).upper()

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def is_prototype(self) -> bool:
        return self.tier == "PROTOTYPE"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "x-partner-user-id": self.partner_user_id,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; UGCGenerator/1.0)",
        }

    def search_tracks(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Queries GET /v0/tracks/search using hook/topic and background mood.
        Fetches top 15 results to enable randomized asset rotation.
        Filters out tracks according to licensing tier rules.
        """
        if not self.is_available:
            logger.warning("Epidemic Sound API key not configured.")
            return []

        params = urllib.parse.urlencode({
            "term": query,
            "limit": limit,
        })
        url = f"{self.BASE_URL}/tracks/search?{params}"

        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Epidemic Sound search failed for query '{query}': {e}")
            return []

        tracks = data.get("tracks", [])
        candidates = []
        for t in tracks:
            is_preview_only = t.get("isPreviewOnly", False)
            tier_option = t.get("tierOption")

            # Record track candidate
            artists = [a.get("name", "") for a in t.get("mainArtists", []) if isinstance(a, dict)]
            artist_str = ", ".join(artists) if artists else "Epidemic Sound"
            genre_names = [g.get("name", "") if isinstance(g, dict) else str(g) for g in t.get("genres", [])]
            genre_str = ", ".join([g for g in genre_names if g])
            mood_names = [m.get("name", "") if isinstance(m, dict) else str(m) for m in t.get("moods", [])]

            candidates.append({
                "id": f"es_{t.get('id')}",
                "type": "audio",
                "track_id": t.get("id"),
                "title": t.get("title", "Soundtrack"),
                "artist": artist_str,
                "description": f"{t.get('title')} by {artist_str} ({genre_str})",
                "bpm": t.get("bpm"),
                "length": t.get("length"),
                "moods": mood_names,
                "genres": genre_names,
                "isPreviewOnly": is_preview_only,
                "tierOption": tier_option,
                "licensing_tier": "PROTOTYPE" if is_preview_only or self.is_prototype else "PRODUCTION",
            })

        return candidates

    def get_similar_tracks(self, track_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Uses /v0/tracks/{trackId}/similar endpoint to rank candidates by musical fit.
        """
        if not self.is_available:
            return []

        url = f"{self.BASE_URL}/tracks/{track_id}/similar?limit={limit}"
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("tracks", [])
        except Exception as e:
            logger.warning(f"Epidemic Sound similar tracks error: {e}")
            return []

    def create_version_job(self, track_id: str, duration_seconds: float) -> Optional[str]:
        """
        Dispatches POST /v0/tracks/versions to fit track to exact target duration (5000-10000ms).
        Returns the jobId for polling.
        """
        if not self.is_available:
            return None

        # Clean track_id prefix if present
        clean_id = track_id.replace("es_", "")
        duration_ms = int(max(5.0, min(10.0, duration_seconds)) * 1000)

        url = f"{self.BASE_URL}/tracks/versions"
        payload = json.dumps({
            "trackId": clean_id,
            "durationMs": duration_ms,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=payload, headers=self._get_headers(), method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                job_id = data.get("jobId")
                logger.info(f"Created Epidemic Sound version job {job_id} for track {clean_id} ({duration_ms}ms)")
                return job_id
        except Exception as e:
            logger.error(f"Failed to create Epidemic Sound version job: {e}")
            return None

    def poll_version_job(self, job_id: str, max_timeout_sec: int = 25) -> Optional[str]:
        """
        Polls GET /v0/tracks/versions/{jobId} until status is COMPLETED.
        Returns the direct CDN download URL for the edited audio track.
        """
        if not self.is_available or not job_id:
            return None

        url = f"{self.BASE_URL}/tracks/versions/{job_id}"
        start_time = time.time()

        while time.time() - start_time < max_timeout_sec:
            try:
                req = urllib.request.Request(url, headers=self._get_headers())
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                status = data.get("status")
                logger.debug(f"Epidemic version job {job_id} status: {status}")

                if status == "COMPLETED":
                    results = data.get("results") or []
                    if results:
                        # Prefer previewUrl or highQualityUrl
                        url_result = results[0].get("highQualityUrl") or results[0].get("previewUrl")
                        if url_result:
                            return url_result
                    logger.warning(f"Epidemic job {job_id} COMPLETED but had no download URLs")
                    return None
                elif status in ["FAILED", "CANCELLED"]:
                    logger.error(f"Epidemic version job {job_id} terminated with status: {status}")
                    return None

            except Exception as e:
                logger.warning(f"Error polling Epidemic job {job_id}: {e}")

            time.sleep(1.5)

        logger.error(f"Timed out polling Epidemic version job {job_id} after {max_timeout_sec}s")
        return None

    def download_track(self, download_url: str, destination_path: Path) -> Path:
        """
        Downloads the fitted audio file to local destination.
        """
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; UGCGenerator/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp, open(destination_path, "wb") as f:
            f.write(resp.read())

        if destination_path.stat().st_size < 5000:
            raise RuntimeError(f"Downloaded audio track at {destination_path} is suspiciously small.")

        return destination_path


epidemic_service = EpidemicService()
