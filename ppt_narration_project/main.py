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
