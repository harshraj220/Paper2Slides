from models.mistral_llm import mistral_generate


def generate_summary(title: str, slide_text: str) -> str:
    prompt = f"""
Summarize the following slide content for internal narration context.

Rules:
- concise
- factual
- no repetition
- no introduction phrases
- max 3 sentences

TITLE:
{title}

CONTENT:
{slide_text}
"""
    return mistral_generate(prompt, max_tokens=120)
