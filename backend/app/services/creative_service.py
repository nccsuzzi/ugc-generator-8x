import logging
from typing import Dict, Any, Optional, List
from app.schemas.creative import CreativePlan
from app.services.asset_service import asset_service
from app.services.groq_service import groq_service

logger = logging.getLogger(__name__)

# Category Fallback Creative Plans (Reflecting Asset-Retrieval Architecture)
CATEGORY_FALLBACK_PLANS: Dict[str, Dict[str, Any]] = {
    "food": {
        "concept": "POV: finally making calorie tracking easy",
        "duration": 7,
        "background_asset_id": "food_01",
        "gif_asset_id": "gif_excited_01",
        "audio_asset_id": "es_slam_dunk",
        "text_overlay": "POV: you finally know what you're eating",
        "text_style": "bold_stroke_shadow",
        "gif_position": "top",
        "gif_scale": 0.70,
    },
    "fitness": {
        "concept": "POV: you actually stayed consistent",
        "duration": 7,
        "background_asset_id": "fitness_01",
        "gif_asset_id": "gif_celebration_01",
        "audio_asset_id": "es_drive_hype",
        "text_overlay": "POV: you actually stayed consistent",
        "text_style": "bold_stroke_shadow",
        "gif_position": "top",
        "gif_scale": 0.70,
    },
    "productivity": {
        "concept": "POV: you finally got your life together",
        "duration": 7,
        "background_asset_id": "productivity_01",
        "gif_asset_id": "gif_mindblown_01",
        "audio_asset_id": "es_slam_dunk",
        "text_overlay": "POV: you finally got your life together",
        "text_style": "bold_stroke_shadow",
        "gif_position": "top",
        "gif_scale": 0.70,
    },
    "finance": {
        "concept": "POV: your bank account is finally growing",
        "duration": 7,
        "background_asset_id": "finance_01",
        "gif_asset_id": "gif_shocked_01",
        "audio_asset_id": "es_slam_dunk",
        "text_overlay": "POV: your bank account is finally growing",
        "text_style": "bold_stroke_shadow",
        "gif_position": "top",
        "gif_scale": 0.70,
    },
    "technology": {
        "concept": "POV: AI just automated your workflow",
        "duration": 7,
        "background_asset_id": "tech_01",
        "gif_asset_id": "gif_mindblown_01",
        "audio_asset_id": "es_synth_pulse",
        "text_overlay": "POV: AI just automated your entire workflow",
        "text_style": "bold_stroke_shadow",
        "gif_position": "top",
        "gif_scale": 0.70,
    },
    "ai": {
        "concept": "POV: you discovered the ultimate tool",
        "duration": 7,
        "background_asset_id": "ai_01",
        "gif_asset_id": "gif_mindblown_01",
        "audio_asset_id": "es_synth_pulse",
        "text_overlay": "Why did nobody tell me about this?",
        "text_style": "bold_stroke_shadow",
        "gif_position": "top",
        "gif_scale": 0.70,
    },
    "beauty": {
        "concept": "POV: the routine actually worked",
        "duration": 7,
        "background_asset_id": "beauty_01",
        "gif_asset_id": "gif_glowup_01",
        "audio_asset_id": "es_lofi_aesthetic",
        "text_overlay": "POV: the routine actually worked",
        "text_style": "bold_stroke_shadow",
        "gif_position": "top",
        "gif_scale": 0.70,
    },
    "shopping": {
        "concept": "POV: your package finally arrived",
        "duration": 7,
        "background_asset_id": "shopping_01",
        "gif_asset_id": "gif_excited_01",
        "audio_asset_id": "es_slam_dunk",
        "text_overlay": "Why did nobody tell me about this?",
        "text_style": "bold_stroke_shadow",
        "gif_position": "top",
        "gif_scale": 0.70,
    },
    "lifestyle": {
        "concept": "POV: you upgraded your everyday routine",
        "duration": 7,
        "background_asset_id": "lifestyle_01",
        "gif_asset_id": "gif_excited_01",
        "audio_asset_id": "es_slam_dunk",
        "text_overlay": "This changed my daily routine",
        "text_style": "bold_stroke_shadow",
        "gif_position": "top",
        "gif_scale": 0.70,
    },
}


