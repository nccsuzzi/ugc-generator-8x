import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.giphy_service import giphy_service
from app.services.pexels_service import pexels_service
from app.services.epidemic_service import epidemic_service

logger = logging.getLogger(__name__)

# Base Verified Licensed Asset Catalog (Curated fallback entries for offline/testing robustness)
CURATED_ASSETS: List[Dict[str, Any]] = [
    # --- BACKGROUNDS (Pexels / Licensed stock format) ---
    {
        "id": "food_01",
        "type": "background",
        "description": "Close-up footage of delicious healthy meal preparation and eating",
        "tags": ["food", "nutrition", "meal", "eating", "cooking", "calorie", "diet", "healthy"],
        "mood": "healthy meal",
        "source": "pexels",
        "download_url": "https://videos.pexels.com/video-files/8851743/8851743-hd_1080_2048_25fps.mp4",
    },
    {
        "id": "food_02",
        "type": "background",
        "description": "Aesthetic fresh salad bowl, macro vegetables, and clean food lifestyle",
        "tags": ["food", "healthy", "diet", "nutrition", "kitchen", "wellness", "salad"],
        "mood": "clean food",
        "source": "pexels",
        "download_url": "https://videos.pexels.com/video-files/8851743/8851743-hd_1080_2048_25fps.mp4",
    },
    {
        "id": "fitness_01",
        "type": "background",
        "description": "High-intensity gym workout and barbell training",
        "tags": ["fitness", "workout", "gym", "health", "exercise", "training", "muscle"],
        "mood": "intense gym",
        "source": "pexels",
    },
    {
        "id": "fitness_02",
        "type": "background",
        "description": "Athlete running outdoors in morning sunlight on track",
        "tags": ["fitness", "running", "cardio", "sports", "outdoors", "health", "active"],
        "mood": "running athlete",
        "source": "pexels",
    },
    {
        "id": "productivity_01",
        "type": "background",
        "description": "Modern minimalist aesthetic desk setup with laptop and coffee",
        "tags": ["productivity", "work", "focus", "desk", "routine", "study", "laptop", "deepwork"],
        "mood": "desk workspace",
        "source": "pexels",
    },
    {
        "id": "productivity_02",
        "type": "background",
        "description": "Organizing task calendar and digital notes on tablet screen",
        "tags": ["productivity", "organize", "planning", "time", "tasks", "apps", "schedule"],
        "mood": "digital planner",
        "source": "pexels",
    },
    {
        "id": "finance_01",
        "type": "background",
        "description": "Green dynamic financial charts and investment growth graphic",
        "tags": ["finance", "money", "investing", "budget", "crypto", "wealth", "stocks"],
        "mood": "finance charts",
        "source": "pexels",
    },
    {
        "id": "finance_02",
        "type": "background",
        "description": "Minimalist digital banking and card transaction aesthetic",
        "tags": ["finance", "banking", "savings", "cash", "cards", "fintech", "budget"],
        "mood": "digital banking",
        "source": "pexels",
    },
    {
        "id": "tech_01",
        "type": "background",
        "description": "Sleek dark mode software UI with animated code and analytics",
        "tags": ["technology", "software", "code", "developer", "saas", "dashboard", "web"],
        "mood": "technology code",
        "source": "pexels",
    },
    {
        "id": "ai_01",
        "type": "background",
        "description": "Futuristic neural network glowing waves and AI data stream",
        "tags": ["ai", "tech", "artificial intelligence", "smart", "automation", "future"],
        "mood": "artificial intelligence",
        "source": "pexels",
    },
    {
        "id": "beauty_01",
        "type": "background",
        "description": "Skincare serum droplet with sunlit golden hour glow",
        "tags": ["beauty", "skincare", "cosmetics", "glow", "selfcare", "wellness"],
        "mood": "beauty skincare",
        "source": "pexels",
    },
    {
        "id": "shopping_01",
        "type": "background",
        "description": "Exciting trendy ecommerce unboxing and shopping haul reveal",
        "tags": ["shopping", "ecommerce", "unboxing", "haul", "fashion", "order"],
        "mood": "shopping retail",
        "source": "pexels",
    },
    {
        "id": "lifestyle_01",
        "type": "background",
        "description": "Warm sunny morning routine with coffee pouring and city view",
        "tags": ["lifestyle", "morning", "aesthetic", "vlog", "routine", "daily", "general"],
        "mood": "morning lifestyle",
        "source": "pexels",
    },

    # --- REACTION GIFS (Giphy Catalog Identifiers) ---
    {
        "id": "gif_excited_01",
        "type": "gif",
        "giphy_id": "75ZaxapnyMp2w",
        "description": "Person reacting with jaw-dropping excitement and pure joy",
        "tags": ["excited", "happy", "celebration", "positive", "wow", "food", "calorie"],
        "mood": "excited",
        "source": "giphy",
        "download_url": "https://media2.giphy.com/media/v1.Y2lkPTJkZTk1OTI4czFpcDlkYnhzcmJ2amU2YmtmODE3bzJ2N2VpcHZpOHYzNml3MG9iMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/75ZaxapnyMp2w/giphy.gif",
    },
    {
        "id": "gif_celebration_01",
        "type": "gif",
        "giphy_id": "artj92V8o75VPL7AeQ",
        "description": "Arms raised high in victorious triumph celebration",
        "tags": ["celebration", "win", "fitness", "success", "achievement", "victory"],
        "mood": "celebration",
        "source": "giphy",
        "download_url": "https://media2.giphy.com/media/v1.Y2lkPTJkZTk1OTI4czFpcDlkYnhzcmJ2amU2YmtmODE3bzJ2N2VpcHZpOHYzNml3MG9iMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/75ZaxapnyMp2w/giphy.gif",
    },
    {
        "id": "gif_mindblown_01",
        "type": "gif",
        "giphy_id": "26ufdipQqU2lhNA4g",
        "description": "Hands to head mind-blown explosion reaction",
        "tags": ["mindblown", "shocked", "tech", "ai", "productivity", "smart", "genius"],
        "mood": "mindblown",
        "source": "giphy",
        "download_url": "https://media2.giphy.com/media/v1.Y2lkPTJkZTk1OTI4czFpcDlkYnhzcmJ2amU2YmtmODE3bzJ2N2VpcHZpOHYzNml3MG9iMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/75ZaxapnyMp2w/giphy.gif",
    },
    {
        "id": "gif_shocked_01",
        "type": "gif",
        "giphy_id": "5VKbvrjxpVJCM",
        "description": "Wide-eyed gasp of disbelief and shock",
        "tags": ["shocked", "surprised", "finance", "money", "disbelief", "omg"],
        "mood": "shocked",
        "source": "giphy",
    },
    {
        "id": "gif_nod_01",
        "type": "gif",
        "giphy_id": "10Jpr9KSaXLchW",
        "description": "Nodding head in total agreement and enthusiastic validation",
        "tags": ["nod", "agree", "yes", "valid", "satisfying", "truth"],
        "mood": "approving",
        "source": "giphy",
    },
    {
        "id": "gif_laugh_01",
        "type": "gif",
        "giphy_id": "BYoRqTmcgzHcL9TCy1",
        "description": "Uncontrollable belly laugh pointing at screen",
        "tags": ["laugh", "funny", "relatable", "humor", "meme"],
        "mood": "joy",
        "source": "giphy",
    },
    {
        "id": "gif_dancing_01",
        "type": "gif",
        "giphy_id": "blSTtZehjAZ8I",
        "description": "Happy carefree shoulder dance celebration",
        "tags": ["dance", "happy", "shopping", "lifestyle", "groove", "fun"],
        "mood": "hyped",
        "source": "giphy",
    },
    {
        "id": "gif_money_01",
        "type": "gif",
        "giphy_id": "3o6gDWzmAzrpi5DQU8",
        "description": "Making it rain dollars cash celebration",
        "tags": ["money", "finance", "cash", "rich", "success", "wealth"],
        "mood": "wealth",
        "source": "giphy",
    },
    {
        "id": "gif_clapping_01",
        "type": "gif",
        "giphy_id": "7rj2ZgttvgomY",
        "description": "Fast enthusiastic round of applause",
        "tags": ["clapping", "applause", "proud", "awesome", "support"],
        "mood": "impressed",
        "source": "giphy",
    },
    {
        "id": "gif_thinking_01",
        "type": "gif",
        "giphy_id": "a5viI92PAF89q",
        "description": "Scratching chin in deep curious contemplation",
        "tags": ["thinking", "confused", "focus", "question", "hmm"],
        "mood": "curious",
        "source": "giphy",
    },
    {
        "id": "gif_delicious_01",
        "type": "gif",
        "giphy_id": "3q3QK6KyDVUBq",
        "description": "Chef's kiss and finger lick delicious reaction",
        "tags": ["food", "delicious", "eating", "satisfying", "chef", "nutrition"],
        "mood": "delighted",
        "source": "giphy",
    },
    {
        "id": "gif_relieved_01",
        "type": "gif",
        "giphy_id": "l0MYt5jPR6QX5pnqM",
        "description": "Huge sigh of relief wiping sweat from brow",
        "tags": ["relieved", "finally", "productivity", "easy", "solved"],
        "mood": "relieved",
        "source": "giphy",
    },
    {
        "id": "gif_running_01",
        "type": "gif",
        "giphy_id": "26u4cqiYI30juCOGY",
        "description": "Fast energetic sprint into action",
        "tags": ["fitness", "fast", "speed", "motivation", "go"],
        "mood": "energetic",
        "source": "giphy",
    },
    {
        "id": "gif_glowup_01",
        "type": "gif",
        "giphy_id": "xUA7aM09ByyR1w5gYG",
        "description": "Radiant smile and confident hair flip",
        "tags": ["beauty", "glow", "reveal", "transformation", "confident"],
        "mood": "confident",
        "source": "giphy",
    },
    {
        "id": "gif_eyes_01",
        "type": "gif",
        "giphy_id": "g01FakEbcUua6yM34a",
        "description": "Quick side-eye peek double take",
        "tags": ["curious", "viral", "look", "attention", "wait"],
        "mood": "suspicious",
        "source": "giphy",
    },

    # --- AUDIO TRACKS (Epidemic Sound Partner Catalog) ---
    {
        "id": "es_slam_dunk",
        "type": "audio",
        "track_id": "4c20406f-6937-49f7-8dcb-39647af926a4",
        "title": "Slam Dunk",
        "artist": "Karl Flykt",
        "description": "Energetic modern upbeat social media anthem with dynamic groove",
        "tags": ["energetic", "modern", "social", "upbeat", "viral", "food", "productivity"],
        "mood": "upbeat",
        "source": "epidemicsound",
        "isPreviewOnly": True,
        "licensing_tier": "PROTOTYPE",
    },
    {
        "id": "es_drive_hype",
        "type": "audio",
        "track_id": "4c20406f-6937-49f7-8dcb-39647af926a4",
        "title": "Drive & Hype",
        "artist": "Epidemic Sound",
        "description": "High-tempo driving motivational workout rhythm",
        "tags": ["fitness", "workout", "hype", "fast", "motivational", "intense"],
        "mood": "motivational",
        "source": "epidemicsound",
        "isPreviewOnly": True,
        "licensing_tier": "PROTOTYPE",
    },
    {
        "id": "es_lofi_aesthetic",
        "type": "audio",
        "track_id": "4c20406f-6937-49f7-8dcb-39647af926a4",
        "title": "Aesthetic Flow",
        "artist": "Epidemic Sound",
        "description": "Warm lofi bounce with smooth aesthetic modern beat",
        "tags": ["chill", "lifestyle", "smooth", "aesthetic", "cozy", "beauty"],
        "mood": "chill",
        "source": "epidemicsound",
        "isPreviewOnly": True,
        "licensing_tier": "PROTOTYPE",
    },
    {
        "id": "es_synth_pulse",
        "type": "audio",
        "track_id": "4c20406f-6937-49f7-8dcb-39647af926a4",
        "title": "Silicon Pulse",
        "artist": "Epidemic Sound",
        "description": "Clean electronic synth groove for software and AI innovation",
        "tags": ["tech", "ai", "electronic", "modern", "cyber", "software"],
        "mood": "electronic",
        "source": "epidemicsound",
        "isPreviewOnly": True,
        "licensing_tier": "PROTOTYPE",
    },
    {
        "id": "es_playful_hook",
        "type": "audio",
        "track_id": "4c20406f-6937-49f7-8dcb-39647af926a4",
        "title": "Smart Moves",
        "artist": "Epidemic Sound",
        "description": "Playful punchy acoustic hook for humorous relatable reels",
        "tags": ["fun", "quirky", "comedy", "relatable", "playful"],
        "mood": "playful",
        "source": "epidemicsound",
        "isPreviewOnly": True,
        "licensing_tier": "PROTOTYPE",
    },
]


