"""
Paper2Slides Entry Point

This script serves as the main orchestrator for the Research2Presentation pipeline.
It handles:
1.  Command Line Interface (CLI) arguments.
2.  Delegation to `paper2ppt_cli` for structural slide generation.
3.  Delegation to `ppt_narration_project` for AI narration and Audio embedding.
4.  Final cleanup and file renaming.

Usage:
    python3 paper2slides.py <input_pdf>
"""

import os
import sys

from paper2ppt_cli import generate_slides
from ppt_narration_project.main import generate_narrated_ppt


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 paper2slides.py <paper.pdf>")
        sys.exit(1)

    input_pdf = sys.argv[1]
    base = os.path.splitext(os.path.basename(input_pdf))[0]

    slides_ppt = "output.pptx"
    final_ppt = f"{base}_summary_with_narration.pptx"

    print("[paper2ppt] Generating summarized slides...")
    generate_slides(
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

    os.replace(narrated, final_ppt)

    print(f"[paper2ppt] ✅ Final output ready: {final_ppt}")


if __name__ == "__main__":
    main()
