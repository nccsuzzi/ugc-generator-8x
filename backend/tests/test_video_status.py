from app.core.database import SessionLocal
from app.models.video import Video


def test_video_status_transitions():
    db = SessionLocal()
    try:
        video = Video(status="pending")
        db.add(video)
        db.commit()

        assert video.status == "pending"

        # Simulating state transitions
        for next_status in ["extracting", "planning", "rendering", "completed"]:
            video.status = next_status
            db.commit()
            db.refresh(video)
            assert video.status == next_status

        # Test failure transition
        video_fail = Video(status="pending")
        db.add(video_fail)
        db.commit()

        video_fail.status = "failed"
        video_fail.error = "Test failure simulation"
        db.commit()
        db.refresh(video_fail)
        assert video_fail.status == "failed"
        assert "Test failure" in video_fail.error
    finally:
        db.close()
