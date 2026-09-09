import asyncio
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.video import Video
from app.services.product_extractor import product_extractor
from app.services.groq_service import groq_service
from app.services.creative_service import creative_service
from app.services.asset_service import asset_service
from app.services.giphy_service import giphy_service
from app.services.pexels_service import pexels_service
from app.services.epidemic_service import epidemic_service
from app.services.ffmpeg_service import ffmpeg_service
from app.services.video_storage import PostgresVideoStorage
from app.utils.file_utils import safe_cleanup_dir, ensure_dir

logger = logging.getLogger(__name__)


class VideoService:
    """
    Coordinates the AI-organizing & asset assembly pipeline:
    1. extracting: Extract product website data
    2. analyzing: Groq AI analyzes product and audience facts
    3. searching_assets: Parallel retrieval of licensed candidate pools, rolling exclusion, rank-weighted sampling
    4. adapting_audio: Parallel download of assets and Epidemic Sound duration adaptation
    5. rendering: FFmpeg 4-layer composition (soft-edge reaction GIF, karaoke text, loudnorm -14 LUFS)
    6. validating: Automated QA ffprobe validation, licensing gate, timing breakdown
    7. completed: Persist in PostgreSQL BYTEA & metadata
    """

    async def generate_video_pipeline(self, video_id: str, url: str, user_hint: Optional[str] = None) -> None:
        db: Session = SessionLocal()
        storage = PostgresVideoStorage(db)
        temp_dir = ensure_dir(settings.TEMP_DIR / video_id)
        t_pipeline_start = time.time()
        timing_breakdown: Dict[str, float] = {}

        def update_stage(status_val: str, stage_val: str, msg_val: str) -> None:
            video_rec = db.query(Video).filter(Video.id == video_id).first()
            if video_rec:
                video_rec.status = status_val
                video_rec.current_stage = stage_val
                video_rec.stage_message = msg_val
                db.commit()

        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                logger.error(f"Video {video_id} not found in database.")
                return

            # Stage 1: Extracting product
            t0 = time.time()
            update_stage("extracting", "extracting", "Reading product page and extracting facts...")
            logger.info(f"[{video_id}] Starting extraction for: {url}")

            raw_page_data = await product_extractor.extract(url, user_hint)
            timing_breakdown["extracting_sec"] = round(time.time() - t0, 2)

            # Stage 2: Analyzing product
            t1 = time.time()
            update_stage("planning", "analyzing", "Analyzing product benefits and creative angles...")
            logger.info(f"[{video_id}] Understanding product and planning creative...")

            # AI Understanding with fallback
            product_data = None
            if groq_service.is_available:
                try:
                    product_data = groq_service.understand_product(
                        raw_content=raw_page_data.get("content", ""),
                        user_hint=user_hint,
                    )
                except Exception as e:
                    logger.warning(f"Groq understanding error: {e}")

            if not product_data:
                title = raw_page_data.get("title", "Product")
                product_data = {
                    "name": title,
                    "category": "food" if "cal" in title.lower() or "cal" in url.lower() else "lifestyle",
                    "description": raw_page_data.get("description", f"UGC video for {title}"),
                    "target_audience": "General consumers and social media users",
                    "key_benefits": ["Easy to use", "Saves time", "Great results"],
                    "marketing_angles": ["Relatable daily routine", "Must-have recommendation"],
                    "emotion_tags": ["pure relief", "mind blown", "hyped celebration"],
                }

            # Save / Link Product in DB
            db_product = Product(
                url=url,
                name=product_data.get("name", "Product"),
                description=product_data.get("description", ""),
                category=product_data.get("category", "lifestyle"),
                target_audience=product_data.get("target_audience", ""),
                benefits=product_data.get("key_benefits", []),
                marketing_angles=product_data.get("marketing_angles", []),
            )
            db.add(db_product)
            db.flush()

            video.product_id = db_product.id
            db.commit()
            timing_breakdown["analyzing_sec"] = round(time.time() - t1, 2)

            # Stage 3: Searching assets (Parallel Search + Rolling Exclusion + Rank-Weighted Selection)
            t2 = time.time()
            update_stage("planning", "searching_assets", "Searching licensed media catalogs (Pexels, Giphy, Epidemic Sound)...")
            logger.info(f"[{video_id}] Querying licensed media catalogs with rolling exclusion...")

            # Query persistent asset exclusion history (last 20 generations)
            excluded_gifs = asset_service.get_recent_excluded_asset_ids(db, "gif", limit=20)
            excluded_audios = asset_service.get_recent_excluded_asset_ids(db, "audio", limit=20)
            excluded_ids = {"gif": excluded_gifs, "audio": excluded_audios}
            logger.info(f"[{video_id}] Rolling exclusions: {len(excluded_gifs)} GIFs, {len(excluded_audios)} Audios")

            # Asynchronous parallel search across Pexels, Giphy, Epidemic
            candidates = await asset_service.fetch_live_candidates_async(
                category=product_data.get("category", "lifestyle"),
                keywords=product_data.get("key_benefits", []) + product_data.get("marketing_angles", []),
                emotion_tags=product_data.get("emotion_tags", []),
                excluded_ids=excluded_ids,
            )

            # Creative Direction Plan (AI organizes and ranks pre-existing licensed assets + generates hook copy)
            plan = creative_service.plan_creative(
                product_info=product_data,
                excluded_ids=excluded_ids,
                prefetched_candidates=candidates,
            )
            logger.info(f"[{video_id}] Creative plan chosen: {plan.concept} | text: '{plan.text_overlay}' | GIF: {plan.gif_asset_id} | Audio: {plan.audio_asset_id}")

            video.concept = plan.concept
            video.duration = plan.duration
            video.background_asset_id = plan.background_asset_id
            video.gif_asset_id = plan.gif_asset_id
            video.audio_asset_id = plan.audio_asset_id
            video.text_overlay = plan.text_overlay
            video.text_style = plan.text_style
            video.gif_position = plan.gif_position
            video.gif_scale = plan.gif_scale
            db.commit()
            timing_breakdown["searching_assets_sec"] = round(time.time() - t2, 2)

            # Stage 4: Adapting audio & parallel asset downloading
            t3 = time.time()
            update_stage("rendering", "adapting_audio", "Adapting soundtrack to exact duration with Epidemic Sound API...")
            logger.info(f"[{video_id}] Downloading assets and adapting soundtrack in parallel...")

            bg_meta = asset_service.get_asset_by_id(plan.background_asset_id) or {}
            gif_meta = asset_service.get_asset_by_id(plan.gif_asset_id) or {}
            audio_meta = asset_service.get_asset_by_id(plan.audio_asset_id) or {}

            # Parallel download and audio adaptation
            bg_task = asyncio.to_thread(self._resolve_background, bg_meta, temp_dir)
            gif_task = asyncio.to_thread(self._resolve_gif, gif_meta, temp_dir)
            audio_task = asyncio.to_thread(self._resolve_audio, audio_meta, plan.duration, temp_dir)

            results = await asyncio.gather(bg_task, gif_task, audio_task)
            bg_path = results[0]
            gif_path = results[1]
            audio_path, active_tier = results[2]
            timing_breakdown["adapting_audio_sec"] = round(time.time() - t3, 2)

            # Stage 5: Rendering
            t4 = time.time()
            update_stage("rendering", "rendering", "Compositing 4-layer 9:16 UGC video with FFmpeg...")
            logger.info(f"[{video_id}] Assembling 4-layer UGC ad with FFmpeg...")

            # Track asset provenance
            asset_sources = {
                "background": {
                    "id": plan.background_asset_id,
                    "source": bg_meta.get("source", "pexels"),
                    "description": bg_meta.get("description"),
                    "download_url": bg_meta.get("download_url"),
                },
                "reaction_gif": {
                    "id": plan.gif_asset_id,
                    "source": gif_meta.get("source", "giphy"),
                    "giphy_id": gif_meta.get("giphy_id"),
                    "download_url": gif_meta.get("download_url"),
                },
                "audio": {
                    "id": plan.audio_asset_id,
                    "source": audio_meta.get("source", "epidemicsound"),
                    "track_id": audio_meta.get("track_id"),
                    "title": audio_meta.get("title"),
                    "artist": audio_meta.get("artist"),
                    "licensing_tier": active_tier,
                },
            }

            # Render final MP4 via FFmpeg and execute strict QA validation
            rendered_mp4, qa_report = await asyncio.to_thread(
                ffmpeg_service.render_video,
                video_id=video_id,
                plan=plan,
                background_path=bg_path,
                gif_path=gif_path,
                audio_path=audio_path,
                licensing_tier=active_tier,
            )
            timing_breakdown["rendering_sec"] = round(time.time() - t4, 2)

            # Stage 6: Validating
            t5 = time.time()
            update_stage("rendering", "validating", "Running automated QA and ffprobe compliance validation...")
            timing_breakdown["validating_sec"] = round(time.time() - t5, 2)
            timing_breakdown["total_pipeline_sec"] = round(time.time() - t_pipeline_start, 2)

            # Attach timing breakdown to QA report and log
            qa_report["timing_breakdown"] = timing_breakdown
            logger.info(f"[{video_id}] Pipeline Timing Breakdown: {timing_breakdown}")

            # Store rendered MP4 directly in PostgreSQL BYTEA
            logger.info(f"[{video_id}] Storing rendered MP4 directly in PostgreSQL BYTEA...")
            storage.save(video_id, rendered_mp4)

            # Cleanup temp files
            safe_cleanup_dir(temp_dir)

            # Record used assets in AssetHistory for persistent rolling exclusion
            if plan.gif_asset_id:
                asset_service.record_used_asset(db, "gif", plan.gif_asset_id, video_id)
            if gif_meta.get("giphy_id") and gif_meta["giphy_id"] != plan.gif_asset_id:
                asset_service.record_used_asset(db, "gif", gif_meta["giphy_id"], video_id)

            if plan.audio_asset_id:
                asset_service.record_used_asset(db, "audio", plan.audio_asset_id, video_id)
            if audio_meta.get("track_id") and audio_meta["track_id"] != plan.audio_asset_id:
                asset_service.record_used_asset(db, "audio", audio_meta["track_id"], video_id)

            # Stage 7: Completed
            update_stage("completed", "completed", "Video ready!")
            video.licensing_tier = active_tier
            video.asset_sources = asset_sources
            video.qa_metadata = qa_report
            video.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"[{video_id}] Video generation successfully completed in {timing_breakdown['total_pipeline_sec']}s (Licensing: {active_tier})!")

        except Exception as e:
            logger.exception(f"[{video_id}] Video generation failed: {e}")
            safe_cleanup_dir(temp_dir)
            try:
                db.rollback()
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.status = "failed"
                    video.error = str(e)
                    db.commit()
            except Exception as dbe:
                logger.error(f"Failed to record video failure status: {dbe}")
        finally:
            db.close()

    def _resolve_background(self, bg_meta: Dict[str, Any], temp_dir: Path) -> Path:
        """Downloads stock background video from Pexels or uses local fallback."""
        bg_dest = temp_dir / "background.mp4"
        download_url = bg_meta.get("download_url")

        if download_url and "pexels.com" in download_url:
            try:
                return pexels_service.download_video(download_url, bg_dest)
            except Exception as e:
                logger.warning(f"Failed downloading Pexels video from {download_url}: {e}")

        # Check local assets directory
        filename = bg_meta.get("filename")
        if filename:
            local_path = settings.ASSETS_DIR / "backgrounds" / filename
            if local_path.exists() and local_path.stat().st_size > 10000:
                return local_path

        # If Pexels API is available, search dynamically
        if pexels_service.is_available:
            try:
                candidates = pexels_service.search_videos(query="healthy food portrait", limit=2)
                if candidates and candidates[0].get("download_url"):
                    return pexels_service.download_video(candidates[0]["download_url"], bg_dest)
            except Exception as e:
                logger.warning(f"Dynamic Pexels search failed: {e}")

        # Default fallback
        existing_bgs = list((settings.ASSETS_DIR / "backgrounds").glob("*.mp4"))
        if existing_bgs:
            return existing_bgs[0]

        raise RuntimeError("No licensed background stock footage available.")

    def _resolve_gif(self, gif_meta: Dict[str, Any], temp_dir: Path) -> Path:
        """Downloads reaction GIF from Giphy catalog or uses local fallback."""
        gif_dest = temp_dir / "reaction.gif"
        download_url = gif_meta.get("download_url")

        if download_url and "giphy.com" in download_url:
            try:
                return giphy_service.download_gif(download_url, gif_dest)
            except Exception as e:
                logger.warning(f"Failed downloading Giphy GIF: {e}")

        # Check local assets
        filename = gif_meta.get("filename")
        if filename:
            local_path = settings.ASSETS_DIR / "gifs" / filename
            if local_path.exists() and local_path.stat().st_size > 5000:
                return local_path

        # If Giphy API is available, fetch trending
        if giphy_service.is_available:
            try:
                trending = giphy_service.get_trending(limit=1)
                if trending and trending[0].get("download_url"):
                    return giphy_service.download_gif(trending[0]["download_url"], gif_dest)
            except Exception as e:
                logger.warning(f"Dynamic Giphy fetch failed: {e}")

        existing_gifs = list((settings.ASSETS_DIR / "gifs").glob("*.gif"))
        if existing_gifs:
            return existing_gifs[0]

        raise RuntimeError("No licensed reaction GIF available.")

    def _resolve_audio(self, audio_meta: Dict[str, Any], duration: int, temp_dir: Path) -> tuple[Path, str]:
        """
        Queries Epidemic Sound Partner API:
        Creates a versioning job (POST /v0/tracks/versions) fitting the track to exact duration,
        polls GET /v0/tracks/versions/{jobId}, and downloads the edited track.
        Returns (audio_path, licensing_tier).
        """
        active_tier = settings.EPIDEMIC_TIER.upper()
        audio_dest = temp_dir / "music.mp3"
        track_id = audio_meta.get("track_id") or "4c20406f-6937-49f7-8dcb-39647af926a4"

        if epidemic_service.is_available and track_id:
            try:
                job_id = epidemic_service.create_version_job(track_id=track_id, duration_seconds=duration)
                if job_id:
                    cdn_url = epidemic_service.poll_version_job(job_id=job_id, max_timeout_sec=15)
                    if cdn_url:
                        downloaded = epidemic_service.download_track(cdn_url, audio_dest)
                        return downloaded, active_tier
            except Exception as e:
                logger.warning(f"Epidemic Sound track versioning failed: {e}")

        # Fallback to local audio
        filename = audio_meta.get("filename")
        if filename:
            local_path = settings.ASSETS_DIR / "audio" / filename
            if local_path.exists() and local_path.stat().st_size > 5000:
                return local_path, active_tier

        existing_audios = list((settings.ASSETS_DIR / "audio").glob("*.mp3"))
        if existing_audios:
            return existing_audios[0], active_tier

        raise RuntimeError("No licensed soundtrack audio track available.")


video_service = VideoService()
