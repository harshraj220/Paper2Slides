import re
from models.qwen_llm import qwen_generate

__all__ = ["generate_narration"]


def generate_narration(title: str, slide_text: str, summary: str) -> str:
    prompt = f"""
You are presenting your own research.
Context: {title}

Slide content:
{slide_text}

Task: Speak 1-2 sentences of high-level intuition about this slide.
Constraints:
- START DIRECTLY with the speech.
- NO timestamps (e.g. 12:00, 00:00).
- NO meta-labels (e.g. "Narration:", "Slide:", "Speaker:").
- NO fillers ("Okay", "So", "Next", "Here we see").
- NO reading the title.

Narration:
""".strip()

    text = qwen_generate(prompt, max_tokens=80).strip()

    # 1. Regex cleaning for timestamps and labels
    # Remove leading timestamps like "12:00 " or "[00:10] "
    text = re.sub(r"^\[?\d{1,2}:\d{2}(:\d{2})?\]?\s*", "", text)
    # Remove leading "Time: ..." or "Narration: ..."
    text = re.sub(r"^(?i)(time|narration|speaker|slide \d+):\s*", "", text)

    # 2. Remove chat fillers
    for prefix in ["Sure", "Okay", "Alright", "Here’s", "Here's", "In this slide", "This slide shows"]:
        if text.startswith(prefix):
            text = text[len(prefix):].lstrip(" ,:-")

    # If model slips into method description, force intuition framing
    if len(text) < 10:
        text = "This key insight drives our approach forward."

    # Enforce max 2 sentences
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    text = ". ".join(sentences[:2])
    if not text.endswith("."):
        text += "."

    return text
