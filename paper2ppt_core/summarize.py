import re
import math
from typing import List, Optional
from collections import Counter

def heuristic_bullets(text: str, target: int = 5):
    """
    Backward-compatible wrapper.
    Uses extractive fallback logic only.
    """
    if not text:
        return []

    sents = re.split(r"(?<=[.!?])\s+", text)
    sents = [s.strip() for s in sents if len(s.split()) >= 6]
    return sents[:target]



# ============================
# MODEL LOADER
# ============================
def get_summarizer(model_name: Optional[str]):
    try:
        from transformers import pipeline
        if not model_name or model_name.lower() in ("none", "no", "off"):
            return None
        return pipeline("text2text-generation", model=model_name, truncation=True)
    except Exception:
        return None


# ============================
# EXTRACTIVE SCORING
# ============================
def _score_sentences(text: str):
    sents = re.split(r"(?<=[.!?])\s+", text)
    words = re.findall(r"\w+", text.lower())
    freqs = Counter(words)

    scores = []
    for s in sents:
        w = re.findall(r"\w+", s.lower())
        if not w:
            scores.append((s, 0.0))
            continue
        score = sum(freqs.get(t, 0) for t in w) / math.sqrt(len(w))
        scores.append((s, score))
    return scores


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
    # 1. Extractive fallback
    # ----------------------------
    scored = _score_sentences(text)
    top = sorted(scored, key=lambda x: -x[1])[: max(3, target * 2)]
    chosen = [s for s, _ in top]

    all_sents = re.split(r"(?<=[.!?])\s+", text)
    extractive = [s.strip() for s in all_sents if s in chosen][:target]

    # ----------------------------
    # 2. Model path (if enabled)
    # ----------------------------
    if summarizer_callable:
        prompt = f"""
Create presentation slide bullets.

Rules:
- EXACTLY {target} bullets
- 6–12 words each
- Slide-style (noun phrases preferred)
- No authors, citations, permissions
- No repetition
- One bullet per line
- No numbering or symbols

Text:
{text}
"""
        try:
            out = summarizer_callable(prompt, max_new_tokens=180, truncation=True)
            gen = out[0].get("generated_text") or out[0].get("text") or ""
            parts = [p.strip(" •-\t") for p in gen.split("\n") if p.strip()]

            if parts:
                seen, final = set(), []
                for p in parts:
                    key = re.sub(r"[^a-z0-9 ]", "", p.lower())[:80]
                    if key not in seen:
                        seen.add(key)
                        final.append(p.rstrip("."))
                return final[:target]
        except Exception:
            pass  # fallback safely

    # ----------------------------
    # 3. Final cleaning + slide normalization
    # ----------------------------
    BOILERPLATE = [
        "this paper",
        "we present",
        "we propose",
        "we show",
        "shows",
        "copyright",
        "email",
        "university",
        "google hereby",
    ]

    def de_academic(b: str) -> str:
        b = re.sub(
            r"^(shows|we show|we propose|this paper|our model shows)\s+",
            "",
            b,
            flags=re.I,
        )
        return b

    cleaned = []
    seen = set()

    for b in extractive:
        b = b.strip().rstrip(".")
        low = b.lower()

        if any(p in low for p in BOILERPLATE):
            continue

        b = de_academic(b)
        b = re.sub(r"^\s+", "", b)

        words = b.split()
        if not (4 <= len(words) <= 16):
            continue

        key = re.sub(r"[^a-z0-9 ]", "", low)[:80]
        if key in seen:
            continue
        seen.add(key)

        cleaned.append(b[0].upper() + b[1:])

    return cleaned[:target]
