from ollama_client import ollama_generate

def generate_summary(slide_title, original_text):
    prompt = f"""
Generate a presentation slide summary.

STRICT RULES:
- Use ONLY exact facts stated in the slide content
- Do NOT comment on missing information
- Do NOT infer or explain
- Use at most 3 bullets
- Each bullet must be one short factual sentence
- Use hyphen bullets only ("- ")

Slide Content:
{original_text}

Write ONLY the bullet points.
"""

    raw = ollama_generate(prompt)

    bullets = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("-", "•")):
            clean = line.lstrip("-• ").strip()
            bullets.append(f"- {clean}")
        if len(bullets) == 3:
            break

    # Fallback if model returns nothing
    if not bullets and original_text.strip():
        first_sentence = original_text.strip().split(".")[0]
        bullets.append(f"- {first_sentence.strip()}.")

    return "\n".join(bullets)
