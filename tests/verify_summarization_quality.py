import os
from paper2ppt_cli import summarize_section_with_mistral

# 1. Setup Mock Paper Excerpt (Highly Representative)
mock_intro_text = """
Recurrent neural networks, long short-term memory and gated recurrent neural networks in particular, have been firmly established as state of the art approaches in sequence modeling. However, recurrent models are inherently sequential, precluding parallelization within training examples. 
Attention mechanisms have become an integral part of compelling sequence modeling and transduction models.
We propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output. 
"""

# 2. Setup Mock Knowledge Base (Synthesized from Phase 3 earlier)
mock_kb = {
    "cited_nodes": [
        {
            "title": "Neural Machine Translation with Attention",
            "claims": ["introduces soft-attention", "improves sequence alignment"]
        },
        {
            "title": "Gated Recurrent Units",
            "claims": ["simplifies memory cells", "still acts sequentially"]
        }
    ],
    "relations": [
        {
            "source": "Neural Machine Translation with Attention",
            "relation": "Transformer removes the base recurrence used alongside this attention."
        }
    ]
}

def run_head_to_head():
    print("🔍 STARTING HEAD-TO-HEAD COMPARISON TEST...")
    print("="*60)
    
    # PASS 1: Without Enriched Knowledge Base
    print("\n🚀 MODE A: LEGACY GENERATOR (Basic Text Extraction)")
    print("-" * 40)
    res_legacy = summarize_section_with_mistral("Introduction", mock_intro_text, 2, knowledge_base=None)
    for b in res_legacy:
        print(b)

    print("\n🚀 MODE B: NEW ENRICHED GENERATOR (With Knowledge Graph context)")
    print("-" * 40)
    res_enriched = summarize_section_with_mistral("Introduction", mock_intro_text, 2, knowledge_base=mock_kb)
    for b in res_enriched:
        print(b)

    print("\n" + "="*60)
    print("🧪 TEST COMPLETE. Check output above to compare authoritarian scope and context saturation.")

if __name__ == "__main__":
    run_head_to_head()
