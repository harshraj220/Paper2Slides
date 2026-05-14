"""
Paper2Slides Entry Point

This script serves as the main orchestrator for the Research2Presentation pipeline.
It handles:
1.  Command Line Interface (CLI) arguments.
2.  Delegation to `paper2ppt_cli` for structural slide generation.
3.  Delegation to `ppt_narration_project` for AI narration and Audio embedding.
4.  Interactive Query Mode for refining content.
5.  Final cleanup and file renaming.

Usage:
    python3 paper2slides.py <input_pdf>
"""

import os
import re
import sys
from typing import List, Dict, Any

from paper2ppt_cli import generate_slides, normalize_section
from paper2ppt_core.pptx_builder import build_presentation
from ppt_narration_project.main import generate_narrated_ppt
from models.mistral_llm import mistral_generate

def find_relevant_section(query: str, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Identifies the best matching section for a user's query using Mistral + Fuzzy Matching.
    """
    if not sections:
        print("[Error] No sections available to search.")
        return None

    # 1. Create a list of available sections
    titles = [s.get('raw_title', s.get('title', 'Unknown')) for s in sections]
    
    # --- OPTION A: Direct Keyword Match (Robust) ---
    import re
    def tokenize(text):
        return set(w[:-1] if w.endswith('s') and len(w) > 3 else w for w in re.findall(r'\w+', text.lower()))

    # Words to ignore in query
    STOP_WORDS = {'explain', 'elaborate', 'describe', 'details', 'about', 'what', 'is', 'the', 'section', 'part', 'please', 'tell', 'me', 'more', 'how', 'doe', 'work', 'show', 'slide'}
    
    q_tokens = tokenize(query) - STOP_WORDS
    
    best_score = 0
    best_sec = None
    
    print(f"[Debug] Query tokens: {q_tokens}")

    for sec in sections:
        raw_title = sec.get('raw_title', '')
        norm_title = sec.get('title', '')
        
        # Create a combined pool of title tokens
        title_tokens = tokenize(raw_title) | tokenize(norm_title)
        
        # Calculate overlap
        overlap = len(q_tokens.intersection(title_tokens))
        
        # Calculate score: Overlap count matches
        score = overlap
        
        # Bonus: specific exact phrase detection
        if query.lower() in raw_title.lower() or query.lower() in norm_title.lower():
             score += 10
        
        # Bonus: High coverage of query
        if q_tokens and overlap / len(q_tokens) > 0.6:
             score += 2
             
        # Bonus: High coverage of title (e.g. query="method", title="Method")
        if title_tokens and overlap / len(title_tokens) > 0.8:
             score += 2

        if score > best_score:
            best_score = score
            best_sec = sec
            
    if best_score >= 2 or (len(q_tokens) == 1 and best_score >= 1):
         print(f"[System] Keyword match found: '{best_sec.get('raw_title')}' (Score: {best_score})")
         return best_sec

    # --- OPTION B: LLM Semantic Routing ---
    titles_str = "\n".join([f"- {t}" for t in titles])
    prompt = f"""
    Internal Task: Select the most relevant research paper section for the user's query.
    
    Available Sections:
    {titles_str}
    
    User Query: "{query}"
    
    Task: Return ONLY the exact name of the section from the list above that matches the query. 
    If unsure, return "General".
    
    Section Name:
    """
    
    response = mistral_generate(prompt, max_tokens=64).strip()
    cleaned = response.strip("'\" .").lower()
    
    # Try to find exact match from LLM output
    for sec in sections:
        t1 = sec.get('raw_title', '').lower()
        t2 = sec.get('title', '').lower()
        if (cleaned in t1 and cleaned) or (cleaned in t2 and cleaned) or (t1 and t1 in cleaned) or (t2 and t2 in cleaned):
            return sec
            
    # If LLM failed, return None to avoid incorrect updates
    return None

def explain_section(query: str, section_text: str) -> str:
    """
    Generates a detailed explanation of the section tailored to the query, 
    specifically asking for examples from the text.
    """
    prompt = f"""
    You are an expert research assistant. A user has a specific question about a section of a paper.
    
    CONTEXT (Section Text):
    {section_text[:6000]}
    
    USER QUERY: "{query}"
    
    TASK: 
    1. Explain the content of this section in clear, simple terms, directly addressing the query.
    2. REQUIRED: Cite specific examples, data points, or logic *from the text provided* to support your explanation.
    3. If the user is confused, clarify the methodology or results step-by-step.
    4. Ensure your conclusion is complete and does not trail off.
    5. Do NOT repeat the same sentence multiple times.
    6. Stop generating immediately when the explanation is complete.
    
    RESPONSE:
    """
    raw_response = mistral_generate(prompt, max_tokens=1024)
    
    # Post-processing to clean up repetition loop:
    lines = raw_response.split('\n')
    unique_lines = []
    seen = set()
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
             unique_lines.append(line)
             continue
        # Check for repetition or legal footer artifacts
        if "cs.CL" in cleaned or "Aug 20" in cleaned:
             continue
        if cleaned in seen:
             continue
        
        seen.add(cleaned)
        unique_lines.append(line)
        
    return "\n".join(unique_lines).strip()

def generate_bullets_from_explanation(explanation: str) -> List[str]:
    """
    Converts a free-text explanation into presentation bullets.
    """
    prompt = f"""
    Convert the following explanation into detailed presentation bullet points.
    
    TEXT:
    {explanation}
    
    INSTRUCTIONS:
    1. Output 6-8 bullet points.
    2. Each bullet must start with "* ".
    3. Allow bullets to be longer (2-3 sentences) to fully capture the meaning.
    4. Do NOT truncate important details for brevity. Use as many words as needed for clarity.
    5. The system will automatically split these across multiple slides if too long, so do not worry about space.
    6. Ensure every bullet point is a complete sentence ending with punctuation.
    
    BULLETS:
    """
    response = mistral_generate(prompt, max_tokens=1024)
    bullets = []
    for line in response.split('\n'):
        line = line.strip()
        if line.startswith("* ") or line.startswith("- "):
             bullets.append(f"* {line[2:].strip()}")
    return bullets

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 paper2slides.py <paper.pdf>")
        sys.exit(1)

    input_pdf = sys.argv[1]
    base = os.path.splitext(os.path.basename(input_pdf))[0]

    slides_ppt = "output.pptx"
    final_ppt = f"{base}_summary_with_narration.pptx"

    print("[paper2ppt] Generating summarized slides...")
    # Updated unpacking to receive sections and doc_title
    ppt, slides_plan, sections, doc_title = generate_slides(
        input_pdf=input_pdf,
        output_ppt=slides_ppt,
        max_bullets=5
    )

    if not os.path.exists(slides_ppt):
        raise RuntimeError("Slide generation failed")

    print("[paper2ppt] Adding narration (hidden)...")
    narrated = generate_narrated_ppt(slides_ppt)

    if not os.path.exists(narrated):
        raise RuntimeError("Narration generation failed")

    # Move to final destination initially
    if os.path.exists(final_ppt):
        os.remove(final_ppt)
    os.replace(narrated, final_ppt)

    print(f"[paper2ppt] ✅ Final output ready: {final_ppt}")
    
    # ==========================================
    # INTERACTIVE QUERY MODE
    # ==========================================
    print("\n" + "="*50)
    print("      INTERACTIVE QUERY & UPDATE MODE")
    print("="*50)
    
    # Print available slides for clarity
    print("Available Slides:")
    slide_titles = [s['title'] for s in slides_plan]
    for i, t in enumerate(slide_titles):
        print(f"  {i+1}. {t}")
        
    print("\nThe system can now clarify sections and update the presentation based on your questions.")
    
    while True:
        print("\nType your query (or 'exit'/'quit' to finish):")
        query = input("> ").strip()
        
        if query.lower() in ['exit', 'quit', 'q', 'done', 'no']:
            print("Exiting. Have a great presentation!")
            break
            
        if not query:
            continue
            
        print("[System] Analyzing query and finding relevant section...")
        print(f"[System] Sections available for matching: {[s.get('raw_title') for s in sections]}")
        target_section = find_relevant_section(query, sections)
        
        if not target_section:
            print("[Error] Could not identify a relevant section. Please try rephrasing.")
            continue
            
        raw_section_name = target_section.get('raw_title', target_section.get('title', 'Unknown'))
        # Strip leading numeric prefix for display (e.g., "2.1. Machine learning" -> "Machine learning")
        section_name = re.sub(r'^\s*(?:(?:\d+(?:\.\d+)*)|[IVXLCDM]+|[A-Z])\.?\s+', '', raw_section_name).strip() or raw_section_name
        section_text = target_section.get('text', '')
        
        print(f"[System] Focused on section: {section_name}")
        
        explanation = explain_section(query, section_text)
        
        print("\n" + "-"*30)
        print(f"Explanation for '{section_name}':")
        print(explanation)
        print("-"*30 + "\n")
        
        print("Do you want to UPDATE the presentation slides for this section with this explanation?")
        confirm = input("(y/n) > ").strip().lower()
        
        if confirm == 'y':
            print("[System] Generating new slide content...")
            new_bullets = generate_bullets_from_explanation(explanation)
            
            if not new_bullets:
                print("[Error] Could not generate bullets. Skipping update.")
                continue
            
            # --- IMPROVED MATCHING LOGIC ---
            normalized_target = normalize_section(section_name)
            updated_indices = []

            # 1. Try Exact Normalized Match
            for i, slide in enumerate(slides_plan):
                base_title = slide['title'].replace(" (continued)", "")
                if base_title.lower() == normalized_target.lower():
                    updated_indices.append(i)
            
            # 2. If no exact match, try fuzzy/substring match on Titles
            if not updated_indices:
                print(f"[Debug] Exact match failed for '{normalized_target}'. Trying fuzzy match...")
                keywords = normalized_target.lower().split()
                for i, slide in enumerate(slides_plan):
                    slide_t = slide['title'].lower()
                    # If major section keywords match
                    if any(k in slide_t for k in keywords if len(k) > 3):
                         updated_indices.append(i)

            # 3. Fallback: Match against Section Raw Title
            if not updated_indices:
                raw = section_name.lower()
                for i, slide in enumerate(slides_plan):
                    if slide['title'].lower() in raw or raw in slide['title'].lower():
                        updated_indices.append(i)

            if updated_indices:
                # Update the FIRST matching slide (usually the main one)
                # We could update all, but usually we just want to replace the main content.
                idx = updated_indices[0] 
                target_slide = slides_plan[idx]
                base_title = target_slide['title'].replace(" (continued)", "")
                
                print(f"[System] TARGET IDENTIFIED: Slide '{base_title}'")
                
                # --- DYNAMIC EXPANSION LOGIC ---
                # Check if we need to split into multiple slides
                MAX_PER_SLIDE = 4
                
                # First, remove ALL existing slides associated with this base title to prevent duplicates
                del_count = 0
                while idx < len(slides_plan):
                    curr_title = slides_plan[idx]['title']
                    if curr_title == base_title or curr_title == f"{base_title} (continued)":
                        del slides_plan[idx]
                        del_count += 1
                    else:
                        break
                print(f"[Debug] Cleaned up {del_count} old slide(s) for section '{base_title}' before replacing.")
                
                if len(new_bullets) > MAX_PER_SLIDE:
                    print(f"[System] Content is long ({len(new_bullets)} bullets). Expanding into multiple slides...")
                    
                    # Create chunks
                    chunks = [new_bullets[i:i + MAX_PER_SLIDE] for i in range(0, len(new_bullets), MAX_PER_SLIDE)]
                    
                    # Create new slide objects
                    new_slides_objects = []
                    original_images = target_slide.get('images', []) # Keep images on first slide
                    
                    for i, chunk in enumerate(chunks):
                        title = base_title if i == 0 else f"{base_title} (continued)"
                        new_slides_objects.append({
                            "title": title,
                            "bullets": chunk,
                            "images": original_images if i == 0 else [] 
                        })
                    
                    # Insert new slides in reverse order so they land correctly at idx
                    for s in reversed(new_slides_objects):
                        slides_plan.insert(idx, s)
                        
                    print(f"[System] Expanded into {len(chunks)} slides.")
                else:
                    # Fits in one slide
                    target_slide['bullets'] = new_bullets
                    target_slide['title'] = base_title
                    slides_plan.insert(idx, target_slide)
                
                print("[System] Rebuilding Presentation...")
                # Re-run build
                build_presentation(slides_plan, slides_ppt, doc_title, sections)
                
                print("[System] Regenerating Narration...")
                new_narrated = generate_narrated_ppt(slides_ppt)
                
                if os.path.exists(final_ppt):
                    os.remove(final_ppt)
                os.replace(new_narrated, final_ppt)
                
                print(f"\n[System] ✅ Updated presentation saved to: {final_ppt}")
                print(f"[System] You can open '{final_ppt}' to view the changes.\n")
            else:
                print(f"[Error] Could not find any slide matching section '{section_name}' or '{normalized_target}'.")
                print("Available slides were:", slide_titles)

if __name__ == "__main__":
    main()
