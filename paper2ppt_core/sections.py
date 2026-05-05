import re
from typing import List, Dict

HEADING_PATTERNS = [
    r"^\s*(?:[\w\d]+(?:\.[\w\d]+)*\.?)?\s*abstract\s*$",
    r"^\s*(?:[\w\d]+(?:\.[\w\d]+)*\.?)?\s*introduction\s*$",
    r"^\s*(?:[\w\d]+(?:\.[\w\d]+)*\.?)?\s*background\s*$",
    r"^\s*(?:[\w\d]+(?:\.[\w\d]+)*\.?)?\s*related\s+work\s*$",
    r"^\s*(?:[\w\d]+(?:\.[\w\d]+)*\.?)?\s*(method|methodology|approach|model)\s*$",
    r"^\s*(?:[\w\d]+(?:\.[\w\d]+)*\.?)?\s*(experiments?|results?|evaluation|analysis)\s*$",
    r"^\s*(?:[\w\d]+(?:\.[\w\d]+)*\.?)?\s*(conclusion|future\s+work|limitations)\s*$",
    r"^\s*(?:[\w\d]+(?:\.[\w\d]+)*\.?)?\s*(references|bibliography)\s*$",
]

def clean_academic_noise(text: str) -> str:
    if not text:
        return ""
    t = text
    t = re.sub(r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]", " ", t)
    t = re.sub(r"https?://\S+|doi:\S+|arXiv:\S+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def is_heading_line(line: str) -> bool:
    if not line:
        return False
    l = line.strip()

    # hard length guard
    if not (3 <= len(l) <= 80):
        return False

    # strict academic headings
    for pat in HEADING_PATTERNS:
        if re.match(pat, l, flags=re.IGNORECASE):
            return True

    # numbered section headers ONLY (not captions)
    # Support "1. Title", "1.1 Title", "A. Title", "I. Title"
    if re.match(r"^\s*(?:\d+(?:\.\d+)*|[A-Z]|[IVXLCDM]+)\.\s+[A-Z][A-Za-z\s]{2,60}$", l):
        # Reject affiliation-like headers
        # Generalized Exclusion List for Affiliations/Metadata
        # Blocks terms indicating addresses, institutions, or non-content metadata
        check_str = l.lower()
        
        # 1. Institutional Keywords
        if any(x in check_str for x in [
            "university", "univ.", "institute", "department", "dept.",
            "laboratory", "lab.", "corporation", "inc.", "ltd.", 
            "school", "college", "faculty", "center", "centre", 
            "group", "association", "foundation", "research",
            "uc", "mit", "cmu", "campus", "box", "id",
            "microsoft", "google", "meta", "ai", "technologies"
        ]):
             return False
             
        # 2. Address/Contact Keywords
        if any(x in check_str for x in [
            "street", "avenue", "road", "p.o. box", "box", 
            "email", "correspondence", "@", "tel:", "fax:"
        ]):
            return False
            
        # 3. Geographic Keywords (Countries & Major Regions - Generalized)
        # Avoids specific cities, focuses on country-level or state-level suffix
        if any(x in check_str for x in [
            "usa", "uk", "china", "japan", "germany", "france", 
            "canada", "australia", "italy", "spain", "india", "brazil",
            "california", "massachusetts", "new york" # Common state-level academic hubs
        ]):
            return False

        # 4. Copyright / Publisher Metadata
        if any(x in check_str for x in [
            "copyright", "reserved", "ieee", "acm", "springer", "elsevier",
            "vol.", "no.", "pp.", "proceedings", "conference", "journal"
        ]):
            return False
            
        return True

    return False

def normalize_heading(h: str) -> str:
    s = (h or "").lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    if "abstract" in s: return "abstract"
    if "introduction" in s: return "introduction"
    if "background" in s: return "background"
    if "related work" in s: return "related work"
    if "method" in s or "approach" in s or "model" in s: return "method"
    if "experiment" in s or "dataset" in s: return "experiments"
    if "result" in s or "analysis" in s: return "results"
    if "conclusion" in s or "limitation" in s: return "conclusion"
    if "literature" in s and "survey" in s: return "related work"
    if "discussion" in s: return "discussion"

    return "section"

def split_into_sections(pages_text: List[str]) -> List[Dict]:
    sections = []
    current = None

    for i, ptxt in enumerate(pages_text):
        lines = [ln.strip() for ln in (ptxt or "").splitlines() if ln.strip()]

        for ln in lines:
            if is_heading_line(ln):
                if current and current["text"].strip():
                    sections.append(current)

                current = {
                    "title": normalize_heading(ln),
                    "raw_title": ln.strip(),
                    "text": "",
                    "pages": {i},
                    "first_page": i,
                }
            else:
                if current is None:
                    # skip junk before first real section
                    continue
                current["text"] += (" " + ln)
                current["pages"].add(i)

    if current and current["text"].strip():
        sections.append(current)

    # cleanup pass
    cleaned = []
    for sec in sections:
        sec["text"] = clean_academic_noise(sec["text"])

        # allow short but meaningful sections
        if len(sec["text"]) < 50 and sec["title"] not in ("abstract", "conclusion"):
            continue

        cleaned.append(sec)

    return cleaned
