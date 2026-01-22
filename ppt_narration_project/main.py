import os

from .slide_extractor import extract_slides
from .summary_generator import generate_summary
from .narration_generator import generate_narration
from .speaker_notes_writer import add_speaker_notes
from .tts_generator import generate_tts
from .ppt_audio_embedder import embed_audio


def generate_narrated_ppt(input_ppt):
    # Directory cleaned inside generate_tts
    
    slides = extract_slides(input_ppt)
    narrations = []
    total = len(slides)
    print(f"[INFO] Generating narration for {total} slides...")

    for i, slide in enumerate(slides, 1):
        # NOTE: summary generation blocked as it was unused and slow
        # summary = generate_summary(slide["slide_title"], slide["original_slide_text"])
        
        print(f"  > Processing slide {i}/{total}...", end="\r", flush=True)
        
        narration = generate_narration(
            slide["slide_title"],
            slide["original_slide_text"],
            "" # summary unused
        )

        narrations.append(narration)
    
    print(f"\n[INFO] Narration generation complete.")

    notes_ppt = "output_with_speaker_notes.pptx"
    add_speaker_notes(input_ppt, narrations, notes_ppt)

    generate_tts(narrations)

    final_ppt = "final_with_audio.pptx"
    embed_audio(
        input_ppt=notes_ppt,
        audio_dir="tts_audio",
        output_ppt=final_ppt
    )

    return final_ppt
