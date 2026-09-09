import pytest
from app.utils.url_utils import extract_url, is_video_generation_intent


def test_extract_url_standard_http():
    text = "Check this out https://calai.app/features for details"
    assert extract_url(text) == "https://calai.app/features"


def test_extract_url_naked_domain():
    text = "Here's the site: calai.app"
    assert extract_url(text) == "https://calai.app"


def test_extract_url_with_punctuation():
    text = "Visit https://example.com/product, it's great!"
    assert extract_url(text) == "https://example.com/product"


def test_no_url():
    text = "Hello there! How are you doing today?"
    assert extract_url(text) is None


def test_multiple_urls_returns_first():
    text = "Compare https://calai.app and https://myfitnesspal.com"
    assert extract_url(text) == "https://calai.app"