import asyncio
import random
from sqlalchemy.orm import Session

DEFAULT_EMOTION_TAGS = {
    "food": ["delicious craving", "mind blown recipe", "jaw drop food", "surprised taste", "satisfied eating"],
    "fitness": ["insane gains", "beast mode hype", "triumph celebration", "shocked transformation", "sweat motivation"],
    "productivity": ["pure relief", "life changing hack", "mind blown focus", "work victory", "total gamechanger"],
    "finance": ["money celebration", "shocked savings", "jaw drop rich", "smart investor", "wealth win"],
    "ai": ["future is now", "mind blown genius", "robot stunned", "automated magic", "insane speed"],
    "technology": ["coding win", "developer celebration", "mind blown software", "speed victory", "tech wizard"],
    "beauty": ["glow up reveal", "stunning transformation", "radiant smile", "jaw drop beauty", "confident vibes"],
    "shopping": ["unboxing excitement", "package arrived hype", "shopping haul dance", "order secured", "retail joy"],
    "lifestyle": ["morning upgrade", "aesthetic vibes", "peaceful relief", "routine victory", "daily happiness"],
}


class AssetService:
    """
    Orchestrates the dynamic retrieval, catalog indexing, and candidate gathering
    from external licensed media APIs (Giphy, Pexels, Epidemic Sound).
    Enforces rolling exclusion (last 20 generations) and rank-weighted candidate sampling.
    """

    def __init__(self):
        self._assets_by_id: Dict[str, Dict[str, Any]] = {a["id"]: a for a in CURATED_ASSETS}

    def register_asset(self, asset: Dict[str, Any]) -> None:
        """Registers a dynamically retrieved asset in the active catalog."""
        if "id" in asset:
            self._assets_by_id[asset["id"]] = asset

    def get_asset_by_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        return self._assets_by_id.get(asset_id)

    def get_recent_excluded_asset_ids(self, db: Session, asset_type: str, limit: int = 20) -> set[str]:
        """
        Retrieves asset IDs used in the last `limit` generations for a given asset type ('gif' or 'audio').
        """
        try:
            from app.models.asset_history import AssetHistory
            records = (
                db.query(AssetHistory.asset_id)
                .filter(AssetHistory.asset_type == asset_type)
                .order_by(AssetHistory.created_at.desc())
                .limit(limit)
                .all()
            )
            return {r[0] for r in records if r[0]}
        except Exception as e:
            logger.warning(f"Failed to fetch excluded asset IDs for {asset_type}: {e}")
            return set()

    def record_used_asset(self, db: Session, asset_type: str, asset_id: str, video_id: Optional[str] = None) -> None:
        """
        Records an asset ID into persistent AssetHistory table to enforce rolling exclusion.
        """
        try:
            from app.models.asset_history import AssetHistory
            record = AssetHistory(
                asset_type=asset_type,
                asset_id=asset_id,
                video_id=video_id,
            )
            db.add(record)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to record used asset {asset_id} ({asset_type}): {e}")

    def _weighted_sample(self, candidates: List[Dict[str, Any]], k: int = 5) -> List[Dict[str, Any]]:
        """
        Rank-weighted sampling without replacement from candidate pool.
        Higher ranked items have higher selection weight, but lower ranked items
        are still regularly chosen to maximize diversity.
        """
        if len(candidates) <= k:
            return list(candidates)

        weights = [1.0 / (i + 1.5) for i in range(len(candidates))]
        pool = list(candidates)
        pool_weights = list(weights)
        chosen = []

        for _ in range(min(k, len(pool))):
            picked = random.choices(pool, weights=pool_weights, k=1)[0]
            idx = pool.index(picked)
            chosen.append(picked)
            pool.pop(idx)
            pool_weights.pop(idx)
        return chosen

    def _filter_and_sample(
        self,
        candidates: List[Dict[str, Any]],
        excluded: set[str],
        id_keys: List[str],
        sample_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Filters out candidates present in the excluded set (checking candidate['id'] and secondary id_keys),
        falling back to the full pool if exclusions leave fewer than 2 candidates.
        Applies rank-weighted sampling to the surviving pool.
        """
        if not candidates:
            return []

        survivors = []
        for c in candidates:
            c_ids = {c.get("id")}
            for k in id_keys:
                if c.get(k):
                    c_ids.add(c.get(k))
            if not (c_ids & excluded):
                survivors.append(c)

        # If exclusions wiped out almost all candidates, keep some from pool
        if len(survivors) < 2 and len(candidates) >= 2:
            logger.info(f"Exclusion filter left {len(survivors)} candidates; recycling candidate pool to maintain variety.")
            survivors = candidates

        return self._weighted_sample(survivors, k=sample_k)

    def fetch_live_candidates(
        self,
        category: str,
        keywords: Optional[List[str]] = None,
        mood: Optional[str] = None,
        emotion_tags: Optional[List[str]] = None,
        excluded_ids: Optional[Dict[str, set[str]]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves real-time candidate assets across all three layers from licensed APIs:
        1. Backgrounds: Pexels portrait stock footage
        2. GIFs: Giphy reaction GIFs
        3. Audios: Epidemic Sound Partner tracks
        Falls back smoothly to curated entries if network API calls fail.
        """
        cat_clean = category.replace("-", " ").replace("_", " ") if category else "lifestyle"
        kw_list = [str(k) for k in (keywords or []) if isinstance(k, (str, int, float))]
        excluded = excluded_ids or {}

        # 1. Pexels Stock Backgrounds
        backgrounds = []
        if pexels_service.is_available:
            try:
                bg_candidates = pexels_service.search_videos(query=f"{cat_clean} portrait", limit=10)
                for bg in bg_candidates:
                    self.register_asset(bg)
                backgrounds = self._filter_and_sample(
                    bg_candidates,
                    excluded.get("background", set()),
                    ["download_url"],
                    sample_k=5,
                )
            except Exception as e:
                logger.warning(f"Pexels live candidate search failed: {e}")

        # 2. Giphy Reaction GIFs (using specific emotion tags)
        gifs = []
        if giphy_service.is_available:
            try:
                tags = emotion_tags or DEFAULT_EMOTION_TAGS.get(cat_clean.lower(), DEFAULT_EMOTION_TAGS["lifestyle"])
                gif_mood = random.choice(tags) if tags else (mood or "excited")
                logger.info(f"Searching Giphy with specific reaction emotion: '{gif_mood}'")
                gif_candidates = giphy_service.search_gifs(query=gif_mood, limit=15)
                if not gif_candidates:
                    gif_candidates = giphy_service.get_trending(limit=15)
                for g in gif_candidates:
                    self.register_asset(g)
                gifs = self._filter_and_sample(
                    gif_candidates,
                    excluded.get("gif", set()),
                    ["giphy_id"],
                    sample_k=5,
                )
            except Exception as e:
                logger.warning(f"Giphy live candidate search failed: {e}")

        # 3. Epidemic Sound Music Tracks (using varied search query)
        audios = []
        if epidemic_service.is_available:
            try:
                audio_query = f"{cat_clean} {' '.join(kw_list[:2])}".strip() or mood or "upbeat groove"
                logger.info(f"Searching Epidemic Sound with query: '{audio_query}'")
                audio_candidates = epidemic_service.search_tracks(query=audio_query, limit=15)
                if not audio_candidates and cat_clean != "upbeat":
                    audio_candidates = epidemic_service.search_tracks(query="upbeat", limit=15)
                for a in audio_candidates:
                    self.register_asset(a)
                audios = self._filter_and_sample(
                    audio_candidates,
                    excluded.get("audio", set()),
                    ["track_id"],
                    sample_k=4,
                )
            except Exception as e:
                logger.warning(f"Epidemic Sound live candidate search failed: {e}")

        # If any layer had 0 results, supplement with curated baseline
        fallback = self.filter_candidates(category, keywords)
        if len(backgrounds) < 2:
            backgrounds.extend([b for b in fallback["backgrounds"] if b not in backgrounds])
        if len(gifs) < 2:
            gifs.extend([g for g in fallback["gifs"] if g not in gifs])
        if len(audios) < 2:
            audios.extend([a for a in fallback["audios"] if a not in audios])

        return {
            "backgrounds": backgrounds[:5],
            "gifs": gifs[:5],
            "audios": audios[:4],
        }

    async def fetch_live_candidates_async(
        self,
        category: str,
        keywords: Optional[List[str]] = None,
        mood: Optional[str] = None,
        emotion_tags: Optional[List[str]] = None,
        excluded_ids: Optional[Dict[str, set[str]]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Asynchronously parallelizes candidate searches across Pexels, Giphy, and Epidemic Sound
        using asyncio.gather, applying rolling exclusion filters and weighted random sampling.
        """
        cat_clean = category.replace("-", " ").replace("_", " ") if category else "lifestyle"
        kw_list = [str(k) for k in (keywords or []) if isinstance(k, (str, int, float))]
        excluded = excluded_ids or {}

        # Prepare queries
        bg_query = f"{cat_clean} portrait"
        tags = emotion_tags or DEFAULT_EMOTION_TAGS.get(cat_clean.lower(), DEFAULT_EMOTION_TAGS["lifestyle"])
        gif_query = random.choice(tags) if tags else (mood or "excited")
        audio_query = f"{cat_clean} {' '.join(kw_list[:2])}".strip() or mood or "upbeat groove"

        logger.info(f"Executing parallel candidate search: bg='{bg_query}', gif='{gif_query}', audio='{audio_query}'")

        # Define thread tasks for parallel execution
        async def search_bg():
            if not pexels_service.is_available:
                return []
            try:
                return await asyncio.to_thread(pexels_service.search_videos, bg_query, 10)
            except Exception as e:
                logger.warning(f"Parallel Pexels search failed: {e}")
                return []

        async def search_gif():
            if not giphy_service.is_available:
                return []
            try:
                res = await asyncio.to_thread(giphy_service.search_gifs, gif_query, 15)
                if not res:
                    res = await asyncio.to_thread(giphy_service.get_trending, 15)
                return res
            except Exception as e:
                logger.warning(f"Parallel Giphy search failed: {e}")
                return []

        async def search_audio():
            if not epidemic_service.is_available:
                return []
            try:
                res = await asyncio.to_thread(epidemic_service.search_tracks, audio_query, 15)
                if not res:
                    res = await asyncio.to_thread(epidemic_service.search_tracks, "upbeat", 15)
                return res
            except Exception as e:
                logger.warning(f"Parallel Epidemic Sound search failed: {e}")
                return []

        # Run all 3 in parallel
        bg_res, gif_res, audio_res = await asyncio.gather(
            search_bg(),
            search_gif(),
            search_audio(),
            return_exceptions=False,
        )

        for bg in bg_res:
            self.register_asset(bg)
        for g in gif_res:
            self.register_asset(g)
        for a in audio_res:
            self.register_asset(a)

        backgrounds = self._filter_and_sample(bg_res, excluded.get("background", set()), ["download_url"], sample_k=5)
        gifs = self._filter_and_sample(gif_res, excluded.get("gif", set()), ["giphy_id"], sample_k=5)
        audios = self._filter_and_sample(audio_res, excluded.get("audio", set()), ["track_id"], sample_k=4)

        # Supplement with fallback catalog if needed
        fallback = self.filter_candidates(category, keywords)
        if len(backgrounds) < 2:
            backgrounds.extend([b for b in fallback["backgrounds"] if b not in backgrounds])
        if len(gifs) < 2:
            gifs.extend([g for g in fallback["gifs"] if g not in gifs])
        if len(audios) < 2:
            audios.extend([a for a in fallback["audios"] if a not in audios])

        return {
            "backgrounds": backgrounds[:5],
            "gifs": gifs[:5],
            "audios": audios[:4],
        }

    def filter_candidates(self, category: str, keywords: Optional[List[Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Deterministic filter over the master catalog based on tag and category scoring.
        """
        cat_lower = category.lower() if category else ""
        query_terms = set(cat_lower.replace("-", " ").replace("_", " ").split())
        if keywords:
            for k in keywords:
                k_str = str(k).lower() if not isinstance(k, str) else k.lower()
                query_terms.update(k_str.split())

        def score_asset(asset: Dict[str, Any]) -> int:
            tags = set(t.lower() for t in asset.get("tags", []))
            desc = asset.get("description", "").lower()
            score = 0
            for term in query_terms:
                if term in tags:
                    score += 5
                if term in desc:
                    score += 2
            return score

        backgrounds = [a for a in CURATED_ASSETS if a["type"] == "background"]
        gifs = [a for a in CURATED_ASSETS if a["type"] == "gif"]
        audios = [a for a in CURATED_ASSETS if a["type"] == "audio"]

        sorted_bgs = sorted(backgrounds, key=score_asset, reverse=True)
        sorted_gifs = sorted(gifs, key=score_asset, reverse=True)
        sorted_audios = sorted(audios, key=score_asset, reverse=True)

        return {
            "backgrounds": sorted_bgs[:5],
            "gifs": sorted_gifs[:5],
            "audios": sorted_audios[:3],
        }


asset_service = AssetService()
