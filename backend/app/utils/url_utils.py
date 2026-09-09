import re
from typing import Optional, Tuple
from urllib.parse import urlparse

# Regular expression to match URLs with or without scheme
# Matches e.g., https://calai.app, http://example.com/page, calai.app, my-product.io/features
URL_REGEX = re.compile(
    r'(?:https?:\/\/)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:\/[^\s]*)?',
    re.IGNORECASE
)

# Explicit video generation triggers
VIDEO_TRIGGERS = [
    "building", "build", "app", "site", "here's the site", "here is the site",
    "video", "ugc", "generate", "create", "make", "ad", "tiktok", "reel",
    "product", "check out", "launching", "startup", "my tool", "my project",
    "calai", "website"
]

# Non-video queries (pure inquiry / conversational questions about a site without wanting video generation)
NON_VIDEO_QUERY_PATTERNS = [
    r"^(?:tell me about|what is|summarize|explain)\s+(?:this\s+)?(?:website|site|url|link)\s*[:\s]*https?:\/\/",
]


def extract_url(text: str) -> Optional[str]:
    """
    Extracts the first valid URL from a message text.
    Normalizes it with https:// if no protocol is given.
    """
    if not text:
        return None
    
    matches = URL_REGEX.findall(text)
    for match in matches:
        clean = match.strip().rstrip(".,!?;:)\"'")
        # Ensure it has a valid TLD and isn't just an abbreviation
        if "." in clean:
            parts = clean.split(".")
            tld = parts[-1].split("/")[0]
            # Common file extensions or short non-TLDs to ignore
            if len(tld) >= 2 and not tld.isdigit():
                if not clean.startswith(("http://", "https://")):
                    clean = f"https://{clean}"
                try:
                    parsed = urlparse(clean)
                    if parsed.netloc and "." in parsed.netloc:
                        return clean
                except Exception:
                    continue
    return None


def is_video_generation_intent(message: str) -> Tuple[bool, Optional[str]]:
    """
    Determines whether a message is requesting video generation or normal conversation.
    Returns (is_generation, detected_url).
    """
    url = extract_url(message)
    if not url:
        return False, None
    
    clean_msg = message.strip().lower()
    
    # Check for negative conversational queries about a URL (e.g., 'Tell me about this website https://...')
    for pattern in NON_VIDEO_QUERY_PATTERNS:
        if re.search(pattern, clean_msg, re.IGNORECASE):
            # If user explicitly asked for video in the same message, allow it
            if any(term in clean_msg for term in ["video", "ugc", "generate", "create a video", "make a video"]):
                return True, url
            return False, url

    # If the user posted a URL along with any product context or creation verbs:
    # "I'm building CalAI, a calorie-tracking app. Here's the site: calai.app"
    # "Create a UGC video for https://example.com"
    # Or simply pasted a URL with context
    words = set(re.findall(r'\b[a-zA-Z]+\b', clean_msg))
    if any(trigger in clean_msg for trigger in VIDEO_TRIGGERS):
        return True, url
    
    # If the message is just a URL or contains a URL with product cues, default to generating video
    # since pasting a product URL is the core action
    return True, url
