import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProductExtractor:
    """
    Extracts product information from websites using Jina Reader with httpx + BeautifulSoup fallback.
    """

    def __init__(self, jina_api_key: Optional[str] = None):
        self.jina_api_key = jina_api_key or settings.JINA_API_KEY
        self.timeout = 12.0

    async def extract(self, url: str, user_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts product details from URL. Returns a structured dictionary of page context.
        Never raises exceptions; gracefully degrades to fallbacks.
        """
        # Attempt 1: Jina Reader
        try:
            jina_data = await self._extract_jina(url)
            if jina_data and len(jina_data.get("content", "")) > 100:
                return jina_data
        except Exception as e:
            logger.warning(f"Jina Reader extraction failed for {url}: {e}")

        # Attempt 2: Direct HTTP request + BeautifulSoup fallback
        try:
            soup_data = await self._extract_html(url)
            if soup_data and (soup_data.get("title") or soup_data.get("description")):
                return soup_data
        except Exception as e:
            logger.warning(f"HTML fallback extraction failed for {url}: {e}")

        # Attempt 3: Graceful domain and user hint derivation
        return self._extract_heuristic_fallback(url, user_hint)

    async def _extract_jina(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content using Jina Reader API."""
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
            "X-Return-Format": "markdown",
        }
        if self.jina_api_key:
            headers["Authorization"] = f"Bearer {self.jina_api_key}"

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(jina_url, headers=headers)
            if resp.status_code == 200:
                text = resp.text
                title = ""
                # Parse title from markdown title tag or first heading if present
                for line in text.splitlines()[:15]:
                    if line.lower().startswith("title:"):
                        title = line.split(":", 1)[1].strip()
                        break
                    elif line.startswith("# "):
                        title = line.replace("# ", "").strip()
                        break
                
                return {
                    "url": url,
                    "title": title or urlparse(url).netloc,
                    "description": text[:800].strip(),
                    "content": text[:3500].strip(),
                    "extractor": "jina",
                }
        return None

    async def _extract_html(self, url: str) -> Optional[Dict[str, Any]]:
        """Fallback extractor using direct GET and BeautifulSoup."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, verify=False) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()

            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()

            # Gather headings and top paragraphs
            headings = [h.get_text().strip() for h in soup.find_all(["h1", "h2", "h3"])[:6] if h.get_text().strip()]
            paragraphs = [p.get_text().strip() for p in soup.find_all("p")[:8] if len(p.get_text().strip()) > 20]
            
            content_summary = "\n".join(headings + paragraphs)
            return {
                "url": url,
                "title": title or urlparse(url).netloc,
                "description": description or (headings[0] if headings else ""),
                "content": content_summary[:3000].strip(),
                "headings": headings,
                "extractor": "beautifulsoup",
            }

    def _extract_heuristic_fallback(self, url: str, user_hint: Optional[str] = None) -> Dict[str, Any]:
        """Ultimate fallback using URL domain hints and user message text."""
        netloc = urlparse(url).netloc.replace("www.", "")
        domain_name = netloc.split(".")[0].capitalize()
        hint = user_hint or ""
        return {
            "url": url,
            "title": domain_name,
            "description": f"Product at {netloc}. Context: {hint}",
            "content": f"Product Name: {domain_name}\nWebsite: {url}\nUser context: {hint}",
            "extractor": "heuristic_fallback",
        }


product_extractor = ProductExtractor()
