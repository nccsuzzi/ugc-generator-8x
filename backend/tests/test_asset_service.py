from app.services.asset_service import asset_service, CURATED_ASSETS


def test_curated_assets_count_and_types():
    assert len(CURATED_ASSETS) >= 30
    backgrounds = [a for a in CURATED_ASSETS if a["type"] == "background"]
    gifs = [a for a in CURATED_ASSETS if a["type"] == "gif"]
    audios = [a for a in CURATED_ASSETS if a["type"] == "audio"]

    assert len(backgrounds) >= 10
    assert len(gifs) >= 15
    assert len(audios) >= 5


def test_asset_retrieval_by_stable_id():
    food_bg = asset_service.get_asset_by_id("food_01")
    assert food_bg is not None
    assert food_bg["type"] == "background"
    assert "food" in food_bg["tags"]

    excited_gif = asset_service.get_asset_by_id("gif_excited_01")
    assert excited_gif is not None
    assert excited_gif["type"] == "gif"
    assert excited_gif["mood"] == "excited"


def test_filter_candidates_food_category():
    candidates = asset_service.filter_candidates("calorie tracking", ["nutrition", "meal"])
    bgs = candidates["backgrounds"]
    gifs = candidates["gifs"]
    audios = candidates["audios"]

    assert len(bgs) > 0
    assert len(gifs) > 0
    assert len(audios) > 0

    # Top background should be food-related
    top_bg_tags = set(bgs[0]["tags"])
    assert any(t in top_bg_tags for t in ["food", "nutrition", "meal", "calorie", "diet"])
