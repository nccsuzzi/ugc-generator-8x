import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.video import Video

client = TestClient(app)


def test_export_blocked_in_prototype_mode():
    db = SessionLocal()
    vid_id = str(uuid.uuid4())
    video = Video(
        id=vid_id,
        status="completed",
        licensing_tier="PROTOTYPE",
        concept="Test CalAI UGC",
        duration=7,
        text_overlay="POV: calorie tracking",
        video_data=b"fake_mp4_content",
    )
    db.add(video)
    db.commit()
    db.close()

    response = client.post(f"/api/v1/videos/{vid_id}/export")
    assert response.status_code == 403
    detail = response.json().get("detail", "")
    assert "Export blocked" in detail
    assert "PROTOTYPE" in detail


def test_export_allowed_in_production_mode():
    db = SessionLocal()
    vid_id = str(uuid.uuid4())
    video = Video(
        id=vid_id,
        status="completed",
        licensing_tier="PRODUCTION",
        concept="Test CalAI UGC Live",
        duration=7,
        text_overlay="POV: calorie tracking",
        video_data=b"fake_mp4_content",
    )
    db.add(video)
    db.commit()
    db.close()

    response = client.post(f"/api/v1/videos/{vid_id}/export")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "exported"
    assert data.get("licensing_tier") == "PRODUCTION"
    assert "export_url" in data
