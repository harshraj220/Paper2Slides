import os
import re
import tempfile
import streamlit as st

from paper2ppt_cli import generate_slides, normalize_section
from paper2ppt_core.pptx_builder import build_presentation
from ppt_narration_project.main import generate_narrated_ppt
from paper2slides import (
    find_relevant_section,
    explain_section,
    generate_bullets_from_explanation
)

# Configuration for page
st.set_page_config(
    page_title="Paper2Slides AI Pro", 
    layout="wide", 
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# PREMIUM UI INJECTION SYSTEM
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Core App Overrides */
    .stApp {
        background: radial-gradient(circle at 0% 0%, #1e1e2e 0%, #0f111a 100%);
        background-attachment: fixed;
        font-family: 'Outfit', system-ui, -apple-system, sans-serif;
    }
    
    /* Fonts */
    html, body, [class*="css"]  {
        font-family: 'Outfit', sans-serif;
    }
    
    /* High-End H1 Design */
    h1 {
        background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 3rem !important;
        letter-spacing: -0.03em !important;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: rgba(17, 24, 39, 0.8);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
    }

    /* Input/Uploader Area styling */
    [data-testid="stFileUploadDropzone"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 2px dashed rgba(99, 102, 241, 0.4) !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        transition: 0.3s ease;
    }
    
    [data-testid="stFileUploadDropzone"]:hover {
        background: rgba(99, 102, 241, 0.05) !important;
        border-color: #6366f1 !important;
    }

    /* Primary Action Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.2) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 25px -5px rgba(99, 102, 241, 0.4) !important;
    }

    /* Download specific button logic */
    [data-testid="stDownloadButton"] > button {
         background: linear-gradient(90deg, #10b981 0%, #059669 100%) !important;
         box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.2) !important;
    }

    /* Chat Message Blocks */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(8px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        margin-bottom: 1rem !important;
    }
    
    .stChatMessage[data-testid="stChatMessageUser"] {
         background: rgba(99, 102, 241, 0.1) !important;
         border: 1px solid rgba(99, 102, 241, 0.2) !important;
    }

    /* Expanding slide details */
    .stExpander {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
    }

    /* Badge/Pill tags for UI flow */
    .hero-badge {
        display: inline-flex;
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(168, 85, 247, 0.3);
        margin-bottom: 1rem;
    }
    
    </style>
""", unsafe_allow_html=True)

# Render Hero Structure
st.markdown('<span class="hero-badge">⚡ NEXT-GEN AI ARCHITECTURE</span>', unsafe_allow_html=True)
st.title("Paper2Slides Pro")
st.markdown("### Deep extraction & real-time intelligent synthesis for academic PDF workflows.")
st.divider()

# State initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "slides_plan" not in st.session_state:
    st.session_state.slides_plan = None
if "sections" not in st.session_state:
    st.session_state.sections = None
if "doc_title" not in st.session_state:
    st.session_state.doc_title = None
if "final_ppt_path" not in st.session_state:
    st.session_state.final_ppt_path = None
if "base_ppt_path" not in st.session_state:
    st.session_state.base_ppt_path = "output.pptx"
if "pending_update" not in st.session_state:
    st.session_state.pending_update = None

# Sidebar for Upload
with st.sidebar:
    st.header("Upload Paper")
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    
    if uploaded_file is not None and st.session_state.slides_plan is None:
        if st.button("Generate Presentation"):
            with st.spinner("Processing PDF and generating slides..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                try:
                    ppt, slides_plan, sections, doc_title = generate_slides(
                        input_pdf=tmp_path,
                        output_ppt=st.session_state.base_ppt_path,
                        max_bullets=5
                    )
                    
                    st.session_state.slides_plan = slides_plan
                    st.session_state.sections = sections
                    st.session_state.doc_title = doc_title
                    
                    st.info("Adding AI voice narration... this may take some time.")
                    narrated = generate_narrated_ppt(st.session_state.base_ppt_path)
                    
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    final_path = f"{base_name}_summary_with_narration.pptx"
                    if os.path.exists(final_path):
                        os.remove(final_path)
                    os.replace(narrated, final_path)
                    
                    st.session_state.final_ppt_path = final_path
                    st.success("✅ Presentation generated successfully!")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "I've generated the base presentation! Feel free to ask me to explain any section, and we can interactively update the slides."
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during generation: {e}")

    if st.session_state.final_ppt_path and os.path.exists(st.session_state.final_ppt_path):
        st.divider()
        st.success("Your presentation is ready!")
        with open(st.session_state.final_ppt_path, "rb") as file:
            btn = st.download_button(
                label="📥 Download Presentation",
                data=file,
                file_name=os.path.basename(st.session_state.final_ppt_path),
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )

# Main UI Area
if st.session_state.slides_plan is not None:
    st.subheader("Interactive Update Mode")
    
    with st.expander("👀 View Current Slides Plan"):
        for i, slide in enumerate(st.session_state.slides_plan):
            st.markdown(f"**{i+1}. {slide['title']}**")
    
    # Render chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Handle pending update approval
    if st.session_state.pending_update:
        st.warning("Do you want to update the presentation slides with this new explanation?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Update Slides", use_container_width=True):
                update_info = st.session_state.pending_update
                st.session_state.pending_update = None
                
                with st.spinner("Regenerating slides & narration..."):
                    new_bullets = generate_bullets_from_explanation(update_info["explanation"])
                    section_name = update_info["section_name"]
                    
                    if not new_bullets:
                        st.error("Could not generate bullets.")
                    else:
                        normalized_target = normalize_section(section_name)
                        updated_indices = []
                        for i, slide in enumerate(st.session_state.slides_plan):
                            base_title = slide['title'].replace(" (continued)", "")
                            if base_title.lower() == normalized_target.lower():
                                updated_indices.append(i)
                        
                        if not updated_indices:
                            keywords = normalized_target.lower().split()
                            for i, slide in enumerate(st.session_state.slides_plan):
                                if any(k in slide['title'].lower() for k in keywords if len(k) > 3):
                                    updated_indices.append(i)
                        
                        if not updated_indices:
                            raw = section_name.lower()
                            for i, slide in enumerate(st.session_state.slides_plan):
                                if slide['title'].lower() in raw or raw in slide['title'].lower():
                                    updated_indices.append(i)
                                    
                        if updated_indices:
                            idx = updated_indices[0]
                            target_slide = st.session_state.slides_plan[idx]
                            base_title = target_slide['title'].replace(" (continued)", "")
                            
                            # Clean up old slides with same title
                            new_plan = []
                            for i, s in enumerate(st.session_state.slides_plan):
                                if s['title'] == base_title or s['title'] == f"{base_title} (continued)":
                                    continue
                                new_plan.append(s)
                            
                            # Expand into multiple slides if long (max 4 per slide)
                            chunks = [new_bullets[i:i + 4] for i in range(0, len(new_bullets), 4)]
                            new_slides_objects = []
                            original_images = target_slide.get('images', [])
                            
                            for c_idx, chunk in enumerate(chunks):
                                title = base_title if c_idx == 0 else f"{base_title} (continued)"
                                new_slides_objects.append({
                                    "title": title,
                                    "bullets": chunk,
                                    "images": original_images if c_idx == 0 else [] 
                                })
                            
                            for s in reversed(new_slides_objects):
                                new_plan.insert(idx, s)
                                
                            st.session_state.slides_plan = new_plan
                            
                            # Rebuild and Narrate
                            build_presentation(st.session_state.slides_plan, st.session_state.base_ppt_path, st.session_state.doc_title, st.session_state.sections)
                            new_narrated = generate_narrated_ppt(st.session_state.base_ppt_path)
                            
                            if os.path.exists(st.session_state.final_ppt_path):
                                os.remove(st.session_state.final_ppt_path)
                            os.replace(new_narrated, st.session_state.final_ppt_path)
                            
                            msg = f"✅ Updated slides for '{section_name}' successfully! You can download the new version from the sidebar."
                            st.session_state.messages.append({"role": "assistant", "content": msg})
                            st.rerun()
                        else:
                            st.error(f"Could not match the section '{section_name}' to an existing slide.")
        with col2:
            if st.button("No, Skip", use_container_width=True):
                st.session_state.pending_update = None
                st.session_state.messages.append({"role": "assistant", "content": "Skipped update. What else would you like to explore?"})
                st.rerun()

    # Chat Input for queries
    if not st.session_state.pending_update:
        if query := st.chat_input("Ask a question about a section to refine it..."):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
                
            with st.chat_message("assistant"):
                with st.spinner("Finding relevant section and analyzing..."):
                    target_section = find_relevant_section(query, st.session_state.sections)
                    
                    if not target_section:
                        response_msg = "I couldn't identify a relevant section. Please try rephrasing."
                        st.markdown(response_msg)
                        st.session_state.messages.append({"role": "assistant", "content": response_msg})
                    else:
                        raw_section_name = target_section.get('raw_title', target_section.get('title', 'Unknown'))
                        section_name = re.sub(r'^\s*(?:(?:\d+(?:\.\d+)*)|[IVXLCDM]+|[A-Z])\.?\s+', '', raw_section_name).strip() or raw_section_name
                        
                        st.markdown(f"**Found relevant section:** `{section_name}`")
                        
                        explanation = explain_section(query, target_section.get('text', ''))
                        st.markdown(explanation)
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": f"**Section:** `{section_name}`\n\n{explanation}"
                        })
                        
                        st.session_state.pending_update = {
                            "section_name": section_name,
                            "explanation": explanation
                        }
                        st.rerun()
else:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03); padding:1.5rem; border-radius:16px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="margin-top:0; color:#818cf8;">📄 Smart Extraction</h4>
            <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:0;">Auto-identifies methodology, results, and complex tables directly from dense academic PDFs.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03); padding:1.5rem; border-radius:16px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="margin-top:0; color:#c084fc;">🧠 Gemini Synthesis</h4>
            <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:0;">Leverages Gemini-3 advanced logic to abstract deep insights into distinct slide narratives.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03); padding:1.5rem; border-radius:16px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="margin-top:0; color:#38bdf8;">🗣️ Audio Integration</h4>
            <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:0;">Automatically generates and embeds hidden neural TTS speaker notes into your file.</p>
        </div>
        """, unsafe_allow_html=True)

    st.info("💡 **Ready to begin?** Drag and drop your research paper PDF into the sidebar on the left!")
