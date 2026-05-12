import os
import uuid
import shutil
import sys
import io
import time
from collections import deque

# GLOBAL THREAD-SAFE LOG BUFFER FOR FRONTEND DELIVERY
class LiveLogBuffer(io.StringIO):
    def __init__(self, limit=10):
        super().__init__()
        self.buffer = deque(maxlen=limit)
        self.terminal = sys.stdout

    def write(self, s):
        self.terminal.write(s)
        clean_s = s.strip()
        if not clean_s:
            return
            
        # STRATEGIC FILTER: Block generic HTTP Noise, permit only actionable logic
        lower_s = clean_s.lower()
        
        # List of mandatory exclusion keywords (prevents HTTP spam)
        if any(x in lower_s for x in ["get /api/", "post /api/", "uvicorn", "started server"]):
            return

        # List of inclusion signals relevant to monitoring
        important = [
            "[gemini", "processing section", "cooling", "throttle", "limit",
            "critical", "error", "warning", "fail", "extraction",
            "[info] (", "[paper2ppt]"
        ]

        # Only permit to buffer if contains key identifier
        if any(key in lower_s for key in important):
            ts = time.strftime("[%H:%M:%S]")
            # Cleanup noisy tagging for user aesthetic
            display_txt = clean_s.replace("[GEMINI DEBUG] ", "🧠 ").replace("[INFO] ", "📋 ")
            self.buffer.append(f"{ts} {display_txt}")

    def get_recent(self):
        return list(self.buffer)

    def flush(self):
        self.terminal.flush()

# Replace global streams to capture backend pipeline prints without altering submodules
sys.stdout = LiveLogBuffer(limit=15)
from typing import Dict, Optional
from fastapi import FastAPI, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Direct integration with project pipeline modules
from paper2ppt_cli import generate_slides, normalize_section
from paper2ppt_core.pptx_builder import build_presentation
from ppt_narration_project.main import generate_narrated_ppt
from paper2slides import (
    find_relevant_section,
    explain_section,
    generate_bullets_from_explanation
)

app = FastAPI(
    title="Paper2Slides Core API",
    description="Industrial grade backend for Academic Presentation generation.",
    version="1.0.0"
)

