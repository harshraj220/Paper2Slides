from models.qwen_llm import qwen_generate

__all__ = ["generate_narration"]


def generate_narration(title: str, slide_text: str, summary: str) -> str:
    prompt = f"""
You are presenting your own research to a live audience.

Slide title:
{title}

The slide already shows technical bullet points.
Do NOT explain or restate them.

Your narration should:
- Sound like spoken commentary, not a paper
- Focus on intuition or high-level takeaway
- Be concise and conversational
- Be concise and conversational
- Use AT MOST 2 sentences

Slide bullets (context only, do not repeat):
{slide_text}
""".strip()

    text = qwen_generate(prompt, max_tokens=80).strip()

    # Remove chat fillers
    for prefix in ["Sure", "Okay", "Alright", "Here’s", "Here's"]:
        if text.startswith(prefix):
            text = text[len(prefix):].lstrip()

    # If model slips into method description, force intuition framing
    # (Optional) Check for very generic failures, but do not replace with hardcoded paper text.
    if len(text) < 10:
        text = "This slide outlines the key points shown here."

    # Enforce max 2 sentences
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    text = ". ".join(sentences[:2])
    if not text.endswith("."):
        text += "."

    return text
