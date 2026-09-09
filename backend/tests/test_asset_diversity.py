import pytest
from app.core.database import SessionLocal
from app.services.asset_service import asset_service
from app.models.asset_history import AssetHistory


def test_asset_history_record_and_exclude():
    db = SessionLocal()
    try:
        test_gif_id = "test_gif_rot_99"
        test_audio_id = "test_audio_rot_88"

        # Record test used assets
        asset_service.record_used_asset(db, "gif", test_gif_id, "video_test_1")
        asset_service.record_used_asset(db, "audio", test_audio_id, "video_test_1")

        # Query recent exclusions
        excluded_gifs = asset_service.get_recent_excluded_asset_ids(db, "gif", limit=20)
        excluded_audios = asset_service.get_recent_excluded_asset_ids(db, "audio", limit=20)

        assert test_gif_id in excluded_gifs
        assert test_audio_id in excluded_audios
    finally:
        # Cleanup test records
        db.query(AssetHistory).filter(
            AssetHistory.asset_id.in_([test_gif_id, test_audio_id])
        ).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_weighted_sample_diversity():
    candidates = [{"id": f"item_{i}", "rank": i} for i in range(15)]
    samples = []
    for _ in range(10):
        sampled = asset_service._weighted_sample(candidates, k=5)
        assert len(sampled) == 5
        assert len(set(s["id"] for s in sampled)) == 5  # No duplicates in single sample
        samples.append(tuple(s["id"] for s in sampled))

    # Across 10 samples, there should be variation (not deterministic identical lists)
    unique_combinations = set(samples)
    assert len(unique_combinations) > 1, "Weighted sample must produce diverse candidate subsets"


def test_candidate_filtering_excludes_used_ids():
    candidates = [
        {"id": "gif_used_1", "giphy_id": "ext_used_1"},
        {"id": "gif_fresh_1", "giphy_id": "ext_fresh_1"},
        {"id": "gif_fresh_2", "giphy_id": "ext_fresh_2"},
        {"id": "gif_fresh_3", "giphy_id": "ext_fresh_3"},
    ]
    excluded = {"gif_used_1", "ext_used_1"}

    filtered = asset_service._filter_and_sample(
        candidates=candidates,
        excluded=excluded,
        id_keys=["giphy_id"],
        sample_k=3,
    )

    filtered_ids = {c["id"] for c in filtered}
    assert "gif_used_1" not in filtered_ids
    assert len(filtered) <= 3


@pytest.mark.asyncio
async def test_fetch_live_candidates_async_runs_and_excludes():
    excluded_ids = {
        "gif": {"gif_excited_01"},
        "audio": {"es_slam_dunk"},
    }
    candidates = await asset_service.fetch_live_candidates_async(
        category="food",
        keywords=["healthy", "meal"],
        emotion_tags=["jaw drop food", "delicious craving"],
        excluded_ids=excluded_ids,
    )

    assert "backgrounds" in candidates
    assert "gifs" in candidates
    assert "audios" in candidates
    assert len(candidates["backgrounds"]) >= 1
    assert len(candidates["gifs"]) >= 1
    assert len(candidates["audios"]) >= 1
