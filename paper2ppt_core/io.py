import fitz
import os, re, math
from typing import List, Dict, Tuple

def _save_pixmap_from_xref(doc, xref, outpath):
    """Save image from xref with better error handling"""
    try:
        pix = fitz.Pixmap(doc, xref)
        # Convert CMYK to RGB
        if pix.n >= 5:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        # Skip tiny images (likely artifacts)
        if pix.width < 50 or pix.height < 50:
            pix = None
            return False
        pix.save(outpath)
        pix = None
        return True
    except Exception as e:
        print(f"[WARN] Failed to save xref {xref}: {e}")
        return False

def _is_likely_figure(text: str) -> bool:
    """Check if text looks like a figure caption"""
    text_lower = text.lower()
    # Check for figure keywords
    if re.search(r'\b(fig(?:ure)?|table|diagram|graph|plot|chart)\s*\d', text_lower):
        return True
    # Check for common caption patterns
    if text_lower.startswith(('fig', 'figure', 'table')):
        return True
    return False

def read_pdf_pages(path: str) -> Tuple[List[str], Dict[int, List[Dict]]]:
    """
    Extract text and images from PDF with improved detection.
    
    Returns:
        pages_text: List of text content per page
        pages_images: Dict mapping page_num -> list of {"path": str, "caption": str}
    """
    pages_text: List[str] = []
    pages_images: Dict[int, List[Dict]] = {}
    
    try:
        doc = fitz.open(path)
        page_count = len(doc)
    except Exception as e:
        raise RuntimeError(f"Failed to open PDF: {e}")

    outdir = "./paper2ppt_figs"
    os.makedirs(outdir, exist_ok=True)
    
    print(f"[INFO] Processing {page_count} pages for images and text...")

    for pno in range(page_count):
        page = doc[pno]
        txt = page.get_text()
        pages_text.append(txt)

        # Get structured page content
        try:
            pagedict = page.get_text("dict")
            blocks = pagedict.get("blocks", [])
        except Exception:
            blocks = []

        image_blocks = []
        text_blocks = []
        
        # Collect all blocks with positions
        for b in blocks:
            btype = b.get("type", 0)
            bbox = b.get("bbox", [0, 0, 0, 0])
            
            if btype == 1:  # Image block
                image_blocks.append({"bbox": bbox, "block": b})
            else:  # Text block
                lines_text = ""
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        lines_text += span.get("text", "") + " "
                txt_str = lines_text.strip()
                if txt_str:  # Only keep non-empty text blocks
                    text_blocks.append({"bbox": bbox, "text": txt_str})

        saved = []
        
        # METHOD 1: Try structured image blocks first
        for img_index, ib in enumerate(image_blocks):
            bbox = ib.get("bbox", [0, 0, 0, 0])
            bdict = ib.get("block", {})
            
            # Extract xref from various possible locations
            xref = None
            if isinstance(bdict, dict):
                imginfo = bdict.get("image") or {}
                if isinstance(imginfo, dict):
                    xref = imginfo.get("xref") or imginfo.get("id")
                if xref is None and "xref" in bdict:
                    xref = bdict.get("xref")
            
            outpath = os.path.join(outdir, f"page_{pno+1}_img_{img_index+1}.png")
            saved_ok = False
            
            if xref:
                saved_ok = _save_pixmap_from_xref(doc, xref, outpath)
            
            # If structured method failed, try rendering the bbox
            if not saved_ok and bbox[2] - bbox[0] > 50 and bbox[3] - bbox[1] > 50:
                try:
                    mat = fitz.Matrix(2, 2)  # 2x resolution
                    clip = fitz.Rect(bbox)
                    pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
                    pix.save(outpath)
                    pix = None
                    saved_ok = True
                except Exception as e:
                    print(f"[WARN] Failed to render bbox on page {pno+1}: {e}")
            
            # Find caption below image
            caption = ""
            if saved_ok:
                try:
                    ibottom = bbox[3]
                    candidates = []
                    
                    for t in text_blocks:
                        tbbox = t["bbox"]
                        ttop = tbbox[1]
                        # Look for text blocks below image (within 100 points)
                        if ibottom - 5 <= ttop <= ibottom + 100:
                            dist = ttop - ibottom
                            candidates.append((dist, t["text"]))
                    
                    # Sort by proximity
                    candidates.sort(key=lambda x: x[0])
                    
                    for dist, ttext in candidates[:3]:  # Check top 3 closest
                        if not ttext:
                            continue
                        ttxt = ttext.strip()
                        # Detect likely captions
                        if _is_likely_figure(ttxt) or (len(ttxt) < 200 and len(ttxt.split()) < 35):
                            caption = ttxt.replace("\n", " ").strip()
                            break
                except Exception as e:
                    print(f"[WARN] Caption detection failed: {e}")
            
            if os.path.exists(outpath):
                saved.append({"path": outpath, "caption": caption})
                print(f"[INFO] Page {pno+1}: Saved image {img_index+1} → {outpath}")

        # METHOD 2: Fallback to get_images() if no structured blocks found
        if not saved:
            imgs = page.get_images(full=True)
            print(f"[INFO] Page {pno+1}: Trying fallback extraction ({len(imgs)} images found)")
            
            for idx, info in enumerate(imgs):
                try:
                    xref = info[0]
                    outpath = os.path.join(outdir, f"page_{pno+1}_img_{idx+1}.png")
                    
                    if _save_pixmap_from_xref(doc, xref, outpath):
                        # Try to find nearby caption in text
                        caption = ""
                        page_text_lines = txt.split('\n')
                        for line in page_text_lines:
                            if _is_likely_figure(line):
                                caption = line.strip()
                                break
                        
                        saved.append({"path": outpath, "caption": caption})
                        print(f"[INFO] Page {pno+1}: Fallback saved image {idx+1}")
                except Exception as e:
                    print(f"[WARN] Failed fallback extraction on page {pno+1}, img {idx}: {e}")
                    continue

        pages_images[pno] = saved
        
        if saved:
            print(f"[SUCCESS] Page {pno+1}: {len(saved)} images extracted")

    # Summary
    total_images = sum(len(imgs) for imgs in pages_images.values())
    print(f"\n[SUMMARY] Extracted {total_images} total images from {page_count} pages")

    
    doc.close()  
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