import re, sys, shutil, os

ROOT = os.path.abspath(os.path.dirname(__file__))
CLI = os.path.join(ROOT, "paper2ppt_cli.py")
BU_CLI = CLI + ".bak.autopatch"
BACKUP_FILES = []

def backup(src):
    dst = src + ".bak." + str(int(__import__('time').time()))
    shutil.copy2(src, dst)
    BACKUP_FILES.append(dst)
    print("Backed up:", src, "->", dst)

if not os.path.exists(CLI):
    print("ERROR: cannot find", CLI)
    sys.exit(1)

backup(CLI)

text = open(CLI, "r", encoding="utf-8").read()

# 1) Insert pages_images helper BEFORE the slide-planning loop.
# We'll search for the first occurrence of a loop that iterates sections:
m_loop = re.search(r'(^\s*for\s+sec\s+in\s+sections\s*:)', text, flags=re.MULTILINE)
if not m_loop:
    # try alternate form
    m_loop = re.search(r'(^\s*for\s+sec\s+in\s+sections\b)', text, flags=re.MULTILINE)
if not m_loop:
    print("ERROR: could not find 'for sec in sections' in paper2ppt_cli.py. Aborting. Please open the file and tell me where slides_plan is constructed.")
    sys.exit(1)

insert_pos = m_loop.start()

helper = r"""
# --- Begin: ensure pages_images includes disk-extracted figures ---
import os, re
FIG_DIR_CANDIDATES = [
    "/Users/harsh/paper2ppt/paper2ppt_figs",
    "/tmp/paper2ppt_figs"
]
_pages_images_from_disk = {}
for d in FIG_DIR_CANDIDATES:
    if os.path.isdir(d):
        for fn in os.listdir(d):
            m = re.match(r'page[_\-]?(\d+)_img', fn, flags=re.IGNORECASE)
            if m:
                pnum = int(m.group(1)) - 1   # convert filename page number to 0-based index
                _pages_images_from_disk.setdefault(pnum, []).append(os.path.join(d, fn))
if 'pages_images' in globals():
    for k, v in _pages_images_from_disk.items():
        pages_images.setdefault(k, []).extend(v)
else:
    pages_images = _pages_images_from_disk
# --- End helper ---
"""

# Only insert helper if it's not already present
if "ensure pages_images includes disk-extracted figures" not in text:
    text = text[:insert_pos] + helper + text[insert_pos:]
    print("Inserted pages_images helper before slide-planning loop.")
else:
    print("Helper already present; skipping insertion.")

# 2) Replace image-gathering + slide append block.
# We'll look for a pattern that computes candidate_pages and imgs and then a loop 'for i in range(0, len(bullets), BULLETS_PER_SLIDE):'
pattern = re.compile(
    r"candidate_pages\s*=\s*sorted\([^\n]*\)[\s\S]*?imgs\s*=\s*\[[^\]]*\][\s\S]*?for\s+i\s+in\s+range\(0,\s*len\(bullets\)[^\)]*\):",
    flags=re.MULTILINE
)

new_block = r"""
    # candidate_pages for this section (0-indexed)
    candidate_pages = sorted(list(sec.get('pages', [])))
    imgs = []
    for p in candidate_pages:
        imgs_for_page = pages_images.get(p, []) or []
        if imgs_for_page:
            imgs_for_page_sorted = sorted(imgs_for_page, key=lambda x: -os.path.getsize(x))
            for ip in imgs_for_page_sorted:
                imgs.append({'path': ip, 'caption': ''})
    # dedupe preserving order
    seen_paths = set()
    imgs_unique = []
    for it in imgs:
        if it['path'] not in seen_paths:
            seen_paths.add(it['path'])
            imgs_unique.append(it)
    imgs = imgs_unique

    # now split bullets into slides and attach images per slide (2 images per slide)
    for i in range(0, len(bullets), BULLETS_PER_SLIDE):
        part = bullets[i:i+BULLETS_PER_SLIDE]
        t = title if i == 0 else f\"{title} (cont.)\"
        # distribute images: 2 images per slide
        img_start = (i // BULLETS_PER_SLIDE) * MAX_FIGURES_PER_SLIDE
        images_for_this_slide = imgs[img_start : img_start + MAX_FIGURES_PER_SLIDE]
        slide_entry = {
            "title": t,
            "bullets": part,
            "images": images_for_this_slide
        }
        # attach insight and tldr to the first slide only
        if i == 0:
            if sec.get('insight'):
                slide_entry['insight'] = sec.get('insight')
            if sec.get('tldr'):
                slide_entry['tldr'] = sec.get('tldr')
        slides_plan.append(slide_entry)
"""

# If the pattern is found, replace it. Otherwise try a more permissive replacement (look for candidate_pages line alone).
if pattern.search(text):
    text = pattern.sub(new_block, text, count=1)
    print("Replaced image-gathering + slide-append block (pattern matched).")
else:
    # try to find simpler pattern and replace chunk between candidate_pages and slides_plan.append
    m = re.search(r"(candidate_pages\s*=.*\n)(?:[\s\S]*?)(for\s+i\s+in\s+range\(0,\s*len\(bullets\)[\s\S]*?:)", text)
    if m:
        start = m.start(1)
        end = m.start(2)
        text = text[:start] + new_block + text[end:]
        print("Replaced image-gathering + slide-append block using fallback pattern.")
    else:
        print("WARNING: could not find the expected image-gathering block to replace. No changes made to slide-append block.")
        # write file and exit so user can inspect
        open(CLI, "w", encoding="utf-8").write(text)
        print("Wrote file (helper only). Exiting.")
        sys.exit(0)

# write changes
open(CLI, "w", encoding="utf-8").write(text)
print("Wrote patched file:", CLI)
print("Backups created:", BACKUP_FILES)
