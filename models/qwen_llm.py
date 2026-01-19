import os
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
from typing import Optional, cast

# pyright: reportMissingImports=false

import torch 

from transformers import (        

    AutoTokenizer,
    AutoModelForCausalLM,
    PreTrainedTokenizerBase,
    PreTrainedModel,
)

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

# Global singletons
_tokenizer: Optional[PreTrainedTokenizerBase] = None
_model: Optional[PreTrainedModel] = None


def _lazy_load() -> None:
    """
    Load tokenizer and model exactly once.
    """
    global _tokenizer, _model

    if _tokenizer is not None and _model is not None:
        return

    print("[QWEN] Loading tokenizer and model (one-time)...")

    _tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        trust_remote_code=True,
    )

    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        device_map="auto",
        torch_dtype=torch.float16,
        load_in_8bit=True,
        trust_remote_code=True,
    )

    assert _model is not None
    _model.eval()



def qwen_generate(prompt: str, max_tokens: int = 72) -> str:
    global _tokenizer, _model

    _lazy_load()

    assert _tokenizer is not None
    assert _model is not None

    tokenizer = cast(PreTrainedTokenizerBase, _tokenizer)
    model = cast(PreTrainedModel, _model)

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048,
    ).to(model.device)

    with torch.no_grad():
        input_ids = inputs["input_ids"]
        attention_mask = inputs.get("attention_mask")

        outputs = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=max_tokens,
        temperature=0.1,      # narration = low creativity
        top_p=0.8,
        do_sample=True,
        eos_token_id=model.config.eos_token_id,
    )



    generated_ids = outputs[0][input_ids.shape[-1]:]
    text = tokenizer.decode(
        generated_ids,
        skip_special_tokens=True,
    ).strip()

    # --- HARD STOP: remove chat / role leakage ---
    for stop in ["Human:", "Assistant:", "System:"]:
        if stop in text:
            text = text.split(stop)[0].strip()

    # Remove leading meta phrases
    for prefix in [
        "Sure,",
        "Here is",
        "Here's",
        "Here’s",
    ]:
        if text.startswith(prefix):
            text = text[len(prefix):].lstrip(" :,-")

    return text


  
