import subprocess
import sys
import os
import shutil

def run():
    if len(sys.argv) < 2:
        print("Usage: python3 run_pipeline.py <paper.pdf>")
        sys.exit(1)

    input_paper = sys.argv[1]

    # Paths
    slides_ppt = "output.pptx"
    slides_path = os.path.abspath(slides_ppt)

    narration_dir = "ppt_narration_project"
    narration_input = os.path.join(narration_dir, "input.pptx")

    paper_base = os.path.splitext(os.path.basename(input_paper))[0]
    final_name = f"{paper_base}_summary_with_narration.pptx"

    # STEP 1: Generate summarized slides
    print("[paper2ppt] Generating summarized slides...")
    subprocess.run(
        [
            sys.executable,
            "paper2ppt_cli.py",
            "-i", input_paper,
            "-o", slides_path
        ],
        check=True
    )

    # STEP 2: Copy slides into narration directory
    shutil.copy(slides_path, narration_input)

    # STEP 3: Run narration (relative path, correct context)
    print("[paper2ppt] Adding narration (hidden)...")
    subprocess.run(
        [
            sys.executable,
            "main.py",
            "input.pptx"
        ],
        cwd=narration_dir,
        check=True
    )

    # STEP 4: Move final output back to root
    final_src = os.path.join(narration_dir, "final_with_audio.pptx")
    final_dst = os.path.abspath(final_name)

    if not os.path.exists(final_src):
        print("[paper2ppt] ❌ ERROR: final_with_audio.pptx was NOT created")
        sys.exit(1)

    os.replace(final_src, final_dst)

    print(f"[paper2ppt] ✅ Final output ready: {final_name}")

if __name__ == "__main__":
    run()
