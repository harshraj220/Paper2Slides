import fitz
import os, re, math, shutil
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

# ==========================================
# NEW: TABLE & VECTOR GRAPHICS ENABLED
# ==========================================

def extract_tables_from_page(page, pno: int, outdir: str) -> Tuple[List[Dict], str]:
    """
    Finds tables, saves them as images, and returns their Markdown text.
    """
    found_images = []
    page_markdown_extras = ""
    
    try:
        tables = page.find_tables()
        if tables.tables:
            print(f"[INFO] Page {pno+1}: Found {len(tables.tables)} tables")
            
        for i, tab in enumerate(tables.tables):
            # 1. Save Image
            bbox = tab.bbox
            # Add small padding
            padded_box = fitz.Rect(bbox[0]-5, bbox[1]-5, bbox[2]+5, bbox[3]+5)
            
            outpath = os.path.join(outdir, f"page_{pno+1}_table_{i+1}.png")
            try:
                # High-res render of table area
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat, clip=padded_box, alpha=False)
                pix.save(outpath)
                found_images.append({
                    "path": outpath, 
                    "caption": f"Table {i+1} from Page {pno+1}"
                })
            except Exception as e:
                print(f"[WARN] Failed to render table {i+1} on page {pno+1}: {e}")

            # 2. Extract Markdown Content
            # This helps the LLM understand the data
            try:
                md = tab.to_markdown()
                if md:
                    page_markdown_extras += f"\n\n[TABLE DATA EXTRACTED FROM PAGE {pno+1}]\n{md}\n[END TABLE DATA]\n"
            except:
                pass
                
    except Exception as e:
        print(f"[WARN] Table extraction failed page {pno+1}: {e}")
        
    return found_images, page_markdown_extras

def extract_vector_graphics_from_page(page, pno: int, outdir: str) -> List[Dict]:
    """
    Detects clusters of vector paths (drawings) to find graphs/charts that are not images.
    """
    found_images = []
    try:
        paths = page.get_drawings()
        if not paths:
            return []
            
        # Cluster rectangles
        # We look for clusters of drawing commands that form a "box" larger than a typical icon
        
        # Heuristic: Merge intersecting or close bounding boxes
        rects = [p["rect"] for p in paths]
        if not rects:
            return []
            
        # Naive clustering: 
        # 1. Filter out tiny paths (likely bullet points or text underlines)
        valid_rects = [r for r in rects if r.width > 10 and r.height > 10]
        
        # 2. Merge overlapping
        merged = []
        for r in valid_rects:
            consumed = False
            for i, m in enumerate(merged):
                # Check intersection or close proximity (within 20pts)
                expanded_m = fitz.Rect(m[0]-20, m[1]-20, m[2]+20, m[3]+20)
                if r.intersects(expanded_m):
                    # Merge
                    merged[i] = m | r # Union
                    consumed = True
                    break
            if not consumed:
                merged.append(r)
                
        # 3. Filter final boxes -> Must be "Chart sized"
        chart_rects = [r for r in merged if r.width > 100 and r.height > 80]
        
        for i, rect in enumerate(chart_rects):
            # Check if this region is ALREADY covered by a standard image
            # We don't want duplicates
            is_duplicate = False
            # (Note: we don't have access to already extracted images here easily without passing them in.
            #  For now, we save them. Deduplication can happen based on pixel content later if really needed,
            #  or we just accept we might get the same graph twice if it's hybrid.)
            
            outpath = os.path.join(outdir, f"page_{pno+1}_vector_{i+1}.png")
            
            # Pad
            clip_rect = fitz.Rect(rect[0]-10, rect[1]-10, rect[2]+10, rect[3]+10)
            
            try:
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
                
                # Check if it's white/empty (common with invisible layout rects)
                # Simple heuristic: if filesize is tiny, it's likely empty
                # But pix.size is raw bytes. 
                # Better: skip if too small dimensions
                if pix.width < 80 or pix.height < 80:
                    continue
                    
                pix.save(outpath)
                
                # Basic check: file size to avoid empty white squares
                if os.path.getsize(outpath) < 1000:
                    os.remove(outpath)
                    continue
                    
                found_images.append({
                    "path": outpath,
                    "caption": f"Chart/Diagram (Vector) from Page {pno+1}"
                })
            except Exception as e:
                pass
                
    except Exception as e:
        print(f"[WARN] Vector extraction failed page {pno+1}: {e}")
        
    return found_images

# ==========================================

def read_pdf_pages(path: str) -> Tuple[List[str], Dict[int, List[Dict]]]:
    """
    Extract text, images, tables, and vector graphics.
    """
    pages_text: List[str] = []
    pages_images: Dict[int, List[Dict]] = {}
    
    try:
        doc = fitz.open(path)
        page_count = len(doc)
    except Exception as e:
        raise RuntimeError(f"Failed to open PDF: {e}")

    outdir = "./paper2ppt_figs"
    
    # NEW: Cleanup old images if they exist
    if os.path.exists(outdir):
        try:
            shutil.rmtree(outdir)
        except Exception as e:
            print(f"[WARN] Failed to clean old images: {e}")
            
    os.makedirs(outdir, exist_ok=True)
    
    print(f"[INFO] Processing {page_count} pages (Text + Images + Tables + Graphs)...")

    for pno in range(page_count):
        page = doc[pno]
        
        # 1. BASIC TEXT
        txt = page.get_text()
        
        # 2. STANDARD IMAGES (Bitmap)
        page_image_list = []
        
        # -- Existing logic for bitmap extraction (Simplified for brevity but kept robust) --
        # (We use a lighter pass here to avoid massive code duplication, assuming get_images is sufficient along with vectors)
        
        raw_imgs = page.get_images(full=True)
        for idx, info in enumerate(raw_imgs):
            try:
                xref = info[0]
                outpath = os.path.join(outdir, f"page_{pno+1}_img_{idx+1}.png")
                if _save_pixmap_from_xref(doc, xref, outpath):
                    page_image_list.append({"path": outpath, "caption": ""})
            except:
                continue
                
        # 3. VECTOR GRAPHICS (Charts/Graphs)
        vectors = extract_vector_graphics_from_page(page, pno, outdir)
        page_image_list.extend(vectors)
        
        # 4. TABLES (Images + Text)
        tables_imgs, table_md = extract_tables_from_page(page, pno, outdir)
        page_image_list.extend(tables_imgs)
        
        if table_md:
            txt += table_md # Append markdown data to text for LLM
            
        pages_text.append(txt)
        pages_images[pno] = page_image_list
        
        if page_image_list:
             print(f"[INFO] Page {pno+1}: Extracted {len(page_image_list)} visual assets (Images/Tables/Graphs)")

    # Summary
    total_assets = sum(len(imgs) for imgs in pages_images.values())
    print(f"\n[SUMMARY] Extracted {total_assets} total visual assets from {page_count} pages")

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