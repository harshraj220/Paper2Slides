import subprocess
import sys
import os

def run():
    if len(sys.argv) < 2:
        print("Usage: python3 run_pipeline.py <paper.pdf>")
        sys.exit(1)

    input_paper = sys.argv[1]

    # Intermediate slides file
    slides_ppt = "output.pptx"
    slides_path = os.path.abspath(slides_ppt)

    # Final narrated file (created by narration step)
    paper_base = os.path.splitext(os.path.basename(input_paper))[0]
    final_ppt = f"{paper_base}_summary_with_narration.pptx"

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

    print("[paper2ppt] Adding narration (hidden)...")
    subprocess.run(
        [
            sys.executable,
            "main.py",
            slides_path
        ],
        cwd="ppt_narration_project",
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Optional cleanup
    for f in ["output.pptx", "output_with_speaker_notes.pptx"]:
        if os.path.exists(f):
            os.remove(f)


    print(f"[paper2ppt] ✅ Final output ready: {final_ppt}")

if __name__ == "__main__":
    run()
