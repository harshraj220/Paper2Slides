from tts_generator import generate_tts
import sys
from slide_extractor import extract_slides
from summary_generator import generate_summary
from narration_generator import generate_narration
from speaker_notes_writer import add_speaker_notes


def main(ppt_path):
    print("Generating narration...")

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

    print("Narration text generated.")

    output_ppt = "output_with_speaker_notes.pptx"
    print("Adding speaker notes...")
    add_speaker_notes(ppt_path, narrations, output_ppt)
    print(f"Saved: {output_ppt}")

    print("Generating audio narration...")
    generate_tts(narrations)
    print("Audio files generated.")

    from ppt_audio_embedder import embed_audio
    print("Embedding audio into presentation...")
    embed_audio(
        input_ppt=output_ppt,
        audio_dir="tts_audio",
        output_ppt="final_with_audio.pptx"
    )

    print("Final presentation with narration ready.")
