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
st.set_page_config(page_title="Paper2Slides AI", layout="wide", page_icon="📄")

st.markdown("""
    <style>
    /* CSS for premium look */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stButton>button {
        border-radius: 8px;
        transition: 0.3s;
        border: 1px solid #38bdf8;
    }
    .stButton>button:hover {
        background-color: #38bdf8;
        color: white;
    }
    .stChatMessage {
        background-color: rgba(30, 41, 59, 0.7);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📄 Paper2Slides AI")
st.markdown("Convert research papers into **automated presentation slides** with hidden audio narration.")

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
    st.info("👈 Upload a PDF on the sidebar to get started.")
