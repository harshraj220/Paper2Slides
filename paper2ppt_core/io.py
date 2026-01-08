import fitz
import os, re, math
from typing import List, Dict

def _save_pixmap_from_xref(doc, xref, outpath):
    try:
        pix = fitz.Pixmap(doc, xref)
        if pix.n >= 5:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        pix.save(outpath)
        pix = None
        return True
    except Exception:
        return False

def read_pdf_pages(path: str):
    """
    Return: (pages_text: List[str], pages_images: Dict[int, List[Dict]])
    pages_images maps page index -> list of dicts: {'path':..., 'caption':...}
    Caption detection uses block bboxes: for each image block, find nearest short text block below it.
    """
    pages_text: List[str] = []
    pages_images: Dict[int, List[Dict]] = {}
    try:
        doc = fitz.open(path)
    except Exception as e:
        raise

    outdir = "./paper2ppt_figs"
    os.makedirs(outdir, exist_ok=True)

    for pno in range(len(doc)):
        page = doc[pno]
        txt = page.get_text()
        pages_text.append(txt)

        # Use page.get_text("dict") to find blocks containing images and text with bbox info
        try:
            pagedict = page.get_text("dict")
            blocks = pagedict.get("blocks", [])
        except Exception:
            blocks = []

        image_blocks = []
        text_blocks = []
        # collect blocks
        for b in blocks:
            btype = b.get("type", 0)
            bbox = b.get("bbox", [0,0,0,0])
            if btype == 1:
                # image block
                image_blocks.append({"bbox": bbox, "block": b})
            else:
                # text block
                lines_text = ""
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        lines_text += span.get("text", "") + " "
                txt_str = lines_text.strip()
                text_blocks.append({"bbox": bbox, "text": txt_str})

        saved = []
        # For each image block, attempt to save its pixmap via xref if available
        img_index = 0
        for ib in image_blocks:
            bbox = ib.get("bbox", [0,0,0,0])
            bdict = ib.get("block", {})
            # xref may be inside bdict.get('image') or in 'xref' (varies)
            xref = None
            if isinstance(bdict, dict):
                imginfo = bdict.get("image") or {}
                if isinstance(imginfo, dict):
                    xref = imginfo.get("xref") or imginfo.get("id")
                # older formats might put 'xref' directly
                if xref is None and "xref" in bdict:
                    xref = bdict.get("xref")
            outpath = os.path.join(outdir, f"page_{pno+1}_img_{img_index+1}.png")
            saved_ok = False
            if xref:
                saved_ok = _save_pixmap_from_xref(doc, xref, outpath)
            # fallback: try extracting via page.get_images list by index
            if not saved_ok:
                try:
                    imgs = page.get_images(full=True)
                    if imgs and img_index < len(imgs):
                        xref2 = imgs[img_index][0]
                        saved_ok = _save_pixmap_from_xref(doc, xref2, outpath)
                except Exception:
                    saved_ok = False
            if not saved_ok:
                # last resort: try rendering the bbox region to an image
                try:
                    mat = fitz.Matrix(2,2)
                    clip = fitz.Rect(bbox)
                    pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
                    pix.save(outpath)
                    pix = None
                    saved_ok = True
                except Exception:
                    saved_ok = False
            # detect caption: nearest short text block below image bbox
            caption = ""
            try:
                ibottom = bbox[3]
                candidates = []
                for t in text_blocks:
                    tbbox = t["bbox"]
                    ttop = tbbox[1]
                    # only consider text blocks below image (ttop > ibottom)
                    if ttop >= ibottom - 1:
                        # vertical distance
                        dist = ttop - ibottom
                        candidates.append((dist, t["text"]))
                # sort by distance and pick first short candidate that looks like a caption
                candidates.sort(key=lambda x: x[0])
                for dist, ttext in candidates:
                    if not ttext:
                        continue
                    ttxt = ttext.strip()
                    # heuristics: contains 'fig' OR short (<250 chars) and not a long paragraph
                    if re.search(r'\b(fig(?:ure)?|caption)\b', ttxt, flags=re.I) or (len(ttxt) < 220 and len(ttxt.split()) < 40):
                        caption = ttxt.replace("\n", " ").strip()
                        break
            except Exception:
                caption = ""
            # add to saved list only if file exists
            if os.path.exists(outpath):
                saved.append({"path": outpath, "caption": caption})
            img_index += 1

        # If we failed to detect image blocks via dict, fallback to previous simple extraction
        if not saved:
            imgs = page.get_images(full=True)
            for idx, info in enumerate(imgs):
                try:
                    xref = info[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n >= 5:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    out = os.path.join(outdir, f"page_{pno+1}_img_{idx+1}.png")
                    pix.save(out); pix = None
                    saved.append({"path": out, "caption": ""})
                except Exception:
                    continue

        pages_images[pno] = saved

    return pages_text, pages_images

def read_text_file(path: str):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        t = f.read()
    return [t], {0: []}

def load_input_paper(path):
    from pathlib import Path
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    ext = p.suffix.lower().lstrip('.')
    if ext == "pdf":
        return read_pdf_pages(str(p))
    else:
        return read_text_file(str(p))
