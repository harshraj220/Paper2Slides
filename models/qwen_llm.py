import os
import requests
import json
import time
import sys

def _show_ui_alert(msg, level="error"):
    """Safely push notification to Streamlit frontend if running in web context"""
    if 'streamlit' in sys.modules:
        try:
            import streamlit as st
            if level == "error":
                 st.error(f"🚨 **Gemini Error:** {msg}")
            elif level == "warning":
                 st.warning(f"⏳ **Gemini Warning:** {msg}")
        except Exception:
            pass

from itertools import cycle

RAW_KEY_STR = os.getenv("GEMINI_API_KEY", "")

# Dynamic File Ingestion Hook
if not RAW_KEY_STR:
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(dotenv_path):
        with open(dotenv_path, "r") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    RAW_KEY_STR = line.strip().split("=", 1)[1].strip("'\" ")
                    break

# Construct Cyclical Round-Robin Pool
KEY_LIST = [k.strip() for k in RAW_KEY_STR.split(",") if k.strip()]
KEY_POOL = cycle(KEY_LIST) if KEY_LIST else None

def qwen_generate(prompt: str, max_tokens: int = 72, temperature: float = 0.1) -> str:
    """
    Proprietary pipeline hook transparently using Google Gemini.
    Kept identical naming to preserve existing runtime workflows.
    
    ENHANCED: Automatically load-balances and rotates across 
    multiple pooled keys if supplied in .env.
    """
    if not KEY_POOL:
        print("CRITICAL: No valid keys found in GEMINI_API_KEY pool.")
        return "ERROR: Key Missing."

    # Setup request structure (Dynamic injection inside loop)
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature
        }
    }

    # Failover and Multi-Key Traversal Logic
    for i in range(len(KEY_LIST) * 2 if len(KEY_LIST) > 1 else 4):
        try:
            active_key = next(KEY_POOL)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={active_key}"
            
            res = requests.post(url, headers=headers, json=payload, timeout=45)
            if res.status_code == 429:
                 raise Exception("Hit Gemini Rate limit")
            res.raise_for_status()
            
            out = res.json()
            txt = out["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Preservation filters
            for s in ["Human:", "Assistant:", "System:"]:
                if s in txt: txt = txt.split(s)[0].strip()
            for p in ["Sure,", "Here is", "Here's", "Certainly:"]:
                if txt.startswith(p): txt = txt[len(p):].lstrip(" :,-")
            
            return txt
        except Exception as e:
            err_str = str(e)
            print(f"[GEMINI DEBUG] Attempt {i+1} error: {err_str}")
            
            # ⚡ INTELLIGENT DYNAMIC COOLING ALGORITHM ⚡
            wait_seconds = (2**i) * 1.5 # Default Backoff
            
            # Inspect raw response to extract Exact Restrict Timers
            if 'res' in locals() and hasattr(res, 'text') and res.status_code == 429:
                 import re
                 # Extract numeric seconds dynamically from the Google API's suggested cooldown string
                 time_match = re.search(r"retry\s+in\s+([\d.]+)(s|ms)", res.text)
                 if time_match:
                     raw_time = float(time_match.group(1))
                     unit = time_match.group(2)
                     calc_time = raw_time if unit == "s" else (raw_time / 1000.0)
                     
                     # Add 1.5s Safety Padding to ensure backend timer registration syncs
                     wait_seconds = calc_time + 1.5
                     print(f"[GEMINI DEBUG] Dynamic Smart-Throttle triggered. Hard cooling for {wait_seconds:.2f}s...")
            
            # Dynamic UI Updates based on context
            if "429" in err_str or "limit" in err_str.lower():
                if i == 0:
                    _show_ui_alert(f"Capacity saturated. Smart-throttling pipeline for {wait_seconds:.1f}s automatically...", "warning")
            elif "403" in err_str or "permission" in err_str.lower():
                 _show_ui_alert("Permission Denied. Verify your API key validity.", "error")

            if 'res' in locals() and hasattr(res, 'text'):
                 print(f"[GEMINI DEBUG] Raw Response: {res.text[:500]}")
                 
            if i == 3 or i == (len(KEY_LIST) * 2) - 1: 
                print("[GEMINI DEBUG] Exhausted all retries and alternative keys.")
                _show_ui_alert(f"All available API keys were exhausted. (Last: {err_str})", "error")
                break
            
            # Direct Injection of Dynamic Delay
            time.sleep(wait_seconds)
            
    return ""
