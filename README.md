
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

## Project Structure (Key Files)

```
paper2slides/
├── paper2slides.py              # Orchestrates the full pipeline
├── paper2ppt_cli.py             # Slide generation from paper
├── ppt_narration_project/       # Narration, TTS, and audio embedding
├── paper2ppt_core/              # Core summarization logic
├── paper2ppt_figs/              # Figure handling utilities
├── requirements.txt
└── README.md
```

---

## Design Principles

* Modular, step-by-step pipeline
* No manual intervention between stages
* Clean separation of summarization, slides, and narration
* Output optimized for presentations, not raw text inspection

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
