from paper2ppt_core.summarize import get_summarizer, summarize_to_bullets, heuristic_bullets

def test_heuristic_bullets_nonempty():
    text = "This paper proposes a new method. We evaluate on dataset X. Our contributions include A, B, and C."
    bullets = heuristic_bullets(text, target=3)
    assert isinstance(bullets, list)
    assert len(bullets) >= 1

def test_summarize_to_bullets_none_model():
    summarizer = get_summarizer(None)  # should be None
    text = "Short text for summarization testing. Contains multiple sentences. Should return bullets."
    bullets = summarize_to_bullets(text, summarizer, target=3)
    assert isinstance(bullets, list)
    assert len(bullets) >= 1
