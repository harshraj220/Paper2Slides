#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore")

import argparse
import math
import os
import re
from pathlib import Path
from typing import List, Dict

from paper2ppt_core.io import load_input_paper
from paper2ppt_core.sections import split_into_sections
from paper2ppt_core.summarize import get_summarizer, summarize_to_bullets
from paper2ppt_core.pptx_builder import build_presentation, MAX_FIGURES_PER_SLIDE

# ==============================
# PERFORMANCE SAFETY CONSTANTS
# ==============================
MAX_MODEL_CHARS = 1800
MODEL_CUTOFF_CHARS = 1200

SKIP_SECTIONS = {
    "references",
    "acknowledgements",
    "acknowledgments",
    "appendix",
    "supplementary",
}

# ==============================
# HELPERS
# ==============================
def clean_title(t: str) -> str:
    if len(t.split()) > 8:
        return "Key Results" if "result" in t.lower() else "Method Overview"
    return t


def score_image(path: str, slide_title: str) -> int:
    name = os.path.basename(path).lower()
    title = slide_title.lower()
    score = 0

    if any(k in name for k in ["arch", "architecture", "model", "diagram", "network"]):
        score += 50
    if any(k in name for k in ["plot", "graph", "curve", "bleu", "accuracy"]):
        score += 40
    if "table" in name:
        score -= 30

    if "model" in title and "model" in name:
        score += 20
    if "result" in title and "plot" in name:
        score += 20

    return score


def select_best_images(images: List[str], title: str, max_images: int = 1):
    return sorted(images, key=lambda p: score_image(p, title), reverse=True)[:max_images]


def should_use_images(title: str, bullets: List[str]) -> bool:
    t = title.lower()
    if any(k in t for k in ["model", "architecture", "result", "experiment"]):
        return True
    return False


def generate_image_caption(image_path: str, slide_title: str) -> str:
    name = os.path.basename(image_path).lower()
    name = re.sub(r"(figure|fig\.?|table)\s*\d+", "", name)

    if any(k in name for k in ["arch", "architecture", "model"]):
        return "Transformer model architecture"
    if any(k in name for k in ["plot", "graph", "bleu", "accuracy"]):
        return "Experimental results on translation benchmarks"

    return f"Illustration related to {slide_title.lower()}"


def align_bullets_with_images(bullets: List[str]) -> List[str]:
    return [
        re.sub(r"(table|figure)\s*\d+", "", b, flags=re.I).strip()
        for b in bullets
    ]


def remove_dangling_refs(bullets: List[str]) -> List[str]:
    cleaned = []
    for b in bullets:
        if re.search(r"(listed in|shown in|given in)\b", b, re.I):
            continue
        cleaned.append(b)
    return cleaned



def drop_table_garbage(bullets: List[str]) -> List[str]:
    clean = []
    for b in bullets:
        if sum(c.isdigit() for c in b) > 6:
            continue
        if len(b.split()) > 25:
            continue
        clean.append(b)
    return clean


def inject_visual_bullet(title: str) -> List[str]:
    t = title.lower()
    if "model" in t:
        return ["Transformer encoder–decoder architecture with self-attention"]
    if "result" in t:
        return ["Performance comparison across translation benchmarks"]
    return []


# ==============================
# SLIDE PLANNING
# ==============================
def plan_slides_for_section(
    title: str,
    bullets: List[str],
    images: List[Dict],
    bullets_per_slide: int,
    max_figs: int,
):
    bullets = bullets or []
    images = images or []

    num_b = max(1, math.ceil(len(bullets) / bullets_per_slide)) if bullets else 1
    num_i = max(1, math.ceil(len(images) / max_figs)) if images else 1
    slide_count = max(num_b, num_i)

    slides = []
    for i in range(slide_count):
        slides.append({
            "title": title if i == 0 else f"{title} (cont.)",
            "bullets": bullets[i * bullets_per_slide:(i + 1) * bullets_per_slide],
            "images": images[i * max_figs:(i + 1) * max_figs],
        })
    return slides


# ==============================
# MAIN
# ==============================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True)
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--model", default="t5-base")
    ap.add_argument("--max-bullets", type=int, default=6)
    args = ap.parse_args()

    pages_text, pages_images = load_input_paper(args.input)
    sections = split_into_sections(pages_text)
    summarizer = get_summarizer(args.model)

    slides_plan = []

    # merge extracted figures
    for d in ["/Users/harsh/paper2ppt/paper2ppt_figs", "/tmp/paper2ppt_figs"]:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.lower().endswith((".png", ".jpg", ".jpeg")):
                pages_images.setdefault(0, []).append(
                    os.path.join(d, fn)
                )



    for sec in sections:
        raw_title = sec.get("raw_title") or sec.get("title") or "Section"
        title = clean_title(raw_title)

        if any(k in title.lower() for k in SKIP_SECTIONS):
            continue

        text = sec.get("text", "")
        text = re.sub(r"\S+@\S+", "", text)
        text = text[:MAX_MODEL_CHARS]

        summarizer_use = summarizer if len(text) <= MODEL_CUTOFF_CHARS else None
        bullets = summarize_to_bullets(text, summarizer_use, target=args.max_bullets)

        # ---- dedupe + length ----
        clean = []
        seen = set()
        for b in bullets:
            key = re.sub(r"[^a-z0-9 ]", "", b.lower())[:80]
            if key in seen:
                continue
            if not (3 <= len(b.split()) <= 25):
                continue
            seen.add(key)
            clean.append(b.strip())

        bullets = clean
        bullets = align_bullets_with_images(bullets)
        bullets = remove_dangling_refs(bullets)
        bullets = drop_table_garbage(bullets)

        images = []
        if should_use_images(title, bullets):
            raw_imgs = []
            for p in sec.get("pages", []):
                raw_imgs.extend(pages_images.get(p, []))

            # 🔑 FALLBACK: if no page-matched images, use any available
            if not raw_imgs:
                raw_imgs = pages_images.get(0, [])

            images = [
                {"path": img, "caption": generate_image_caption(img, title)}
                for img in select_best_images(raw_imgs, title)
            ]

        if not bullets and images:
            bullets = inject_visual_bullet(title)

        if not bullets and not images:
            continue

        slides_plan.extend(
            plan_slides_for_section(
                title.title(),
                bullets,
                images,
                args.max_bullets,
                MAX_FIGURES_PER_SLIDE,
            )
        )

    doc_title = pages_text[0].split("\n")[0] if pages_text else Path(args.input).stem
    out = build_presentation(slides_plan, args.output, doc_title, sections)
    print("Saved:", out)
    print("Summarized slides created.")



if __name__ == "__main__":
    main()
