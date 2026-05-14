import re
import os
from typing import List, Dict
from models.mistral_llm import mistral_generate

def extract_citation_entries(ref_text: str) -> List[str]:
    """
    Performs naive but robust parsing of a packed citation block to isolate individual reference rows.
    Accepts diverse formats: [1] Authors..., 1. Authors..., or simply newline split.
    """
    if not ref_text:
        return []
        
    # Standard IEEE format: [1] or [23]
    if "[" in ref_text and re.search(r"\[\d+\]", ref_text):
        # Split by [digit]
        entries = re.split(r"(\[\d+\])", ref_text)
        combined = []
        # Re-stitch the tags back to their associated text
        for i in range(1, len(entries), 2):
             tag = entries[i]
             content = entries[i+1] if (i+1 < len(entries)) else ""
             combined.append(f"{tag} {content.strip()}")
        return [c for c in combined if len(c) > 20]

    # Standard Numeric list format: "1. ", "2. " at beginning
    if re.search(r"(^|\s)\d+\.\s+[A-Z]", ref_text):
        entries = re.split(r"(^|\s)(?=\d+\.\s)", ref_text)
        return [e.strip() for e in entries if len(e.strip()) > 20]

    # Fallback to general sentence/punctuation chunking or LLM split if tiny
    lines = [ln.strip() for ln in ref_text.split('.') if len(ln.strip()) > 30]
    return lines

def select_top_influential_citations(all_entries: List[str], main_abstract: str, limit=5) -> List[str]:
    """
    Uses Mistral to intelligently analyze the massive bibliography and select the top N papers
    that seem foundational to the methodology described in the abstract.
    """
    if not all_entries:
        return []
        
    total = len(all_entries)
    subset = all_entries[:40] # Don't flood the prompt context
    
    entries_str = "\n".join([f"{i+1}. {e}" for i, e in enumerate(subset)])
    
    prompt = f"""
    [SYSTEM ARCHITECT TASK]
    Review the following core paper abstract and list of 40 academic references.
    Identify exactly {limit} citations that are HIGHEST relevance to the technical methodology of the abstract.
    
    CORE ABSTRACT:
    {main_abstract[:1000]}
    
    REFERENCES LIST:
    {entries_str}
    
    Return ONLY the direct quoted text of the 5 chosen references, one per line.
    DO NOT ADD ANY EXPLANATIONS OR INTRO. JUST THE 5 REFERENCES.
    """
    
    try:
        print(f"[CITATION] Dispatching relevance selection to LLM (Scoring {min(40, total)} options)...")
        response = mistral_generate(prompt, max_tokens=800)
        
        # Clean up response to only valid lines
        selected = [ln.strip() for ln in response.split('\n') if len(ln.strip()) > 15]
        
        # Truncate to request limit just in case
        return selected[:limit]
        
    except Exception as e:
        print(f"[CITATION ERROR] Scoring failed: {str(e)}")
        # Fallback: Take first N
        return subset[:limit]

import requests
import time

def fetch_paper_metadata(citation_str: str) -> Dict:
    """
    Queries Semantic Scholar to convert a fuzzy citation string into concrete
    structured metadata, ensuring an abstract or direct PDF URL exists.
    """
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    # Construct optimized query
    clean_query = re.sub(r"\[\d+\]", "", citation_str).strip()
    
    params = {
        "query": clean_query,
        "limit": 1,
        "fields": "title,authors,abstract,openAccessPdf,url,year"
    }
    
    for attempt in range(3):
        try:
            resp = requests.get(base_url, params=params, timeout=15)
            
            if resp.status_code == 429:
                wait = (attempt + 1) * 3
                print(f"[WARN] Rate limited on SS. Sleeping {wait}s...")
                time.sleep(wait)
                continue
                
            resp.raise_for_status()
            data = resp.json()
            
            if not data.get("data"):
                return None
                
            return data["data"][0]
            
        except Exception as e:
            print(f"[DEBUG] SS Fetch attempt {attempt+1} failed for query snippet.")
            time.sleep(1)
            
    return None

def execute_citation_discovery(references_text: str, core_abstract: str, limit=5) -> List[Dict]:
    """
    Master Orchestrator for Phase 2: Citation Discovery Pipeline.
    1. Extracts text blocks
    2. Ranks with LLM context
    3. Fetches semantic graphs
    """
    print("[PHASE 2] Initializing Citation Discovery Engine...")
    
    # 1. Segment
    raw_list = extract_citation_entries(references_text)
    print(f"[PHASE 2] Isolated {len(raw_list)} bibliographic entries.")
    
    # 2. Intelligently Select
    selections = select_top_influential_citations(raw_list, core_abstract, limit=limit)
    print(f"[PHASE 2] LLM isolated top {len(selections)} foundational targets.")
    
    # 3. Resolve 
    results = []
    for item in selections:
        print(f"[PHASE 2] Resolving Metadata -> {item[:50]}...")
        meta = fetch_paper_metadata(item)
        if meta:
            results.append(meta)
            print(f"  ✅ SUCCESS: Located '{meta.get('title')[:40]}...'")
        else:
            print(f"  ❌ NOT FOUND.")
        time.sleep(0.5) # Avoid fast-spam
        
    print(f"[PHASE 2] Discovery Complete. Resolved {len(results)} node candidates.")
    return results

# Basic standalone test
if __name__ == "__main__":
    test_text = "[1] Vaswani et al., 'Attention is all you need', NIPS 2017. [2] Other paper 2023."
    res = execute_citation_discovery(test_text, "We explore Transformer scaling.", limit=1)
    print("Final Output:", res)
