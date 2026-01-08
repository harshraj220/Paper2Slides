import pyttsx3
import os

def generate_tts(narrations, output_dir="tts_audio"):
    """
    Generate one audio file per slide narration.
    """
    os.makedirs(output_dir, exist_ok=True)

    engine = pyttsx3.init()
    engine.setProperty("rate", 170)  # natural speaking speed

    for idx, narration in enumerate(narrations, start=1):
        output_path = os.path.join(output_dir, f"slide_{idx}.wav")
        engine.save_to_file(narration, output_path)

    engine.runAndWait()
