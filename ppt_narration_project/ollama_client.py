import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def ollama_generate(prompt, model="phi3"):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.05,
            "num_ctx": 2048
        }
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()

    

    return response.json()["response"].strip()


