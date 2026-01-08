"""
paper2ppt_core — core functions for Paper -> PPT pipeline
Modules:
 - io: pdf/txt read + image extraction
 - sections: split text into sections
 - summarize: heuristic summarizer (and HF wrapper placeholder)
 - tts: layered TTS backends (pyttsx3, say, gTTS)
"""
from .io import read_pdf_pages
from .sections import split_into_sections
from .summarize import heuristic_bullets
from .tts import synthesize
__all__ = ["read_pdf_pages", "split_into_sections", "heuristic_bullets", "synthesize"]
