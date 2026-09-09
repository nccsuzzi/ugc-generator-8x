import pytest
from app.services.product_extractor import ProductExtractor


@pytest.mark.asyncio
async def test_extractor_fallback_when_unreachable():
    extractor = ProductExtractor()
    # When given a fake URL that cannot resolve, it should gracefully fall back to heuristic domain data
    result = await extractor.extract("https://this-domain-definitely-does-not-exist-1234567.com", "My test app")
    assert result is not None
    assert "url" in result
    assert result["url"] == "https://this-domain-definitely-does-not-exist-1234567.com"
    assert "extractor" in result
    assert result["extractor"] == "heuristic_fallback"
    assert "This-domain-definitely-does-not-exist-1234567" in result["title"]
