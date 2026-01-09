from tts_generator import generate_tts
import sys
from slide_extractor import extract_slides
from summary_generator import generate_summary
from narration_generator import generate_narration
from speaker_notes_writer import add_speaker_notes


def main(ppt_path):
        import os
        os.makedirs("tts_audio", exist_ok=True)

        slides = extract_slides(ppt_path)
        narrations = []

        for slide in slides:
            summary = generate_summary(
                slide["slide_title"],
                slide["original_slide_text"]
            )
            narration = generate_narration(
                slide["slide_title"],
                slide["original_slide_text"],
                summary
            )
            narrations.append(narration)

        output_ppt = "output_with_speaker_notes.pptx"
        add_speaker_notes(ppt_path, narrations, output_ppt)

        if not os.path.exists(output_ppt):
            raise RuntimeError("Speaker notes PPT was not created")

        generate_tts(narrations)

        from ppt_audio_embedder import embed_audio
        embed_audio(
            input_ppt=output_ppt,
            audio_dir="tts_audio",
            output_ppt="final_with_audio.pptx"
        )

        if not os.path.exists("final_with_audio.pptx"):
            raise RuntimeError("Final PPT with audio was not created")
        

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_ppt>")
        sys.exit(1)

    main(sys.argv[1])

