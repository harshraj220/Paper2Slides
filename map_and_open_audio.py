import os, sys, subprocess
from pptx import Presentation
from pathlib import Path

ppt = "test_output_with_audio_embedded.pptx"
auddir = Path("paper2ppt_audio")
prs = Presentation(ppt)
mapping = []
for i, slide in enumerate(prs.slides, start=1):
    audio = auddir / f"slide_{i}.mp3"
    if audio.exists():
        mapping.append((i, str(audio)))
    else:
        # try offset in case title slide changed indexing
        alt = auddir / f"slide_{i-1}.mp3"
        if alt.exists():
            mapping.append((i, str(alt)))
        else:
            mapping.append((i, None))

print("Slide -> audio mapping:")
for s,a in mapping:
    print(f"Slide {s:02d} -> {a if a else 'NO AUDIO'}")

# optionally open audio files (macOS)
for s,a in mapping:
    if a:
        print("Opening", a)
        if sys.platform == "darwin":
            subprocess.Popen(["open", a])
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", a])
        elif sys.platform.startswith("win"):
            os.startfile(a)
