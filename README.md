
# Paper2Slides

Paper2Slides is an automated pipeline that converts research papers into concise presentation slides with hidden narration and embedded audio, producing presentation-ready PowerPoint files from a single command.

---

## Features

* Converts research papers (PDF) into summarized presentation slides
* Generates clean, topic-based slides suitable for academic and technical talks
* Automatically creates narration aligned with each slide
* Embeds narration as hidden speaker notes and audio
* Maintains a clean slide layout without exposing narration text
* End-to-end automation with a single command

---

## How It Works

1. Extracts and summarizes content from a research paper
2. Generates structured slides with titles and bullet points
3. Creates detailed narration for each slide (hidden from view)
4. Converts narration into audio
5. Embeds narration and audio into the final presentation

The user receives **one final PPTX file** containing:
````markdown

# Paper2Slides

Paper2Slides is an automated pipeline that converts research papers into concise presentation slides with hidden narration and embedded audio, producing presentation-ready PowerPoint files from a single command.

---

## Features

* Converts research papers (PDF) into summarized presentation slides
* Generates clean, topic-based slides suitable for academic and technical talks
* Automatically creates narration aligned with each slide
* Embeds narration as hidden speaker notes and audio
* Maintains a clean slide layout without exposing narration text
* End-to-end automation with a single command

---

## How It Works

1. Extracts and summarizes content from a research paper
2. Generates structured slides with titles and bullet points
3. Creates detailed narration for each slide (hidden from view)
4. Converts narration into audio
5. Embeds narration and audio into the final presentation

The user receives **one final PPTX file** containing:

* Visible summarized slides
* Hidden narration (speaker notes + audio)

---

## Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

Ensure you have a compatible Python environment and required system dependencies for text-to-speech.

---

## Usage

Run the pipeline with a research paper as input:

```bash
python3 paper2slides.py <paper.pdf>
```

Example:

```bash
python3 paper2slides.py aiawn.pdf
```

---

## Output

* One PowerPoint file named after the input paper:

  ```
  <paper_name>_summary_with_narration.pptx
  ```
* Slides contain concise summaries
* Narration is embedded as speaker notes and audio
* No manual steps required

---

## Project Structure

The project is organized efficiently to separate listing, generation, and narration concerns:

```
paper2slides/
├── paper2slides.py              # Main Entry Point: Orchestrates the full pipeline
├── paper2ppt_cli.py             # Core Logic: Extract text, structure slides
├── ppt_narration_project/       # Module: Handles AI narration, TTS (EdgeTTS), and Audio Embedding
│   ├── main.py
│   ├── tts_generator.py         # High-quality Neural TTS generation
│   └── ...
├── paper2ppt_core/              # Utilities: Text cleaning and sectioning
├── models/                      # AI Model Interfaces (Qwen, etc.)
├── scripts/                     # Helper utilities and experimental scripts
├── archive/                     # Deprecated or legacy scripts
├── requirements.txt             # Dependency definitions
└── README.md
```

## clean & Readable Code

This project adheres to key design principles:
1.  **Modularity**: Each step (extraction, summarization, narration, audio) is a separate module.
2.  **Clean Output**: Temporary files are managed safely; final output is a single, professional PPTX.
3.  **High Quality Audio**: Uses `edge-tts` for natural-sounding narration.


---

## Notes

* Narration is intentionally hidden to keep slides clean
* Audio playback depends on PowerPoint or compatible viewers
* Intermediate files may be generated internally and cleaned automatically

---

## Use Cases

* Academic presentations
* Research paper reviews
* Lecture material generation
* Technical talk preparation

---

````
