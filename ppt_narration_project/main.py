import sys
import os

from .slide_extractor import extract_slides
from .summary_generator import generate_summary
from .narration_generator import generate_narration as _gen_narr
from .speaker_notes_writer import add_speaker_notes
from .tts_generator import generate_tts
from .ppt_audio_embedder import embed_audio




def generate_narration(ppt_path: str, output_ppt: str = "final_with_audio.pptx"):
    import os

    os.makedirs("tts_audio", exist_ok=True)

    slides = extract_slides(ppt_path)
    narrations = []

    for slide in slides:
        summary = generate_summary(
            slide["slide_title"],
            slide["original_slide_text"]
        )
        narration = _gen_narr(
            slide["slide_title"],
            slide["original_slide_text"],
            summary
        )
        narrations.append(narration)

    notes_ppt = "output_with_speaker_notes.pptx"
    add_speaker_notes(ppt_path, narrations, notes_ppt)

    generate_tts(narrations)

    embed_audio(
        input_ppt=notes_ppt,
        audio_dir="tts_audio",
        output_ppt=output_ppt
    )

    # 🔑 THIS LINE IS THE FIX
    return os.path.abspath(output_ppt)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_ppt>")
        sys.exit(1)

    generate_narration(sys.argv[1])
