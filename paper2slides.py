import os
import sys

from paper2ppt_cli import generate_slides
from ppt_narration_project.main import generate_narration


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 paper2slides.py <paper.pdf>")
        sys.exit(1)

    input_pdf = sys.argv[1]
    base = os.path.splitext(os.path.basename(input_pdf))[0]

    slides_ppt = "output.pptx"
    final_ppt = f"{base}_summary_with_narration.pptx"

    print("Generating summarized slides...")
    generate_slides(input_pdf, slides_ppt)

    print("Adding narration (hidden)...")
    final_generated = generate_narration(slides_ppt)

    if not os.path.exists(final_generated):
        raise RuntimeError("Final narrated PPT not found")

    os.replace(final_generated, final_ppt)

    print(f"Final output ready: {final_ppt}")


if __name__ == "__main__":
    main()
