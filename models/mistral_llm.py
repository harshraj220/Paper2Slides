import os
import json
import time
import sys
import boto3 # type: ignore
from botocore.exceptions import ClientError # type: ignore
from botocore.config import Config # type: ignore

def _show_ui_alert(msg, level="error"):
    """Safely push notification to Streamlit frontend if running in web context"""
    if 'streamlit' in sys.modules:
        try:
            import streamlit as st
            if level == "error":
                 st.error(f"🚨 **Bedrock Error:** {msg}")
            elif level == "warning":
                 st.warning(f"⏳ **Bedrock Warning:** {msg}")
        except Exception:
            pass

# ==========================================
# AMAZON BEDROCK INTEGRATION FOR LOAD BALANCING
# ==========================================
_BEDROCK_CLIENT = None
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "mistral.mistral-large-2402-v1:0")

def _get_bedrock_client():
    """Lazily initialize the boto3 bedrock runtime client with adaptive retry configuration."""
    global _BEDROCK_CLIENT
    if _BEDROCK_CLIENT is not None:
        return _BEDROCK_CLIENT

    # Load from .env explicitly if variables are not loaded in system env
    if not os.environ.get("AWS_ACCESS_KEY_ID"):
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(dotenv_path):
            with open(dotenv_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip("'\"")

    try:
        # Configure adaptive retry strategies to prevent immediate throttling failures
        config = Config(
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            retries={
                'max_attempts': 8,
                'mode': 'adaptive'
            },
            connect_timeout=15,
            read_timeout=90
        )
        
        # Explicitly construct client with credentials loaded from environment
        _BEDROCK_CLIENT = boto3.client(
            service_name='bedrock-runtime',
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            config=config
        )
        return _BEDROCK_CLIENT
    except Exception as e:
        print(f"[BEDROCK ERROR] Failed to create Bedrock client: {e}")
        return None

def mistral_generate(prompt: str, max_tokens: int = 72, temperature: float = 0.1) -> str:
    """
    Pipeline hook using Amazon Bedrock API (preserves existing mistral_generate function signature).
    Supports Mistral & Claude dynamic payload formatting.
    Includes intelligent retry mechanisms and dynamic cooling for throttling protection.
    """
    client = _get_bedrock_client()
    if not client:
        _show_ui_alert("Bedrock Client unavailable. Check AWS Credentials in .env", "error")
        return "ERROR: Bedrock Client Unavailable"

    # Load live configuration
    model_id = os.environ.get("BEDROCK_MODEL_ID", BEDROCK_MODEL_ID)
    
    # Setup dynamic payload structures
    is_mistral = "mistral" in model_id.lower()
    
    if is_mistral:
        # Mistral instructs use the prompt template <s>[INST] {prompt} [/INST]
        formatted_prompt = f"<s>[INST] {prompt} [/INST]"
        request_body = {
            "prompt": formatted_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
    else:
        # Claude payload format
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Multi-attempt backoff timing to prevent instant burst throttling
            if attempt > 0:
                wait_seconds = min((2 ** attempt) * 1.5, 30)  # Cap backoff at 30s
                print(f"[BEDROCK DEBUG] Smart cooling activated. Sleeping for {wait_seconds:.2f}s...")
                time.sleep(wait_seconds)

            response = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response.get('body').read())
            
            # Extract parsed text based on model architecture
            if is_mistral:
                # Mistral response schema: {"outputs": [{"text": "...", "stop_reason": "..."}]}
                if "outputs" in response_body and len(response_body["outputs"]) > 0:
                    txt = response_body["outputs"][0].get("text", "").strip()
                else:
                    txt = str(response_body)
            else:
                # Claude response schema: {"content": [{"type": "text", "text": "..."}]}
                if "content" in response_body and len(response_body["content"]) > 0:
                    txt = response_body["content"][0].get("text", "").strip()
                else:
                    txt = str(response_body)

            # Preservation and cleanup filters
            for s in ["Human:", "Assistant:", "System:"]:
                if s in txt:
                    txt = txt.split(s)[0].strip()
            for p in ["Sure,", "Here is", "Here's", "Certainly:"]:
                if txt.startswith(p):
                    txt = txt[len(p):].lstrip(" :,-")

            return txt

        except Exception as e:
            err_str = str(e)
            print(f"[BEDROCK DEBUG] Attempt {attempt + 1}/{max_retries} error: {err_str}")
            
            is_throttle = any(x in err_str.lower() for x in ["throttlingexception", "toomanyrequestsexception"])
            is_auth = any(x in err_str.lower() for x in ["security token", "unrecognizedclientexception", "accessdenied"])
            
            if is_auth:
                _show_ui_alert("AWS Authentication failed. Review Access Key / Secret in .env", "error")
                return "ERROR: AWS Authentication Denied."
                
            if is_throttle:
                if attempt == 0:
                     _show_ui_alert("Capacity limit hit on Bedrock. Smart throttling pipeline dynamically...", "warning")
                
            if attempt == max_retries - 1:
                _show_ui_alert(f"Failed after {max_retries} attempts. Reason: {err_str}", "error")
                return f"ERROR: Max retries exhausted. Last error: {err_str}"

    return "ERROR: Generation failed."
