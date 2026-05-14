<div align="center">
  <h1>🎙️ Decify</h1>
  <p><strong>Let The Paper Speak: Citation-Grounded Knowledge Graph Distillation for Automated Narrated Presentations</strong></p>

  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 🌟 Overview

**Decify** (formerly Paper2Slides) is a next-generation academic research architecture that demonstrates the principle of *"Let The Paper Speak."* It instantly converts dense academic research papers (PDFs) into concise, high-fidelity presentation slides with embedded neural narration.

Unlike standard summarization wrappers, Decify utilizes a **Citation-Anchored Synthesis Pipeline**. It retrieves a paper's foundational references via the Semantic Scholar API, constructs a cross-paper knowledge graph, and grounds the LLM to synthesize highly factual, context-aware bullet points. 

This platform features a robust **FastAPI-driven microservices architecture** wrapped in a high-end, obsidian-glassmorphic dashboard for a first-class research experience.

---

## ✨ Research & Technical Novelty

- 🔗 **Citation-Anchored Knowledge Graphs**: Dynamically retrieves cited abstracts via Semantic Scholar to ground generated slide content in the paper's actual academic ecosystem.
- 🧠 **Smart Contextual Extraction**: Leverages LLM abstractive synthesis enriched by cross-paper relational mapping to distill complex theories.
- 🗣️ **Edge TTS Autopilot**: Crystal-clear AI voices embedded invisibly into the PPTX speaker notes, enabling self-presenting academic literature.
- 💬 **Neural Refinement Chat**: A built-in conversational bridge allowing researchers to "chat" with slides and execute on-the-fly targeted reconstruction of any node.
- 🎨 **Next-Gen Aesthetic Suite**: High-performance, animated visual dashboard with custom glassmorphic panels and real-time telemetry widgets.
- 🚀 **Asynchronous Architecture**: FastAPI background queuing ensures massive parallel workloads without blocking the HTTP experience.

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
Configure your environment variables in a `.env` file for Bedrock/Mistral access:
```env
AWS_ACCESS_KEY_ID="your-aws-access-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
AWS_REGION="us-east-1"
BEDROCK_MODEL_ID="mistral.mistral-large-2402-v1:0"
```

### 4. Fire Up the Server Cluster
Initialize the standalone FastAPI gateway (runs on standard HTTP port):
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
├── paper2slides.py              # Main Terminal (CLI) Orchestrator & Interactive Loop
├── knowledge_builder.py         # Knowledge Graph construction module
├── citation_extractor.py        # Semantic Scholar citation retrieval engine
├── models/
│   └── mistral_llm.py           # LLM orchestration & retry-loop wrapper
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

## 🤝 Contributing

Technical issues, architectural feedback, and contribution bridges are highly welcome! Inspect the [issues page](https://github.com/harshraj220/Paper2Slides/issues).

---

<div align="center">
  <i>Engineered with Excellence by Harsh Raj</i>
</div>
