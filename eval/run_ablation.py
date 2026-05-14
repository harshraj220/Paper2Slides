#!/usr/bin/env python3
"""
Decify Ablation Study Harness

This script runs a target PDF through the slide generation pipeline twice:
1. KB-OFF (Baseline text-only summarization)
2. KB-ON  (Decify citation-grounded knowledge graph summarization)

It provides a side-by-side comparison of the generated bullet points for evaluation.
"""

import os
import sys
import json
from pathlib import Path

# Ensure project root is in python path so we can import core modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from paper2ppt_cli import generate_slides

def print_header(text):
    print("\n" + "=" * 80)
    print(f" {text.center(78)} ")
    print("=" * 80 + "\n")

def run_ablation_test(pdf_path: str):
    if not os.path.exists(pdf_path):
        print(f"[Error] PDF path does not exist: {pdf_path}")
        sys.exit(1)

    pdf_name = Path(pdf_path).stem
    eval_dir = Path(__file__).resolve().parent
    
    output_off = str(eval_dir / f"{pdf_name}_ablation_KB_OFF.pptx")
    output_on = str(eval_dir / f"{pdf_name}_ablation_KB_ON.pptx")

    print_header(f"RUNNING ABLATION STUDY FOR: {pdf_name}")

    # --- PHASE 1: KB-OFF (Baseline) ---
    print("\n>>> [1/2] RUNNING BASELINE: KB-OFF (Pure Document Extraction)...")
    try:
        _, slides_off, _, _ = generate_slides(
            input_pdf=pdf_path,
            output_ppt=output_off,
            max_bullets=4,
            disable_kb=True
        )
        print(f"✅ Saved KB-OFF Presentation to: {output_off}")
    except Exception as e:
        print(f"❌ KB-OFF generation failed: {e}")
        slides_off = []

    # --- PHASE 2: KB-ON (Decify Core) ---
    print("\n>>> [2/2] RUNNING DECIFY: KB-ON (Citation Knowledge Graph)...")
    try:
        _, slides_on, _, _ = generate_slides(
            input_pdf=pdf_path,
            output_ppt=output_on,
            max_bullets=4,
            disable_kb=False
        )
        print(f"✅ Saved KB-ON Presentation to: {output_on}")
    except Exception as e:
        print(f"❌ KB-ON generation failed: {e}")
        slides_on = []

    # --- PHASE 3: SIDE-BY-SIDE LOGICAL REPORTING ---
    print_header("SIDE-BY-SIDE COMPARISON")
    
    # Organize by section for easy mapping
    def build_section_dict(slides_plan):
        sec_dict = {}
        for slide in slides_plan:
            title = slide.get("title", "Unknown").replace(" (continued)", "")
            if title not in sec_dict:
                sec_dict[title] = []
            sec_dict[title].extend(slide.get("bullets", []))
        return sec_dict

    dict_off = build_section_dict(slides_off)
    dict_on = build_section_dict(slides_on)

    comparison_report = {
        "paper": pdf_name,
        "sections": {}
    }

    # We are mostly interested in Introduction, Overview, Background, Related Work
    target_sections = ["Overview", "Introduction", "Background", "Related Work", "Method"]
    all_titles = set(dict_off.keys()).union(set(dict_on.keys()))
    intersect = [t for t in target_sections if t in all_titles]
    
    # If none of target match, just use whatever intersect exists
    if not intersect:
        intersect = list(set(dict_off.keys()).intersection(set(dict_on.keys())))[:2]

    for sec in intersect:
        print(f"\n📌 SECTION: {sec.upper()}")
        print("-" * 80)
        
        bullets_off = dict_off.get(sec, ["(No content generated)"])
        bullets_on = dict_on.get(sec, ["(No content generated)"])

        print(f"{'[MODE A: KB-OFF (Text Only)]':<40} | {'[MODE B: KB-ON (Decify Engine)]':<40}")
        print("-" * 80)
        
        max_lines = max(len(bullets_off), len(bullets_on))
        
        comparison_report["sections"][sec] = {
            "kb_off": bullets_off,
            "kb_on": bullets_on
        }

        for i in range(max_lines):
            b_off = bullets_off[i] if i < len(bullets_off) else ""
            b_on = bullets_on[i] if i < len(bullets_on) else ""
            
            # Strip the "* " for display
            clean_off = b_off.replace("* ", "").strip()
            clean_on = b_on.replace("* ", "").strip()
            
            # Truncate long lines for visual layout
            disp_off = clean_off[:37] + "..." if len(clean_off) > 40 else clean_off
            disp_on = clean_on[:37] + "..." if len(clean_on) > 40 else clean_on
            
            print(f"{disp_off:<40} | {disp_on:<40}")
            
    # Save JSON report
    report_path = eval_dir / f"ablation_report_{pdf_name}.json"
    with open(report_path, "w") as f:
        json.dump(comparison_report, f, indent=2)
        
    print_header("ABLATION STUDY COMPLETE")
    print(f"Detailed comparison payload dumped to: {report_path}")
    print("Use this report to extract visual differences for your paper tables!\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 eval/run_ablation.py <pdf_file_path>")
        print("Example: python3 eval/run_ablation.py test_pdfs/lora.pdf")
        sys.exit(1)
        
    run_ablation_test(sys.argv[1])
