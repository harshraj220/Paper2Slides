"""
Batch Evaluation — Runs evaluate_pipeline on all PDF+PPTX pairs found in the directory.
Outputs a combined comparison table.
"""
import os
import json
import sys

sys.path.append(os.getcwd())
from eval.evaluate_slides import evaluate_pipeline

# PDF -> PPTX pairs (auto-detected)
pairs = []
for fname in sorted(os.listdir(".")):
    if fname.endswith(".pdf") and fname not in {"paper1.pdf", "paper2.pdf", "paper3.pdf"}:
        base = os.path.splitext(fname)[0]
        pptx = f"{base}_summary_with_narration.pptx"
        if os.path.exists(pptx):
            pairs.append((fname, pptx))

print(f"\nFound {len(pairs)} PDF+PPTX pairs to evaluate:\n")
for pdf, pptx in pairs:
    print(f"  {pdf}  →  {pptx}")

print("\n" + "="*70)

all_results = []

for pdf, pptx in pairs:
    print(f"\n>>> Evaluating: {pdf}")
    report_file = f"eval/eval_{os.path.splitext(pdf)[0]}.json"
    try:
        evaluate_pipeline(pdf, pptx, output_json=report_file)
        with open(report_file) as f:
            report = json.load(f)
        scores = report["overall_scores"]
        all_results.append({
            "paper": pdf,
            "structure_alignment": scores["structure_alignment_score"],
            "semantic_fidelity": scores["semantic_fidelity_score"],
            "rouge_l": scores["lexical_overlap_score_rougel"],
            "weighted_score": scores["overall_weighted_score"],
            "classification": scores["overall_classification"],
            "narration_grade": scores["avg_narration_readability_grade"],
        })
    except Exception as e:
        print(f"[ERROR] Failed for {pdf}: {e}")
        all_results.append({
            "paper": pdf,
            "structure_alignment": "ERROR",
            "semantic_fidelity": "ERROR",
            "rouge_l": "ERROR",
            "weighted_score": "ERROR",
            "classification": "ERROR",
            "narration_grade": "ERROR",
        })

# ---- Print Summary Table ----
print("\n\n" + "="*90)
print("                        BATCH EVALUATION SUMMARY TABLE")
print("="*90)
header = f"{'Paper':<45} {'Align%':>7} {'Semantic':>9} {'ROUGE-L':>8} {'Score':>7} {'Class':>7} {'Narr.Grade':>11}"
print(header)
print("-"*108)
valid_aligns = []
valid_semantics = []
valid_rouges = []
valid_weights = []

for r in all_results:
    name = r["paper"][:43]
    align = r["structure_alignment"]
    sem   = r["semantic_fidelity"]
    rouge = r["rouge_l"]
    weight = r["weighted_score"]
    cls = r["classification"]
    grade = r["narration_grade"]

    align_str = f"{float(align)*100:.0f}%" if align != "ERROR" else "ERR"
    sem_str   = f"{float(sem):.3f}"        if sem   != "ERROR" else "ERR"
    rouge_str = f"{float(rouge):.4f}"      if rouge != "ERROR" else "ERR"
    weight_str = f"{float(weight):.3f}"    if weight != "ERROR" else "ERR"
    grade_str = f"{float(grade):.1f}"      if grade != "ERROR" else "ERR"

    print(f"{name:<45} {align_str:>7} {sem_str:>9} {rouge_str:>8} {weight_str:>7} {cls:>7} {grade_str:>11}")

    if align != "ERROR":
        valid_aligns.append(float(align))
        valid_semantics.append(float(sem))
        valid_rouges.append(float(rouge))
        valid_weights.append(float(weight))

print("-"*108)
if valid_aligns:
    avg_w = sum(valid_weights)/len(valid_weights)
    if avg_w >= 0.50:
        avg_cls = "Good"
    elif avg_w >= 0.30:
        avg_cls = "Average"
    else:
        avg_cls = "Poor"

    print(f"{'AVERAGE':<45} {sum(valid_aligns)/len(valid_aligns)*100:>6.1f}% "
          f"{sum(valid_semantics)/len(valid_semantics):>9.3f} "
          f"{sum(valid_rouges)/len(valid_rouges):>8.4f} "
          f"{avg_w:>7.3f} {avg_cls:>7}")
print("="*108)

print("""
METRIC GUIDE:
  Align%       — % of slides whose content was matched back to a PDF section (structure)
  Semantic     — Embedding cosine similarity: content fidelity (0=none, 1=perfect)
  ROUGE-L      — Lexical overlap between slide text and source section (0=none, 1=perfect)
  Score        — Weighted score using Structure (10%), ROUGE (10%), and Semantic (80%)
  Narr.Grade   — Flesch-Kincaid grade level of narration (8-12 is ideal for presentations)
""")

# Save combined report
combined_path = "eval/batch_eval_report.json"
with open(combined_path, "w") as f:
    json.dump(all_results, f, indent=2)
print(f"Combined report saved to: {combined_path}")