# Enable CORS for smooth interface interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
STORAGE_DIR = os.path.join(os.getcwd(), "api_storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Simple in-memory job tracker for the prototype
JOB_TRACKER: Dict[str, dict] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str
    filename: Optional[str] = None
    error: Optional[str] = None
    logs: Optional[list] = []

def process_pipeline(job_id: str, input_path: str, original_filename: str):
    """Background processing node - detached from web server latency"""
    try:
        JOB_TRACKER[job_id]["status"] = "1_EXTRACTING"
        
        base_output_ppt = os.path.join(STORAGE_DIR, f"{job_id}_base.pptx")
        
        # 1. Generate Presentation Structure
        ppt, slides, sec, title = generate_slides(
            input_pdf=input_path,
            output_ppt=base_output_ppt
        )
        
        JOB_TRACKER[job_id]["status"] = "2_NARRATING"
        
        # 2. Generate & Embed Hidden AI Audio (Long running)
        final_ppt = generate_narrated_ppt(base_output_ppt)
        
        # Rename to clean user output path
        clean_name = f"{os.path.splitext(original_filename)[0]}_presentation.pptx"
        final_dest = os.path.join(STORAGE_DIR, f"{job_id}_final.pptx")
        os.replace(final_ppt, final_dest)
        
        # 3. Finalize state and PRESERVE metadata for post-processing Query Mode
        JOB_TRACKER[job_id].update({
            "status": "COMPLETE",
            "download_filename": clean_name,
            "final_path": final_dest,
            "base_ppt_path": base_output_ppt, # keep for rebuild potential
            "slides_plan": slides,
            "sections": sec,
            "doc_title": title,
            "original_filename": original_filename
        })
        
    except Exception as e:
        JOB_TRACKER[job_id].update({
            "status": "FAILED",
            "error": str(e)
        })
        print(f"[CRITICAL] Pipeline Fatal Error: {str(e)}")

def process_update_task(job_id: str, section_name: str, explanation: str):
    """Isolated background re-generator for interactive Refinement Mode"""
    try:
        j = JOB_TRACKER[job_id]
        j["status"] = "REGENERATING"
        print(f"[UPDATE] Triggering background re-build for section '{section_name}'...")
        
        new_bullets = generate_bullets_from_explanation(explanation)
        if not new_bullets:
            raise Exception("Generated zero bullets from the explanation.")

        slides_plan = j["slides_plan"]
        normalized_target = normalize_section(section_name)
        
        # --- REFINEMENT MATCHING ALGORITHM (Copied from paper2slides core) ---
        updated_indices = []
        for i, slide in enumerate(slides_plan):
            base_title = slide['title'].replace(" (continued)", "")
            if base_title.lower() == normalized_target.lower():
                updated_indices.append(i)
        if not updated_indices:
            keywords = normalized_target.lower().split()
            for i, slide in enumerate(slides_plan):
                if any(k in slide['title'].lower() for k in keywords if len(k) > 3):
                    updated_indices.append(i)
        
        if not updated_indices:
            raise Exception(f"Target mismatch: Slide for '{section_name}' not detected.")
            
        idx = updated_indices[0]
        target_slide = slides_plan[idx]
        base_title = target_slide['title'].replace(" (continued)", "")
        
        # Purge old instances
        new_plan = []
        for i, s in enumerate(slides_plan):
            if s['title'] == base_title or s['title'] == f"{base_title} (continued)":
                continue
            new_plan.append(s)
        
        # Dynamic Expansion
        MAX_PER = 4
        chunks = [new_bullets[i:i+MAX_PER] for i in range(0, len(new_bullets), MAX_PER)]
        new_objs = []
        images = target_slide.get('images', [])
        for c_idx, chunk in enumerate(chunks):
            t = base_title if c_idx == 0 else f"{base_title} (continued)"
            new_objs.append({"title": t, "bullets": chunk, "images": images if c_idx == 0 else []})
        
        # Splice back in
        for s in reversed(new_objs):
            new_plan.insert(idx, s)
        
        j["slides_plan"] = new_plan
        base_path = os.path.join(STORAGE_DIR, f"{job_id}_base.pptx")
        
        # RE-BUILD presentation file
        build_presentation(j["slides_plan"], base_path, j["doc_title"], j["sections"])
        
        j["status"] = "2_NARRATING"
        print(f"[UPDATE] Slides constructed. Commencing re-narration pass.")
        
        # RE-NARRATE
        narrated = generate_narrated_ppt(base_path)
        
        # Replace ultimate destination
        final_dest = j["final_path"]
        if os.path.exists(final_dest):
             os.remove(final_dest)
        os.replace(narrated, final_dest)
        
        j["status"] = "COMPLETE"
        print(f"[UPDATE] ✅ Refinement loop resolved successfully.")
        
    except Exception as e:
        j.update({
            "status": "FAILED",
            "error": f"Refinement Error: {str(e)}"
        })
        print(f"[CRITICAL] Refinement loop aborted: {str(e)}")

@app.post("/api/generate", response_model=JobStatus)
async def create_presentation(file: UploadFile, background_tasks: BackgroundTasks):
    """Accepts PDF and spawns an isolated background processor immediately."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are permitted.")
    
    job_id = str(uuid.uuid4())[:8]
    save_path = os.path.join(STORAGE_DIR, f"{job_id}_in.pdf")
    
    # Stream incoming file directly to local persistent disk
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Register job to queue state
    JOB_TRACKER[job_id] = {
        "status": "QUEUED",
        "filename": file.filename
    }
    
    # Hand-off processing to worker loop so HTTP Response resolves instantly
    background_tasks.add_task(process_pipeline, job_id, save_path, file.filename)
    
    return {"job_id": job_id, "status": "QUEUED", "logs": sys.stdout.get_recent() if hasattr(sys.stdout, 'get_recent') else []}

@app.get("/api/status/{job_id}", response_model=JobStatus)
async def check_status(job_id: str):
    """Query existing task resolution state."""
    if job_id not in JOB_TRACKER:
        raise HTTPException(404, "Job reference not found.")
    
    j = JOB_TRACKER[job_id]
    
    # Fetch recent capture buffer from interceptor
    recent_logs = sys.stdout.get_recent() if hasattr(sys.stdout, 'get_recent') else []
    
    return {
        "job_id": job_id,
        "status": j["status"],
        "filename": j.get("filename"),
        "error": j.get("error"),
        "logs": recent_logs
    }

@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    """Retrieve resulting asset binary upon successful status resolve."""
    if job_id not in JOB_TRACKER or JOB_TRACKER[job_id]["status"] != "COMPLETE":
         raise HTTPException(404, "Requested presentation asset not fully generated yet.")
    
    asset_path = JOB_TRACKER[job_id]["final_path"]
    pretty_name = JOB_TRACKER[job_id]["download_filename"]
    
    return FileResponse(
        path=asset_path, 
        filename=pretty_name, 
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )


# ==========================================
# INTERACTIVE REFINEMENT API ENDPOINTS
# ==========================================

class ChatRequest(BaseModel):
    prompt: str

class UpdateConfirmRequest(BaseModel):
    section_name: str
    explanation: str

@app.post("/api/chat/{job_id}")
async def handle_chat_query(job_id: str, req: ChatRequest):
    """Analyze question, route to relevant section, and return explanation."""
    if job_id not in JOB_TRACKER:
        raise HTTPException(404, "Job session expired or not found.")
        
    j = JOB_TRACKER[job_id]
    if not j.get("sections"):
        raise HTTPException(400, "Section data not available for querying.")

    # 1. Locate pertinent information
    print(f"[CHAT] Searching section for prompt: '{req.prompt}'")
    target_section = find_relevant_section(req.prompt, j["sections"])
    
    if not target_section:
        return {"found": False, "response": "I couldn't locate a highly relevant section for your query. Could you rephrase with a specific section name (e.g., 'Results' or 'Method')?"}

    # 2. Extract Section Metadata
    raw_name = target_section.get('raw_title', target_section.get('title', 'Selected Section'))
    clean_name = re.sub(r'^\s*(?:(?:\d+(?:\.\d+)*)|[IVXLCDM]+|[A-Z])\.?\s+', '', raw_name).strip() or raw_name
    text = target_section.get('text', '')
    
    # 3. Execute generative explanation
    print(f"[CHAT] Mapping query to '{clean_name}'. Requesting LLM Explanation...")
    resp = explain_section(req.prompt, text)
    
    return {
        "found": True,
        "section_name": clean_name,
        "explanation": resp,
        "response": f"**Focusing on '{clean_name}':**\n\n{resp}"
    }

@app.post("/api/update/{job_id}")
async def trigger_slide_refinement(job_id: str, req: UpdateConfirmRequest, background_tasks: BackgroundTasks):
    """Begin background process to reconstruct selected slide node based on chat payload."""
    if job_id not in JOB_TRACKER:
        raise HTTPException(404, "Job not found.")

    # Hand off to non-blocking processor
    background_tasks.add_task(process_update_task, job_id, req.section_name, req.explanation)
    
    return {"status": "SUBMITTED", "message": "Regeneration stack activated."}

# Serve visual interface at base route
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>UI construction in progress</h1>", status_code=200)

# Optionally mount other assets if needed later
# app.mount("/assets", StaticFiles(directory="static"), name="static")
