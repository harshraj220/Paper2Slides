from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from PIL import Image, ImageOps, ImageChops
from io import BytesIO
import json, os

# =========================
# THEME & CONSTANTS
# =========================

DEFAULT_THEME = {
    "title_font": "Calibri",
    "body_font": "Calibri",
    "title_size_pt": 36,
    "body_size_pt": 18,
    "accent_color": [18, 90, 173],
    "background_color": [255, 255, 255],
    "panel_bg": [20, 20, 20],
    "text_color": [245, 245, 245],
    "subtext_color": [200, 200, 200],
    "panel_transparency": 0.30,
    "image_frame": "none"
}

THEME_DIR = Path(__file__).resolve().parent.parent / "paper2ppt" / "themes"
if not THEME_DIR.exists():
    THEME_DIR = Path(__file__).resolve().parent / "themes"

MAX_FIGURES_PER_SLIDE = 2
MAX_VISIBLE_BULLETS = 5

# =========================
# UTILS
# =========================

def load_theme(theme_name: str):
    try:
        if not theme_name:
            return DEFAULT_THEME
        path = Path(theme_name)
        if path.exists():
            return {**DEFAULT_THEME, **json.loads(path.read_text())}
        tfile = THEME_DIR / f"{theme_name}.json"
        if tfile.exists():
            return {**DEFAULT_THEME, **json.loads(tfile.read_text())}
    except Exception:
        pass
    return DEFAULT_THEME


def rgb(t):
    return RGBColor(int(t[0]), int(t[1]), int(t[2]))


def _draw_footer(slide, prs, theme, text=None):
    try:
        footer = slide.shapes.add_textbox(
            Inches(0.4),
            prs.slide_height - Inches(0.5),
            prs.slide_width - Inches(0.8),
            Inches(0.4),
        )
        tf = footer.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = text or f"Auto-generated • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        p.font.size = Pt(9)
        p.font.color.rgb = rgb(theme["subtext_color"])
        p.alignment = PP_ALIGN.CENTER
    except Exception:
        pass


# =========================
# IMAGE HELPERS
# =========================

def crop_image_whitespace(path: str) -> BytesIO:
    try:
        img = Image.open(path).convert("RGB")
        bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        cropped = img.crop(bbox) if bbox else img
        bio = BytesIO()
        cropped.save(bio, format="PNG")
        bio.seek(0)
        return bio
    except Exception:
        bio = BytesIO()
        Image.open(path).convert("RGB").save(bio, format="PNG")
        bio.seek(0)
        return bio


def thumb_fit_bytesio(bio, target_w_px: int, target_h_px: int) -> BytesIO:
    bio.seek(0)
    img = Image.open(bio).convert("RGB")
    img = ImageOps.contain(img, (target_w_px, target_h_px))
    out = BytesIO()
    img.save(out, format="PNG")
    out.seek(0)
    return out


# =========================
# SLIDE BUILDERS
# =========================

def add_text_panel(slide, prs, theme, full_width: bool):
    left, top = Inches(0.6), Inches(1.0)
    width = prs.slide_width - (Inches(1.2) if full_width else Inches(4.0))
    height = prs.slide_height - Inches(2.2)
    tb = slide.shapes.add_textbox(left, top, width, height)

    try:
        fill = tb.fill
        fill.solid()
        fill.fore_color.rgb = rgb(theme["panel_bg"])
        fill.fore_color.transparency = float(theme.get("panel_transparency", 0.25))
    except Exception:
        pass

    return tb


def add_images_right(slide, prs, image_items: List[Dict], theme):
    if not image_items:
        return

    col_w, col_h = Inches(3.2), Inches(2.6)
    gap = Inches(0.28)
    left = prs.slide_width - col_w - Inches(0.6)
    top = Inches(1.2)

    px_w = int(col_w.inches * 96)
    px_h = int(col_h.inches * 96)

    for idx, item in enumerate(image_items[:MAX_FIGURES_PER_SLIDE]):
        try:
            pth = item["path"] if isinstance(item, dict) else str(item)
            caption = item.get("caption", "") if isinstance(item, dict) else ""
            bio = thumb_fit_bytesio(crop_image_whitespace(pth), px_w, px_h)
            slide.shapes.add_picture(
                bio, left, top + idx * (col_h + gap), col_w, col_h
            )
            if caption:
                cap = slide.shapes.add_textbox(
                    left, top + idx * (col_h + gap) + col_h + Inches(0.04),
                    col_w, Inches(0.6)
                )
                ctf = cap.text_frame
                ctf.clear()
                cp = ctf.paragraphs[0]
                cp.text = caption[:220]
                cp.font.size = Pt(10)
                cp.font.italic = True
                cp.font.color.rgb = rgb(theme["subtext_color"])
                cp.alignment = PP_ALIGN.CENTER
        except Exception:
            continue


# =========================
# MAIN BUILDER
# =========================

def build_presentation(slides_plan, output_path: str, doc_title: str, sections, theme_name="academic"):
    theme = load_theme(theme_name)
    prs = Presentation()
    blank = prs.slide_layouts[6]

    for s in slides_plan:
        slide = prs.slides.add_slide(blank)
        has_images = bool(s.get("images"))

        panel = add_text_panel(slide, prs, theme, full_width=not has_images)
        tf = panel.text_frame
        tf.clear()
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

        # Title
        title = tf.paragraphs[0]
        title.text = s.get("title", "")[:120]
        title.font.bold = True
        title.font.size = Pt(theme["title_size_pt"])
        title.font.color.rgb = rgb(theme["text_color"])
        title.space_after = Pt(10)

        # Key Insight
        if s.get("insight"):
            pi = tf.add_paragraph()
            pi.text = "Key insight: " + s["insight"]
            pi.font.italic = True
            pi.font.size = Pt(12)
            pi.font.color.rgb = rgb(theme["subtext_color"])
            pi.space_after = Pt(8)

        # Bullets
        for b in s.get("bullets", [])[:MAX_VISIBLE_BULLETS]:
            if not b:
                continue
            pb = tf.add_paragraph()
            pb.text = "• " + b
            pb.level = 1
            pb.font.size = Pt(theme["body_size_pt"])
            pb.font.color.rgb = rgb(theme["text_color"])
            pb.space_before = Pt(2)
            pb.space_after = Pt(6)

        if has_images:
            add_images_right(slide, prs, s["images"], theme)

        try:
            notes = slide.notes_slide.notes_text_frame
            notes.clear()
            if s.get("tldr"):
                notes.text = "TL;DR: " + s["tldr"]
        except Exception:
            pass

        _draw_footer(slide, prs, theme)

    prs.save(output_path)
    return output_path
