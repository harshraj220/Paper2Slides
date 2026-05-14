<div align="center">
  <h1>🎙️ Paper2Slides</h1>
  <p><strong>Transform Research Papers into Narrated, Presentation-Ready PowerPoints in Seconds</strong></p>

  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 🌟 Overview

**Paper2Slides** is a next-generation AI architecture that instantly converts dense academic research papers (PDFs) into concise, high-fidelity presentation slides. 

Beyond basic summarization, the engine recursively extracts key methodologies, isolates mathematical theorems, generates structured visual hierarchies, and automatically records **hidden neural TTS narration** directly into every PowerPoint slide.

This platform features a robust **FastAPI-driven microservices architecture** wrapped in a high-end, obsidian-glassmorphic dashboard for a first-class research experience.

---

## ✨ Premium Feature Suite

- 🎨 **Next-Gen Aesthetic Suite**: Ditch minimal UIs for a high-performance, animated visual dashboard with custom glassmorphic panels and real-time telemetry widgets.
- 🚀 **FastAPI Core Engine**: Asynchronous background queuing ensures massive parallel workloads without blocking your HTTP experience.
- 🧠 **Smart Contextual Extraction**: Leverages cutting-edge LLM abstractive synthesis to distill complex theories rather than simply copy-pasting equations.
- 💬 **Neural Refinement Chat**: A built-in conversational bridge allowing researchers to "chat" with slides and execute on-the-fly targeted reconstruction of any node.
- 📊 **Real-Time Streaming Console**: Advanced backend event interception yields a visual monitoring console directly in the web plane, providing immediate feedback on synthesis heartbeats and rate-limiting throttling.
- 🗣️ **Edge TTS Autopilot**: Fully embedded, crystal-clear AI voices embedded invisibly into speaker notes.

---

## 🚀 Local Installation & Deployment

### 1. Clone the Repository
```bash
git clone https://github.com/harshraj220/Paper2Slides.git
cd Paper2Slides
```

### 2. Install Dependencies
Ensure you possess a Python 3.11+ environment.
```bash
pip install -r requirements.txt
```

### 3. Provision Authorization Keys
Paper2Slides operates leveraging modern LLM APIs. Configure your environment variables in a `.env` file:
```env
AWS_ACCESS_KEY_ID="your-aws-access-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
AWS_REGION="us-east-1"
BEDROCK_MODEL_ID="mistral.mistral-large-2402-v1:0"
```

### 4. Fire Up the Server Cluster
Initialize the standalone FastAPI gateway (runs on standard HTTP port for universal mapping):
```bash
uvicorn main_api:app --host 0.0.0.0 --port 80
```

*Access UI instantly at:* `http://localhost`

---

## 📂 System Architecture

```text
Paper2Slides/
├── main_api.py                  # FastAPI Enterprise Backend & Background Queue
├── static/index.html            # High-Fidelity Premium Dashboard (Obsidian Glass)
├── paper2ppt_cli.py             # Primary Extractor & Generation Harness
├── paper2slides.py              # Modular Interactive Inference Helpers
├── models/
│   └── mistral_llm.py              # LLM orchestration & retry-loop wrapper
├── paper2ppt_core/
│   ├── summarize.py             # Academic prompt abstraction logic
│   ├── sections.py              # Semantic section mapping & filtering
│   └── pptx_builder.py          # Native XML Presentation Generator
└── ppt_narration_project/       
    ├── narration_generator.py   # Speaker note AI scripts
    ├── tts_generator.py         # Edge-TTS asynchronous generators
    └── ppt_audio_embedder.py    # Hidden binary audio stream injector
```

---

## 🧠 Strategic Philosophy

1. **Zero-NPM Architecture**: The frontend utilizes Native Vanilla components to remain lightweight and cloud-agnostic, eliminating `node_modules` bloat.
2. **Abstractive Authority**: We enforce rigorous LLM directives targeting "synthesis over repetition," guaranteeing your slides actually teach rather than copy.
3. **Stateless Resiliency**: Our background task queuing paradigm handles crashes gracefully and tracks jobs using persistent RAM mapping.

---

## 🤝 Contributing

Technical issues, architectural feedback, and contribution bridges are highly welcome! Inspect the [issues page](https://github.com/harshraj220/Paper2Slides/issues).

---

<div align="center">
  <i>Engineered with Excellence by Harsh Raj</i>
</div>
