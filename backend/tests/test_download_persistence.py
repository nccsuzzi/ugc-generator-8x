import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.video import Video
from app.api.routes.videos import generate_download_filename, is_video_expired

client = TestClient(app)


def test_generate_download_filename():
    v = Video(
        concept="POV: CalAI scans your food instantly",
        text_overlay="POV: your meals get logged with one snap",
        created_at=datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc),
    )
    filename = generate_download_filename(v)
    assert filename.endswith("_2026-09-09.mp4")
    assert "meals-get-logged-with-one-snap" in filename
    assert not filename.startswith("pov")


def test_is_video_expired():
    fresh_video = Video(
        created_at=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    assert not is_video_expired(fresh_video)

    expired_video = Video(
        created_at=datetime.now(timezone.utc) - timedelta(hours=25)
    )
    assert is_video_expired(expired_video)


def test_download_endpoint_content_disposition():
    db = SessionLocal()
    vid_id = str(uuid.uuid4())
    video = Video(
        id=vid_id,
        status="completed",
        current_stage="completed",
        stage_message="Video ready",
        concept="CalAI meal scanner",
        text_overlay="Instant calorie tracking",
        video_data=b"fake mp4 video content header for testing download",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db.add(video)
    db.commit()
    db.close()

    # Request as direct download
    resp = client.get(f"/api/v1/videos/{vid_id}/file?download=true")
    assert resp.status_code == 200
    assert "attachment; filename=" in resp.headers.get("Content-Disposition", "")
    assert ".mp4" in resp.headers.get("Content-Disposition", "")
    assert resp.headers.get("Content-Type") == "video/mp4"
    assert resp.content == b"fake mp4 video content header for testing download"


def test_download_expired_returns_410():
    db = SessionLocal()
    vid_id = str(uuid.uuid4())
    video = Video(
        id=vid_id,
        status="completed",
        current_stage="completed",
        stage_message="Video ready",
        video_data=b"old video content",
        created_at=datetime.now(timezone.utc) - timedelta(hours=25),
    )
    db.add(video)
    db.commit()
    db.close()

    # Video status returns expired
    status_resp = client.get(f"/api/v1/videos/{vid_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "expired"
    assert data["is_expired"] is True

    # Direct download returns 410 Gone
    download_resp = client.get(f"/api/v1/videos/{vid_id}/file?download=true")
    assert download_resp.status_code == 410
    assert "expired" in download_resp.json()["detail"].lower()


def test_conversation_history_persistence():
    db = SessionLocal()
    conv = Conversation()
    db.add(conv)
    db.flush()

    vid_id = str(uuid.uuid4())
    video = Video(
        id=vid_id,
        status="completed",
        current_stage="completed",
        concept="CalAI demo",
        text_overlay="Tracking calories easily",
        video_data=b"video data",
        created_at=datetime.now(timezone.utc),
    )
    db.add(video)
    db.flush()

    msg1 = Message(
        conversation_id=conv.id,
        role="user",
        content="I'm building CalAI: calai.app",
    )
    msg2 = Message(
        conversation_id=conv.id,
        role="assistant",
        content="Got it — I'll create a short UGC-style video for CalAI.",
        video_id=vid_id,
    )
    db.add_all([msg1, msg2])
    db.commit()
    conv_id = conv.id
    db.close()

    resp = client.get(f"/api/v1/chat/conversations/{conv_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["conversation_id"] == conv_id
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "I'm building CalAI: calai.app"

    assistant_msg = data["messages"][1]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["video_id"] == vid_id
    assert assistant_msg["video_metadata"]["status"] == "completed"
    assert assistant_msg["video_metadata"]["text_overlay"] == "Tracking calories easily"
    assert assistant_msg["video_metadata"]["download_url"] is not None