class CreativeService:
    """
    Coordinates asset selection and creative planning:
    Stage 1: Dynamic multi-API candidate asset retrieval
    Stage 2: Groq selection & hook copy generation
    Stage 3: Validation and deterministic fallback
    """

    def plan_creative(
        self,
        product_info: Dict[str, Any],
        excluded_ids: Optional[Dict[str, set[str]]] = None,
        prefetched_candidates: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> CreativePlan:
        category = product_info.get("category", "").lower()
        
        # Determine normalized category family
        matched_cat = self._normalize_category(category)
        
        # Stage 1: Candidate retrieval (use prefetched if provided, else fetch)
        if prefetched_candidates:
            candidates = prefetched_candidates
        else:
            candidates = asset_service.fetch_live_candidates(
                category=category,
                keywords=product_info.get("key_benefits", []) + product_info.get("marketing_angles", []),
                emotion_tags=product_info.get("emotion_tags", []),
                excluded_ids=excluded_ids,
            )

        # Stage 2: Groq Creative Selection
        plan: Optional[CreativePlan] = None
        if groq_service.is_available:
            try:
                plan = groq_service.select_creative_plan(
                    product_info=product_info,
                    candidate_backgrounds=candidates["backgrounds"],
                    candidate_gifs=candidates["gifs"],
                    candidate_audios=candidates["audios"],
                )
            except Exception as e:
                logger.warning(f"Groq creative selection error: {e}")

        # Stage 3: Validation and deterministic fallback
        if plan and self._is_valid_plan(plan):
            return plan

        logger.info(f"Using fallback plan for category: '{matched_cat}'")
        return self.get_fallback_plan(matched_cat, product_info.get("name"), candidates=candidates)

    def _normalize_category(self, category: str) -> str:
        cat = category.lower()
        if any(w in cat for w in ["calorie", "nutrition", "food", "meal", "diet", "recipe"]):
            return "food"
        if any(w in cat for w in ["fitness", "gym", "workout", "exercise", "running", "muscle"]):
            return "fitness"
        if any(w in cat for w in ["productivity", "task", "notes", "calendar", "organize", "planner"]):
            return "productivity"
        if any(w in cat for w in ["finance", "money", "budget", "invest", "banking", "crypto"]):
            return "finance"
        if any(w in cat for w in ["ai", "artificial intelligence", "machine learning", "gpt"]):
            return "ai"
        if any(w in cat for w in ["tech", "software", "developer", "saas", "code", "app"]):
            return "technology"
        if any(w in cat for w in ["beauty", "skin", "makeup", "cosmetics"]):
            return "beauty"
        if any(w in cat for w in ["shop", "store", "commerce", "fashion", "order"]):
            return "shopping"
        return "lifestyle"

    def _is_valid_plan(self, plan: CreativePlan) -> bool:
        """Strictly validates that selected asset IDs exist in the catalog."""
        bg = asset_service.get_asset_by_id(plan.background_asset_id)
        gif = asset_service.get_asset_by_id(plan.gif_asset_id)
        audio = asset_service.get_asset_by_id(plan.audio_asset_id)

        return bool(
            bg and bg["type"] == "background" and
            gif and gif["type"] == "gif" and
            audio and audio["type"] == "audio" and
            plan.text_overlay and len(plan.text_overlay.strip()) > 0
        )

    def get_fallback_plan(
        self,
        category: str,
        product_name: Optional[str] = None,
        candidates: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> CreativePlan:
        """Retrieves verified fallback plan, leveraging available candidate assets for rotation."""
        import random
        base = CATEGORY_FALLBACK_PLANS.get(category, CATEGORY_FALLBACK_PLANS["lifestyle"]).copy()

        # If candidates are available, choose from them for diversity
        if candidates:
            if candidates.get("backgrounds"):
                base["background_asset_id"] = random.choice(candidates["backgrounds"])["id"]
            if candidates.get("gifs"):
                base["gif_asset_id"] = random.choice(candidates["gifs"])["id"]
            if candidates.get("audios"):
                base["audio_asset_id"] = random.choice(candidates["audios"])["id"]

        # If product name is provided and category is food / CalAI, ensure classic hook
        if product_name and "cal" in product_name.lower():
            base["text_overlay"] = "POV: you finally know what you're eating"
            base["gif_position"] = "top"
            base["gif_scale"] = 0.70
            base["text_style"] = "bold_stroke_shadow"

        return CreativePlan(**base)


creative_service = CreativeService()
