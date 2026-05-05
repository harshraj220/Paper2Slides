import os
import json
import hashlib

from .slide_extractor import extract_slides
from .summary_generator import generate_summary
from .narration_generator import generate_narration
from .speaker_notes_writer import add_speaker_notes
from .tts_generator import generate_tts
from .ppt_audio_embedder import embed_audio

CACHE_FILE = "narration_cache.json"

def get_hash(title, text):
    content = f"{title}_{text}".encode('utf-8', errors='ignore')
    return hashlib.md5(content).hexdigest()

def generate_narrated_ppt(input_ppt):
    # Load cache
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
        except Exception:
            pass
            
    slides = extract_slides(input_ppt)
    narrations = []
    total = len(slides)
    print(f"[INFO] Generating narration for {total} slides...")

    cache_hits = 0
    for i, slide in enumerate(slides, 1):
        print(f"  > Processing slide {i}/{total}...", end="\r", flush=True)
        
        slide_hash = get_hash(slide["slide_title"], slide["original_slide_text"])
        
        if slide_hash in cache:
            narration = cache[slide_hash]
            cache_hits += 1
        else:
            narration = generate_narration(
                slide["slide_title"],
                slide["original_slide_text"],
                "" # summary unused
            )
            cache[slide_hash] = narration

        narrations.append(narration)
    
    print(f"\n[INFO] Narration generation complete. (Cached {cache_hits}/{total} slides)")

    # Save cache for next time
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

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
