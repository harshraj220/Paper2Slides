# (overwrite file with the enhanced version including previous functions)
# For brevity: full file implementing token protection (as earlier) plus generate_section_summary

import re

BOILERPLATE_PATTERNS = [
    r"provided proper attribution",
    r"this paper",
    r"we propose",
    r"we present",
    r"the authors",
    r"google hereby",
    r"reproduce the tables",
    r"copyright",
    r"email",
    r"university of",
]

def clean_bullet(b: str) -> str:
    b = b.strip()

    # remove leading symbols
    b = re.sub(r"^[•\-\d\.\)\s]+", "", b)

    # drop boilerplate/legal content
    low = b.lower()
    for pat in BOILERPLATE_PATTERNS:
        if pat in low:
            return ""

    # shorten very long bullets
    words = b.split()
    if len(words) > 16:
        b = " ".join(words[:16])

    # normalize capitalization
    b = b[0].upper() + b[1:] if b else ""

    return b

from typing import List, Optional
try:
    from transformers import pipeline
except Exception:
    pipeline = None



def load_paraphraser(model_name: Optional[str] = None):
    if not model_name or model_name.lower() in ("none","no","off"):
        return None
    if pipeline is None:
        print("transformers not available; paraphraser disabled.")
        return None
    try:
        gen = pipeline("text2text-generation", model=model_name, truncation=True)
        return gen
    except Exception as e:
        print("Could not load paraphraser:", e)
        return None

def _protect_tokens(text: str):
    token_map = {}
    idx = 0
    def repl(m):
        nonlocal idx
        k = f"__TOK{idx}__"
        token_map[k] = m.group(0)
        idx += 1
        return k
    pattern = r'([A-Z]{2,}(?:\-[A-Z]{2,})*|\b\d+(?:[.,]\d+)?%?|\bv\d+(?:\.\d+)+\b)'
    prot = re.sub(pattern, repl, text)
    return prot, token_map

def _restore_tokens(text: str, token_map):
    for k, v in token_map.items():
        text = text.replace(k, v)
    return text

def _rule_based_rewrite(bullets: List[str], max_sentences: int = 3) -> str:
    if not bullets:
        return ""
    picks = bullets[:max_sentences]
    sents = []
    for b in picks:
        b = b.strip().rstrip(".")
        if not b:
            continue
        if ":" in b:
            left, right = [p.strip() for p in b.split(":", 1)]
            sent = f"{left} is {right}"
        elif len(b.split()) <= 6:
            sent = "This slide covers " + b
        else:
            sent = b
        if not sent.endswith("."):
            sent += "."
        sents.append(sent[0].upper() + sent[1:])
    return " ".join(sents)

def enhance_for_speech(bullets: List[str], paraphraser=None, max_sentences: int = 3) -> str:
    narration = _rule_based_rewrite(bullets, max_sentences=max_sentences)
    if not narration:
        return ""
    if paraphraser is None:
        return narration
    prot_text, tokmap = _protect_tokens(narration)
    prompt = (
        "Paraphrase the following into a short, natural, 2-3 sentence spoken narration. "
        "Preserve numbers, versions, and ALL-CAPS tokens exactly.\n\n"
        "Text: " + prot_text
    )
    try:
        out = paraphraser(prompt, max_new_tokens=120, truncation=True)
        if out and isinstance(out, list):
            rst = out[0].get("generated_text") or out[0].get("text") or out[0].get("summary_text")
            if rst:
                rst = _restore_tokens(rst, tokmap)
                words = rst.split()
                if len(words) > 70:
                    rst = " ".join(words[:70]) + "..."
                return rst
    except Exception:
        pass
    return narration

def generate_section_summary(section_title: str, section_text: str, summarizer=None) -> dict:
    """
    Create a structured summary of a section. Returns dict:
    {'tldr': str, 'summary': str, 'key_insight': str, 'limitations': str (optional)}
    Uses summarizer (text2text pipeline) if provided, otherwise heuristic fallback.
    """
    out = {'tldr': '', 'summary': '', 'key_insight': '', 'limitations': ''}
    if not section_text or not section_text.strip():
        return out

    # short heuristic TL;DR: first sentence or summary fallback
    sents = re.split(r"(?<=[.!?])\s+", section_text.strip())
    if sents:
        out['tldr'] = sents[0].strip()[:200]

    if summarizer is None:
        # fallback: use first 2-3 sentences as summary and extract a short insight
        out['summary'] = " ".join(sents[:3]).strip()
        out['key_insight'] = sents[0].strip()[:200]
        return out

    # protect numbers
    prot, tokmap = _protect_tokens(section_text)
    prompt = f"""
            You are summarizing a research paper section for slides.

            Section title: {section_title}

            Write the output in the following EXACT format:

            TLDR:
            (one short sentence, max 18 words)

            SUMMARY:
            (2–3 concise sentences, factual, no hype)

            KEY_INSIGHT:
            (one original takeaway, NOT copied text.
            Focus on why this section matters.
            Max 18 words.
            No author names, no citations, no permissions.)


            LIMITATIONS:
            (optional, one sentence if applicable)

            Section text:
            {section_text}
            """

    try:
        gen = summarizer(prompt, max_new_tokens=220, truncation=True)
        if gen and isinstance(gen, list):
            txt = gen[0].get("generated_text") or gen[0].get("text") or gen[0].get("summary_text") or ""
            # restore tokens
            txt = _restore_tokens(txt, tokmap)
            # naive parse: look for lines starting with TLDR:, Summary:, KeyInsight:, Limitations:
            for line in txt.splitlines():
                line = line.strip()
                if not line: continue
                if line.lower().startswith("tldr"):
                    out['tldr'] = line.split(":",1)[1].strip() if ":" in line else line
                elif line.lower().startswith("summary"):
                    out['summary'] += (line.split(":",1)[1].strip() if ":" in line else line) + " "
                elif line.lower().startswith("keyinsight") or line.lower().startswith("key insight"):
                    out['key_insight'] = line.split(":",1)[1].strip() if ":" in line else line
                elif line.lower().startswith("limitations") or line.lower().startswith("limitation"):
                    out['limitations'] = line.split(":",1)[1].strip() if ":" in line else line
            # fallback splits if any fields empty
            if not out['summary']:
                out['summary'] = " ".join(sents[:3]).strip()
            if not out['key_insight']:
                out['key_insight'] = out['tldr']
    except Exception as e:
        # fallback
        out['summary'] = " ".join(sents[:3]).strip()
        out['key_insight'] = out['tldr']
        
    ki = out.get("key_insight", "").strip()

    # drop useless insights
    if any(x in ki.lower() for x in ["provided proper", "this paper", "we present"]):
        ki = ""

    # shorten
    if len(ki.split()) > 18:
        ki = " ".join(ki.split()[:18])

    out["key_insight"] = ki

