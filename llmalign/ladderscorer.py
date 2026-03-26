#
# # --- MAIN EXECUTION ---
import json
import os

import json5

from llmalign.eval import read_alignments, score_multiple, log_final_scores

from llmalign.ladderconverter import normalize_text, create_master_ladder_alignment, read_file

test_alignments = []
gold_alignments = []
file_names = []

category = "law"
folder_path_ar = f"llmalignresults/{category}/gemini"
output_dir = "llmladder"
os.makedirs(output_dir, exist_ok=True)

processed_files = [f for f in os.listdir(folder_path_ar)]
print(f"Starting alignment for {len(processed_files)} file(s)...")
src_dir = f'../golddataset/{category}/ar'
tgt_dir = f'../golddataset/{category}/en'
gold_dir = f'../golddataset/{category}/gold'
ladder_output = []
for fname in processed_files:
    print("evaluating ", fname)
    ladder_path = os.path.join(folder_path_ar, fname)
    src_path = os.path.join(src_dir, fname)
    tgt_path = os.path.join(tgt_dir, fname)
    source_list = read_file(src_path)
    target_list = read_file(tgt_path)
    with open(ladder_path, 'r', encoding='utf-8') as f:
        pairs = json5.load(f)
    test_align = create_master_ladder_alignment(fname, pairs, source_list, target_list)
    gold_file = os.path.join(gold_dir, fname)
    gold_align = read_alignments(gold_file)

    # Score this individual file
    file_score = score_multiple(gold_list=[gold_align], test_list=[test_align])
    print(f"Scores for {fname}:")
    log_final_scores(file_score)  # This logs per-file scores

    # Store for overall scoring (optional)
    test_alignments.append(test_align)
    gold_alignments.append(gold_align)
    file_names.append(fname)

# Optional: Final overall score across all files
print("\n=== Overall Scores ===")
overall_scores = score_multiple(gold_list=gold_alignments, test_list=test_alignments)
log_final_scores(overall_scores)

