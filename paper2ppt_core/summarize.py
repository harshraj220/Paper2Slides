import re
from typing import List, Optional

# ============================
# LIGHT HEURISTIC EXTRACTION
# ============================

CLAIM_PATTERNS = [
    r"\bwe (propose|present|introduce|develop)\b",
    r"\bour (method|approach|model)\b",
    r"\bresults (show|demonstrate|indicate)\b",
    r"\boutperform(s|ed)?\b",
    r"\bachieve(s|d)?\b",
    r"\bimprove(s|d)?\b",
]

def extract_claim_sentences(text: str, max_items: int = 8) -> List[str]:
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    selected = []

    for s in sentences:
        s = s.strip()
        if not (10 <= len(s.split()) <= 40):
            continue

        low = s.lower()
        if any(re.search(p, low) for p in CLAIM_PATTERNS):
            selected.append(s)

        if len(selected) >= max_items:
            break

    return selected


# ============================
# MODEL LOADER
# ============================

def get_summarizer(model_name: Optional[str]):
    try:
        from transformers import pipeline
        if not model_name or model_name.lower() in ("none", "off"):
            return None
        return pipeline(
            "text2text-generation",
            model=model_name,
            truncation=True,
            device_map="auto",
        )
    except Exception:
        return None


# ============================
# MAIN SUMMARIZER
# ============================

def summarize_to_bullets(
    text: str,
    summarizer_callable,
    target: int = 5,
) -> List[str]:
    if not text:
        return []

    # ----------------------------
    # 1. Extract claim candidates
    # ----------------------------
    candidates = extract_claim_sentences(text, max_items=target * 2)

    if not candidates:
        # fallback: first reasonable sentences
        sents = re.split(r"(?<=[.!?])\s+", text)
        candidates = [s for s in sents if len(s.split()) >= 8][:target]

    bullets = []

    # ----------------------------
    # 2. Rewrite each bullet using LLM
    # ----------------------------
    if summarizer_callable:
        for s in candidates:
            prompt = f"""
Rewrite the following sentence into ONE presentation slide bullet.

Rules:
- Preserve technical meaning
- Concise but complete
- 10–18 words
- No authors, citations, or narration
- No punctuation at end

Sentence:
{s}
"""
            try:
                out = summarizer_callable(prompt, max_new_tokens=60)
                gen = out[0].get("generated_text") or out[0].get("text") or ""
                bullet = gen.strip().split("\n")[0].strip("•- ").rstrip(".")
                if bullet:
                    bullets.append(bullet)
            except Exception:
                bullets.append(s)

            if len(bullets) >= target:
                break

    else:
        bullets = candidates[:target]

    # ----------------------------
    # 3. Final cleanup
    # ----------------------------
    final = []
    seen = set()

    for b in bullets:
        b = re.sub(
            r"^(this paper|we propose|we present|our method shows)\s+",
            "",
            b,
            flags=re.I,
        )
        b = b.strip()
        if not (6 <= len(b.split()) <= 20):
            continue

        key = re.sub(r"[^a-z0-9 ]", "", b.lower())[:80]
        if key in seen:
            continue
        seen.add(key)

        final.append(b[0].upper() + b[1:])

    return final[:target]
