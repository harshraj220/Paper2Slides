from models.qwen_llm import qwen_generate


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
    return qwen_generate(prompt, max_tokens=120)
