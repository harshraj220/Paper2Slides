# Paper2Slides

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
### Step 6: Interactive Query & Update (New!)
*   **Code**: `paper2slides.py` (Main Loop), `paper2ppt_cli.py` (Slide Matching)
*   **Action**:
    *   Once the initial presentation is built, the system enters an **Interactive Mode**.
    *   It prompts you: `Type your query (or 'exit'/'quit' to finish):`.
    *   You can ask questions (e.g., "Explain the methodology in more detail").
    *   The system uses **Qwen-2.5** to find the relevant section, generate a detailed explanation, and convert it into presentation bullets.
    *   If you approve the update, it **automatically updates the slides** and **regenerates the narration** for that section.
    *   It handles **dynamic slide expansion**: if the new explanation is long, it splits the content into multiple slides.

### Step 7: Final Assembly
*   **Code**: `ppt_narration_project/ppt_audio_embedder.py`
*   **Action**: It inserts the generated audio files onto the correct slides set to "Play in Background". It saves the final result as `<paper_name>_summary_with_narration.pptx`.

---

## 🛠️ Advanced Configuration

### Excluding Sections/Affiliations
The system uses a smart filter to ignore author lists and affiliations. This is configured in `paper2ppt_core/sections.py`. It currently filters out:
*   Universities (e.g., "UC", "MIT", "Institute")
*   Tech Companies (e.g., "Microsoft", "Google", "Meta")
*   Addresses & Metadata ("Street", "Box", "Copyright")

### Slide chunking
*   Default limit per slide: **5 bullets**.
*   If content exceeds this (e.g., detailed interactive updates), formatting is preserved by splitting across `Title` and `Title (continued)` slides.

---

## ❓ Troubleshooting

**Q: The system hangs on "Using Qwen LLM for..."**
*   **A**: This is the model generating text. On slower CPUs, this might take 1-2 minutes per section. Please be patient. We have optimized `max_tokens` to 512 to improve speed.

**Q: My query isn't finding the right section.**
*   **A**: Ensure your query uses keywords present in the paper (e.g., "Architecture" vs "Method"). The system uses semantic fuzzy matching, but specific terms help.

**Q: The presentation has "Ghost" sections (e.g., References).**
*   **A**: The section filtering logic usually catches these. If one slips through, you can list it in the `SKIP_SECTIONS` set in `paper2ppt_cli.py`.

---

## Project Structure

```
paper2slides/
├── paper2slides.py              # Main Entry Point & Interactive Loop
├── paper2ppt_cli.py             # Core Logic: Extraction, Filtering, & Slide Management
├── ppt_narration_project/       # Module: Narration, TTS, audio embedding
│   ├── main.py
│   ├── narration_generator.py   # AI Script Writing (Qwen)
│   ├── tts_generator.py         # Neural TTS (Edge-TTS)
│   └── ppt_audio_embedder.py    # PowerPoint Audio Insertion
├── paper2ppt_core/              # Utilities
│   ├── sections.py              # Section detection & Header filtering
│   ├── pptx_builder.py          # Slide layout engine
│   └── io.py                    # PDF Reading & Image Extraction
├── models/                      # AI Model Interfaces
│   └── qwen_llm.py              # Local LLM wrapper
├── requirements.txt
└── README.md
```

## Design Principles

1.  **Generalization**: The pipeline is robust to different paper formats, filtering out common noise like affiliations and metadata.
2.  **Privacy-First**: Runs entirely locally; no data leaves your machine.
3.  **Human-in-the-Loop**: The interactive mode allows you to refine the AI's output before finalizing the presentation.

