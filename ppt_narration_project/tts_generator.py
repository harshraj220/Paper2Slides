
import asyncio
import os
import edge_tts

async def generate_single_audio(text, output_file, voice="en-US-ChristopherNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def generate_tts(narrations, output_dir="tts_audio"):
    """
    Generate one audio file per slide narration using Edge TTS (Natural sounding).
    """
    # Clean/Create directory
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print(f"[TTS] Generating {len(narrations)} audio files using Edge TTS...")
    
    async def process_all():
        tasks = []
        for idx, narration in enumerate(narrations, start=1):
            text = narration.strip()
            if not text:
                text = " " # Silence
            
            output_path = os.path.join(output_dir, f"slide_{idx}.wav") # edge-tts handles format based on ext usually, but mp3 is native. pptx creates issues with mp3 sometimes, but let's try. Actually pptx prefers .wav or .mp3. edge-tts save implies mp3 usually. 
            # Force .mp3 extension if edge-tts defaults to it, but we can stick to .wav if we want. 
            # Note: edge-tts native output is mp3. Renaming to .wav acts weird sometimes. 
            # Let's verify codec. Actually let's use .mp3 for safety with edge-tts and update embedder.
            output_path = os.path.join(output_dir, f"slide_{idx}.mp3")
            
            print(f"[DEBUG] Queueing slide {idx} | Len: {len(text)}")
            tasks.append(generate_single_audio(text, output_path))
        
        await asyncio.gather(*tasks)

    # Run async loop
    asyncio.run(process_all())
    print("[TTS] Finished generation.")
