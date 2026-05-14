import json
import re
from typing import List, Dict, Any
from models.mistral_llm import mistral_generate

def extract_knowledge_nodes(paper_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes an individual paper abstract to extract key Claims, Entities, and Techniques.
    """
    title = paper_metadata.get("title", "Unknown Title")
    abstract = paper_metadata.get("abstract", "")
    
    if not abstract:
        return {"title": title, "claims": [], "entities": []}
        
    prompt = f"""
    [KNOWLEDGE NODE EXTRACTION]
    Paper Title: {title}
    Abstract: {abstract[:1500]}
    
    Task: Analyze this abstract and extract EXACTLY 3 Core Claims and 3 Key Technologies/Entities mentioned.
    Return your response in RIGID JSON format EXACTLY like this:
    {{
      "claims": ["claim 1", "claim 2", "claim 3"],
      "entities": ["entity 1", "entity 2", "entity 3"]
    }}
    
    Return ONLY valid JSON.
    """
    
    try:
        response = mistral_generate(prompt, max_tokens=500)
        # Strip potential markdown wrapping
        cleaned = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        data["title"] = title
        return data
    except Exception as e:
        print(f"[KG ERROR] Node extraction failed for '{title}': {str(e)}")
        return {"title": title, "claims": [], "entities": []}

def build_cross_paper_relations(core_paper: Dict[str, Any], cited_nodes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Identifies specific logical bridges between citations and the core paper.
    (e.g., Paper A builds on Paper B; Paper A competes with Paper C)
    """
    if not cited_nodes:
        return []
        
    context_str = "\n".join([
        f"- Citation: {node.get('title')} | Claims: {', '.join(node.get('claims', []))}"
        for node in cited_nodes
    ])
    
    prompt = f"""
    [CROSS-PAPER KNOWLEDGE GRAPH MAPPER]
    We have a CORE PAPER: "{core_paper.get('title')}"
    Which references the following papers and their claims:
    {context_str[:2000]}
    
    Task: Map exactly one meaningful relationship for each citation relative to the CORE PAPER.
    Relations should be short, e.g., "Uses architecture from", "Improves performance of", "Addresses weakness in".
    
    Return as JSON list of objects:
    [
      {{"source": "Citation Title", "relation": "relationship definition"}}
    ]
    
    Return ONLY valid JSON.
    """
    
    try:
        response = mistral_generate(prompt, max_tokens=1000)
        cleaned = response.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception as e:
        print(f"[KG ERROR] Relationship mapping failed: {str(e)}")
        return []

def construct_knowledge_base(core_title: str, core_abstract: str, citations_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Master Orchestrator for Phase 3: Knowledge Builder.
    Transforms disparate citation feeds into a unified Semantic Knowledge Graph.
    """
    print(f"[PHASE 3] Beginning Construction of Knowledge Graph...")
    
    # 1. Build Core Node
    core_data = {"title": core_title, "abstract": core_abstract}
    core_node = extract_knowledge_nodes(core_data)
    print(f"  ✅ Core Node locked: {len(core_node.get('claims', []))} claims extracted.")
    
    # 2. Build Citation Nodes
    nodes = []
    for meta in citations_metadata:
        print(f"  📥 Distilling knowledge for: '{meta.get('title')[:30]}...'")
        node = extract_knowledge_nodes(meta)
        nodes.append(node)
        
    # 3. Infer Inter-connectivity
    print(f"  🔗 Synthesizing cross-paper topology connections...")
    relations = build_cross_paper_relations(core_data, nodes)
    
    kg = {
        "core_node": core_node,
        "cited_nodes": nodes,
        "relations": relations,
        "stats": {
            "total_nodes": len(nodes) + 1,
            "total_edges": len(relations)
        }
    }
    
    print(f"[PHASE 3] Knowledge Base Construction Sealed.")
    print(f" -> Built {kg['stats']['total_nodes']} nodes with {kg['stats']['total_edges']} logical edges.")
    return kg

if __name__ == "__main__":
    # Simulated Dry Run
    dummy_citations = [
        {"title": "Original BERT paper", "abstract": "We introduce BERT, a language model using transformers."}
    ]
    res = construct_knowledge_base("DistilBERT", "We compress BERT for faster inference.", dummy_citations)
    print("\nFinal KG Topology Result:")
    print(json.dumps(res, indent=2))
