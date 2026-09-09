import json
import logging
from typing import Dict, Any, List, Optional
from groq import Groq
from app.core.config import settings
from app.schemas.creative import CreativePlan

logger = logging.getLogger(__name__)


class GroqService:
    """
    Isolated Groq AI service for:
    1. Product understanding (extracting name, category, benefits, audience)
    2. Creative direction (selecting concept, candidate asset IDs, hook text)
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self._client: Optional[Groq] = None
        if self.api_key:
            try:
                self._client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def understand_product(self, raw_content: str, user_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Sends extracted page content and user message to Groq.
        Returns structured product understanding JSON.
        """
        if not self.is_available:
            return None

        prompt = f"""
You are an expert product analyst and marketing strategist. Analyze the website content and user message below.
Extract accurate product facts. Do NOT invent unsupported claims. Only use information directly supported by the text.

User message / context:
{user_hint or "None"}

Extracted website content:
{raw_content[:3000]}

Respond ONLY with valid JSON matching this schema:
{{
  "name": "Product name",
  "category": "Category such as food, fitness, productivity, finance, tech, ai, shopping, lifestyle",
  "description": "Clear 1-2 sentence description of what the product does",
  "target_audience": "Specific audience who benefits most",
  "key_benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
  "marketing_angles": ["Angle 1", "Angle 2", "Angle 3"],
  "emotion_tags": ["3 to 5 specific, vivid reaction emotion phrases like 'jaw drop', 'shocked realization', 'pure relief', 'mind blown', 'hyped celebration' - NOT generic words"]
}}
"""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise product analyst. Output strictly valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            # Basic validation
            if "name" in data and "category" in data:
                return data
        except Exception as e:
            logger.error(f"Groq product understanding failed: {e}")
        return None

    def select_creative_plan(
        self,
        product_info: Dict[str, Any],
        candidate_backgrounds: List[Dict[str, Any]],
        candidate_gifs: List[Dict[str, Any]],
        candidate_audios: List[Dict[str, Any]],
    ) -> Optional[CreativePlan]:
        """
        Groq acts as the Creative Director.
        Given candidate assets filtered for the product, Groq selects the best combination,
        a short punchy hook text, and the reaction GIF timing/scale.
        """
        if not self.is_available:
            return None

        bg_list = [{"id": a["id"], "description": a["description"], "tags": a.get("tags", [])} for a in candidate_backgrounds]
        gif_list = [{"id": a["id"], "description": a["description"], "mood": a.get("mood", ""), "tags": a.get("tags", [])} for a in candidate_gifs]
        audio_list = [{"id": a["id"], "description": a["description"], "tags": a.get("tags", [])} for a in candidate_audios]

        valid_bg_ids = {a["id"] for a in candidate_backgrounds}
        valid_gif_ids = {a["id"] for a in candidate_gifs}
        valid_audio_ids = {a["id"] for a in candidate_audios}

        prompt = f"""
You are an expert AI assembly and organization system for short-form UGC video ads (TikTok, Instagram Reels).
Your job is NOT to generate pixels, video frames, or audio waveforms.
Your role is to:
1. Select and rank the best combination of pre-existing licensed assets (background footage, reaction GIF, and music track) from the provided candidate pools to match the trend/topic.
2. Generate the single generative component: a high-converting, punchy 1-line hook text copy.

Product Details:
Product Name: {product_info.get('name')}
Category: {product_info.get('category')}
Description: {product_info.get('description')}
Marketing Angles: {', '.join(product_info.get('marketing_angles', []))}

Candidate Licensed Assets Pool (You MUST pick from these IDs only):

1. Available Backgrounds (Pexels Stock Video):
{json.dumps(bg_list, indent=2)}

2. Available Reaction GIFs (Giphy Hero Visual):
{json.dumps(gif_list, indent=2)}

3. Available Music Tracks (Epidemic Sound):
{json.dumps(audio_list, indent=2)}

Assembly Specifications:
- text_overlay: The only generative piece! Create a punchy, viral 1-line POV or relatable hook (e.g., 'POV: you finally know what you're eating', 'Why did nobody tell me about this?'). Under 45 characters.
- gif_position: Must be 'top' (top-third, directly under the hook text) or 'webcam' (corner bubble). Do NOT use dead-center as it conflicts with platform UI.
- gif_scale: Hero element: choose between 0.65 and 0.75 (65-75% of canvas width).
- duration: Exactly 7 seconds.

Return strictly JSON matching this structure:
{{
  "concept": "POV: finally making calorie tracking easy",
  "duration": 7,
  "background_asset_id": "exact_id_from_available_backgrounds",
  "gif_asset_id": "exact_id_from_available_gifs",
  "audio_asset_id": "exact_id_from_available_audios",
  "text_overlay": "POV: you finally know what you're eating",
  "text_style": "bold_stroke_shadow",
  "gif_position": "top",
  "gif_scale": 0.70
}}
"""
        for attempt in range(2):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an AI assembly and organization curator. "
                                "You select and rank pre-existing licensed assets per layer and generate high-converting hook copy. "
                                "Output strictly valid JSON selecting exclusively from the provided candidate asset IDs."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                )
                data = json.loads(response.choices[0].message.content)
                bg_id = data.get("background_asset_id")
                gif_id = data.get("gif_asset_id")
                audio_id = data.get("audio_asset_id")

                # Validate asset IDs strictly against available candidates
                if bg_id in valid_bg_ids and gif_id in valid_gif_ids and audio_id in valid_audio_ids:
                    return CreativePlan(**data)
                else:
                    logger.warning(f"Groq returned invalid asset IDs on attempt {attempt+1}: bg={bg_id}, gif={gif_id}, audio={audio_id}")
            except Exception as e:
                logger.error(f"Groq creative plan generation failed on attempt {attempt+1}: {e}")

        return None

    def generate_conversational_response(self, user_message: str) -> str:
        """Generates a friendly conversational chat response when no video is requested."""
        if not self.is_available:
            return self._fallback_chat_response(user_message)

        prompt = f"""
The user said: "{user_message}"
You are the AI assistant for a UGC Video Generator application.
You can:
- Generate short 5-10 second vertical UGC-style videos from product URLs (e.g. "I'm building CalAI, here's the site: calai.app").
- Understand product websites, select fitting background footage, viral reaction GIFs, upbeat music, and hook text.

Respond conversationally, warmly, and concisely (1-2 sentences). If they greet you, greet them back. If they ask what you do, explain how you turn product links into ready-to-use UGC videos.
"""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful, concise assistant for UGC Video Generator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=150,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Groq conversational chat failed: {e}")
            return self._fallback_chat_response(user_message)

    def _fallback_chat_response(self, user_message: str) -> str:
        clean = user_message.strip().lower()
        if any(w in clean for w in ["hi", "hello", "hey"]):
            return "Hey there! 👋 I can turn any product website or link into a short UGC-style video with background footage, reaction GIFs, and audio. Paste a product URL to try it!"
        if "what can you do" in clean or "help" in clean:
            return "I create ready-to-post UGC vertical videos from product websites! Simply send me a product URL (for example: 'I'm building CalAI, here's the site: calai.app') and I'll assemble the creative for you."
        return "I'm here to help create UGC videos for your products! Send me a product name and website URL to generate your video."


groq_service = GroqService()
