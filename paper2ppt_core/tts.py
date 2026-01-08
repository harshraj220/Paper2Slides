import sys, shutil, subprocess
from pathlib import Path
try:
    import pyttsx3
except Exception:
    pyttsx3 = None
try:
    from gtts import gTTS
except Exception:
    gTTS = None

AUDIO_DIR = Path("paper2ppt_audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def synthesize(narration: str, idx: int) -> str:
    """
    Return path to created audio file (string) or empty string on failure.
    Order: pyttsx3 -> macOS say -> gTTS
    """
    base_mp3 = AUDIO_DIR / f"slide_{idx}.mp3"

    # 1) pyttsx3 -> write wav then convert
    if pyttsx3 is not None:
        try:
            eng = pyttsx3.init()
            wav = AUDIO_DIR / f"slide_{idx}.wav"
            eng.save_to_file(narration, str(wav))
            eng.runAndWait()
            # if ffmpeg available convert
            if shutil.which("ffmpeg"):
                subprocess.run(["ffmpeg","-y","-i",str(wav), str(base_mp3)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                wav.unlink(missing_ok=True)
                return str(base_mp3)
            return str(wav)
        except Exception:
            pass

    # 2) macOS 'say'
    if sys.platform == "darwin":
        try:
            aiff = AUDIO_DIR / f"slide_{idx}.aiff"
            subprocess.run(["say","-o",str(aiff), narration], check=True)
            if shutil.which("ffmpeg"):
                subprocess.run(["ffmpeg","-y","-i",str(aiff), str(base_mp3)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                aiff.unlink(missing_ok=True)
                return str(base_mp3)
            return str(aiff)
        except Exception:
            pass

    # 3) gTTS fallback (requires network)
    if gTTS is not None:
        try:
            tts = gTTS(text=narration)
            tts.save(str(base_mp3))
            return str(base_mp3)
        except Exception:
            pass

    return ""


def synthesize_narration(narration: str, out_path):
    """Write narration to out_path.
    out_path may be a Path or string. Returns the path string on success or empty string on failure.
    Uses pyttsx3 -> macOS 'say' -> gTTS (same layered logic as synthesize()).
    """
    import sys, shutil, subprocess
    from pathlib import Path
    try:
        outp = Path(out_path)
    except Exception:
        outp = Path(str(out_path))
    # ensure directory exists
    outp.parent.mkdir(parents=True, exist_ok=True)

    # 1) try pyttsx3 -> write wav then convert with ffmpeg if available
    try:
        if 'pyttsx3' in globals() and pyttsx3 is not None:
            try:
                eng = pyttsx3.init()
                wav = outp.with_suffix('.wav')
                eng.save_to_file(narration or " ", str(wav)); eng.runAndWait()
                if shutil.which('ffmpeg'):
                    subprocess.run(['ffmpeg','-y','-i',str(wav), str(outp)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    wav.unlink(missing_ok=True)
                    return str(outp)
                return str(wav)
            except Exception:
                pass
    except Exception:
        pass

    # 2) macOS 'say' -> AIFF, convert if ffmpeg present
    if sys.platform == 'darwin':
        try:
            aiff = outp.with_suffix('.aiff')
            subprocess.run(['say','-o', str(aiff), narration or " "], check=True)
            if shutil.which('ffmpeg'):
                subprocess.run(['ffmpeg','-y','-i', str(aiff), str(outp)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                aiff.unlink(missing_ok=True)
                return str(outp)
            return str(aiff)
        except Exception:
            pass

    # 3) gTTS fallback
    try:
        if 'gTTS' in globals() and gTTS is not None:
            t = gTTS(text=narration or " ")
            t.save(str(outp))
            return str(outp)
    except Exception:
        pass

    return ""
