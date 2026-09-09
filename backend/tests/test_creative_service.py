from app.services.creative_service import creative_service
from app.schemas.creative import CreativePlan


def test_fallback_plan_food_category():
    fallback = creative_service.get_fallback_plan("food", "CalAI")
    assert fallback.background_asset_id == "food_01"
    assert fallback.gif_asset_id == "gif_excited_01"
    assert fallback.audio_asset_id == "es_slam_dunk"
    assert fallback.text_overlay == "POV: you finally know what you're eating"
    assert fallback.duration == 7
    assert fallback.gif_position == "top"
    assert fallback.gif_scale == 0.70
    assert fallback.text_style == "bold_stroke_shadow"


def test_fallback_plan_fitness_category():
    fallback = creative_service.get_fallback_plan("fitness")
    assert fallback.background_asset_id == "fitness_01"
    assert fallback.gif_asset_id == "gif_celebration_01"
    assert fallback.audio_asset_id == "es_drive_hype"
    assert fallback.gif_position == "top"


def test_plan_validation_rejects_invalid_id():
    invalid_plan = CreativePlan(
        concept="Test invalid",
        duration=7,
        background_asset_id="non_existent_bg_999",
        gif_asset_id="gif_excited_01",
        audio_asset_id="audio_energy_01",
        text_overlay="Test text",
    )
    assert creative_service._is_valid_plan(invalid_plan) is False


def test_plan_creative_always_returns_valid_plan():
    # Test with random/unknown category
    plan = creative_service.plan_creative({
        "name": "SuperTool",
        "category": "unknown_niche_123",
        "description": "A random app",
    })
    assert isinstance(plan, CreativePlan)
    assert creative_service._is_valid_plan(plan) is True
