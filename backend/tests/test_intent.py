from app.utils.url_utils import is_video_generation_intent


def test_conversational_greeting_intent():
    intent, url = is_video_generation_intent("hi")
    assert intent is False
    assert url is None


def test_conversational_question_intent():
    intent, url = is_video_generation_intent("what can you do?")
    assert intent is False
    assert url is None


def test_product_demo_prompt_intent():
    prompt = "I'm building CalAI, a calorie-tracking app. Here's the site: calai.app"
    intent, url = is_video_generation_intent(prompt)
    assert intent is True
    assert url == "https://calai.app"


def test_explicit_video_creation_intent():
    prompt = "Create a UGC video for https://notion.so"
    intent, url = is_video_generation_intent(prompt)
    assert intent is True
    assert url == "https://notion.so"


def test_inquiry_about_website_intent():
    prompt = "Tell me about this website https://example.com"
    intent, url = is_video_generation_intent(prompt)
    assert intent is False
    assert url == "https://example.com"
