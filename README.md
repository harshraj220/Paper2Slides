<div align="center">
  <h1>🎙️ Paper2Slides</h1>
  <p><strong>Transform Research Papers into Narrated, Presentation-Ready PowerPoints in Seconds</strong></p>

  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://deckify.streamlit.app/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 🌟 Overview

**Paper2Slides** is an end-to-end automated pipeline and web application that instantly converts academic research papers (PDFs) into concise, high-quality presentation slides. 

Beyond just summarizing text, Paper2Slides intelligently extracts diagrams and tables, generates a logical presentation flow, and synthesizes **hidden speaker notes and TTS narration audio** for every single slide.

Whether you are preparing for a conference, a seminar, or a quick lab meeting, Paper2Slides handles the heavy lifting so you can focus on the delivery.

---

## ✨ Key Features

- 📄 **Smart PDF Extraction**: Seamlessly extracts text, headings, mathematical context, tables, and visual figures from academic PDFs.
- 🧠 **AI-Powered Summarization**: Uses **Qwen 2.5 7B** (via OpenRouter) to abstract high-level concepts and generate concise, impactful bullet points.
- 🎨 **Automated Layouts**: Assembles slides dynamically, automatically chunking long sections to prevent text-heavy slides.
- 🗣️ **Neural Narration (TTS)**: Automatically writes explanatory speaker notes and generates high-quality audio using `edge-tts`.
- 💬 **Interactive Chat Refinement**: A built-in chat interface allows you to ask questions and refine specific slides on the fly.
- ☁️ **Cloud Ready**: Lightweight dependency structure, easily deployable to Streamlit Community Cloud.

---

## 🚀 Live Demo

Try the live web application directly in your browser:
👉 **[Deckify on Streamlit](https://deckify.streamlit.app/)**

---

## 💻 Local Installation

To run Paper2Slides on your local machine, follow these steps:

### 1. Clone the Repository
```bash
git clone https://github.com/harshraj220/Paper2Slides.git
cd Paper2Slides
```

### 2. Install Dependencies
Ensure you have Python 3.11+ installed.
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Paper2Slides uses the OpenRouter API for free access to Qwen 2.5. Export your API key in your terminal:
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key-here"
```

---

## 🛠️ Usage

### Running the Web Application (Streamlit)
To launch the interactive web UI:
```bash
streamlit run app.py
```

### Running the CLI Pipeline
If you prefer to generate presentations directly from the command line:
```bash
python3 paper2slides.py path/to/your/paper.pdf
```
*Output: A file named `<paper_name>_summary_with_narration.pptx` will be generated in the root directory.*

---

## 📂 Project Architecture

```text
Paper2Slides/
├── app.py                       # Streamlit Web Application Entry Point
├── paper2slides.py              # CLI Entry Point & Interactive Refinement Loop
├── paper2ppt_cli.py             # Core Engine: Orchestrates extraction & layout
├── models/
│   └── qwen_llm.py              # OpenRouter API wrapper for Qwen 2.5
├── paper2ppt_core/
│   ├── summarize.py             # AI prompt engineering & summarization logic
│   ├── sections.py              # Academic section detection & filtering
│   ├── io.py                    # PDF parsing and image extraction (PyMuPDF)
│   └── pptx_builder.py          # PowerPoint XML generation engine
├── ppt_narration_project/       
│   ├── narration_generator.py   # AI script writing for speaker notes
│   ├── tts_generator.py         # Neural TTS generation via Edge-TTS
│   └── ppt_audio_embedder.py    # Embeds audio directly into PPTX slides
└── requirements.txt             # Lightweight dependencies for cloud deployment
```

---

## 🧠 Design Philosophy

1. **Noise Reduction over Raw Extraction**: Academic papers are filled with equations, citations, and dense formatting. Paper2Slides is heavily prompted to abstract concepts rather than copy-pasting garbled text.
2. **Accessible AI**: By migrating from heavy local GPU models to the OpenRouter API, this tool runs instantly on any laptop and easily deploys to free cloud tiers.
3. **Human-in-the-Loop**: Generating slides isn't a one-shot process. The interactive chat loop allows users to critique and regenerate specific sections without starting over.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/harshraj220/Paper2Slides/issues).

---

<div align="center">
  <i>Built with ❤️ by Harsh Raj</i>
</div>
