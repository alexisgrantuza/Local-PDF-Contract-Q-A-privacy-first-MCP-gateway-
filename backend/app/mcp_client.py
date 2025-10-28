import os, requests
import time

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

# Recommended free models for Q&A tasks:
# - "google/flan-t5-small" (default, good for short answers)
# - "google/flan-t5-base" (better quality, slightly slower)
# - "microsoft/DialoGPT-small" (conversational)
# - "facebook/blenderbot-400M-distill" (conversational)

def mcp_generate(prompt: str):
    """Generate text using Hugging Face Inference API"""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "do_sample": True
        }
    }
    
    try:
        r = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        out = r.json()
        
        if isinstance(out, dict) and "error" in out:
            print(f"HF API Error: {out['error']}")
            return {"text": "I don't know."}
        
        if isinstance(out, list) and len(out) > 0:
            # return a list with generated_text
            if isinstance(out[0], dict) and "generated_text" in out[0]:
                return {"text": out[0]["generated_text"]}
            else:
                return {"text": str(out[0])}
        
        return {"text": str(out)}
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {"text": "I don't know."}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"text": "I don't know."}
