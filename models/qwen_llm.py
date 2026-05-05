import os
import requests
import json

# Fetch API key from environment
# We use OpenRouter because they offer Qwen 2.5 7B completely for FREE
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

def qwen_generate(prompt: str, max_tokens: int = 72, temperature: float = 0.1) -> str:
    """
    Generate text using Qwen via OpenRouter's free API.
    """
    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY is not set. Please set it in your environment or Streamlit secrets.")
        return "ERROR: OPENROUTER_API_KEY is not set. Please set it to use the AI features."

    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/harshraj220/Paper2Slides",
        "X-Title": "Paper2Slides",
        "Content-Type": "application/json"
    }
    
    data = {
        # This specific model string uses OpenRouter's free tier
        "model": "qwen/qwen-2.5-7b-instruct:free",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.8,
        "repetition_penalty": 1.1
    }
    
    import time
    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            text = result["choices"][0]["message"]["content"].strip()
            
            # --- HARD STOP: remove chat / role leakage ---
            for stop in ["Human:", "Assistant:", "System:"]:
                if stop in text:
                    text = text.split(stop)[0].strip()

            # Remove leading meta phrases
            for prefix in ["Sure,", "Here is", "Here's", "Here’s"]:
                if text.startswith(prefix):
                    text = text[len(prefix):].lstrip(" :,-")
                    
            return text
        
        except Exception as e:
            print(f"API Error (Attempt {attempt+1}): {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"Response: {response.text}")
            if attempt == 2:
                raise Exception(f"OpenRouter API failed after 3 attempts: {str(e)}")
            time.sleep(2)
    return ""
