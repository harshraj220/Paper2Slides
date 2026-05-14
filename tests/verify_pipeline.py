import sys
import os

# Add models directory to path context
sys.path.append('/home/harsh/Paper2Slides')

from models.mistral_llm import mistral_generate, KEY_LIST

print("=== VALIDATING MULTI-KEY PIPELINE ===")
print(f"Keys found in pool: {len(KEY_LIST)}")

print("\n--- Firing Test Request 1 ---")
r1 = mistral_generate("Count 1 to 3")
print(f"Response 1 snippet: {r1[:40]}")

print("\n--- Firing Test Request 2 ---")
r2 = mistral_generate("Count 4 to 6")
print(f"Response 2 snippet: {r2[:40]}")

print("\n=== PIPELINE CONFIRMED OPERATIONAL ===")
