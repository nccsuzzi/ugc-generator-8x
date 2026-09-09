import re
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.video import Video
from app.schemas.video import VideoStatusResponse
from app.services.video_storage import PostgresVideoStorage

router = APIRouter()

VIDEO_RETENTION_HOURS = 24


def is_video_expired(video: Video) -> bool:
    """
    Checks whether a video has passed the 24-hour retention/download window.
    """
    if not video.created_at:
        return False
    now = datetime.now(timezone.utc)
    created = video.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return (now - created) > timedelta(hours=VIDEO_RETENTION_HOURS)


def generate_download_filename(video: Video) -> str:
    """
    Generates a human-readable, descriptive filename for direct video downloads.
    e.g. calai-pov-meals-scanned_2026-09-09.mp4
    """
    source_text = video.text_overlay or video.concept or "ugc-ad"
    cleaned = re.sub(r"^(pov|hook)\s*:\s*", "", source_text, flags=re.IGNORECASE)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", cleaned).strip("-").lower()[:48]
    if not slug:
        slug = "ugc-video"
    date_str = (video.created_at or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    return f"{slug}_{date_str}.mp4"


def build_video_status_response(video: Video) -> VideoStatusResponse:
    """
    Constructs an enriched VideoStatusResponse, factoring in 24h retention expiry.
    """
    expired = is_video_expired(video)
    effective_status = "expired" if expired else video.status
    stage_message = (
        "This video generation has expired (24-hour retention window)."
        if expired
        else (video.stage_message or "Processing video...")
    )
    video_url = (
        f"/api/v1/videos/{video.id}/file"
        if video.status == "completed" and not expired
        else None
    )
    download_url = (
        f"/api/v1/videos/{video.id}/file?download=true"
        if video.status == "completed" and not expired
        else None
    )

    return VideoStatusResponse(
        id=video.id,
        status=effective_status,
        current_stage=video.current_stage or video.status,
        stage_message=stage_message,
        duration=video.duration,
        concept=video.concept,
        text_overlay=video.text_overlay,
        background_asset_id=video.background_asset_id,
        gif_asset_id=video.gif_asset_id,
        audio_asset_id=video.audio_asset_id,
        video_url=video_url,
        download_url=download_url,
        error=video.error,
        licensing_tier=video.licensing_tier or "PROTOTYPE",
        asset_sources=video.asset_sources,
        qa_metadata=video.qa_metadata,
        is_expired=expired,
        created_at=video.created_at,
        completed_at=video.completed_at,
    )


@router.get("/videos/{video_id}", response_model=VideoStatusResponse)
def get_video_status(video_id: str, db: Session = Depends(get_db)):
    """
    Returns the generation status and metadata of a video.
    Polled by the frontend until 'completed', 'failed', or 'expired'.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return build_video_status_response(video)


@router.post("/videos/{video_id}/export")
@router.post("/videos/{video_id}/publish")
def export_video(video_id: str, db: Session = Depends(get_db)):
    """
    Enforces the Epidemic Sound Licensing Gate:
    Free/PROTOTYPE tier tracks cannot be sublicensed or exported for live/published content.
    Blocks export and surfaces a clear 403 error if attempted in PROTOTYPE mode.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if is_video_expired(video):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Video has expired (24-hour retention window). Cannot export.",
        )

    if video.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot export video with status '{video.status}'. Must be 'completed'.",
        )

    # Licensing Gate Verification
    tier = (video.licensing_tier or "PROTOTYPE").upper()
    if tier == "PROTOTYPE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Export blocked: Video contains audio licensed under PROTOTYPE tier. "
                "Free tier tracks cannot be sublicensed or used in live/published content. "
                "Upgrade to a PRODUCTION (Scale/Enterprise) tier key to sublicense and export."
            ),
        )

    return {
        "video_id": video.id,
        "status": "exported",
        "licensing_tier": tier,
        "export_url": f"/api/v1/videos/{video.id}/file",
        "message": "Video successfully licensed and authorized for live publication.",
    }


@router.get("/videos/{video_id}/download")
@router.get("/videos/{video_id}/file")
def get_video_file(
    video_id: str,
    request: Request,
    download: bool = Query(default=False, description="Whether to enforce Content-Disposition attachment download"),
    db: Session = Depends(get_db),
):
    """
    Streams or downloads the raw MP4 video directly from PostgreSQL BYTEA storage.
    - If `download=true` or path is `/download`: serves with `Content-Disposition: attachment; filename="..."`
    - Otherwise: supports HTTP Range requests (206 Partial Content) for browser seeking and playback.
    - Rejects with HTTP 410 Gone if past the 24-hour retention window.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if is_video_expired(video):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Video download link has expired (24-hour retention window). Please generate a new video.",
        )

    storage = PostgresVideoStorage(db)
    video_bytes = storage.get(video_id)
    if not video_bytes:
        raise HTTPException(status_code=404, detail="Video file data not found or still rendering.")

    file_size = len(video_bytes)
    is_download = download or request.url.path.endswith("/download")
    safe_filename = generate_download_filename(video)

    # If requested as direct download, force attachment header
    if is_download:
        headers = {
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
            "Cache-Control": "public, max-age=86400",
        }
        return Response(content=video_bytes, status_code=status.HTTP_200_OK, headers=headers)

    # Standard browser playback with HTTP Range support
    range_header = request.headers.get("Range")
    if range_header:
        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else file_size - 1
            if start >= file_size:
                raise HTTPException(status_code=416, detail="Requested range not satisfiable")
            end = min(end, file_size - 1)
            chunk_size = end - start + 1
            chunk = video_bytes[start : end + 1]

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Type": "video/mp4",
                "Cache-Control": "public, max-age=3600",
            }
            return Response(content=chunk, status_code=status.HTTP_206_PARTIAL_CONTENT, headers=headers)

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": "video/mp4",
        "Cache-Control": "public, max-age=3600",
    }
    return Response(content=video_bytes, status_code=status.HTTP_200_OK, headers=headers)
