import os
import re
import json

import json5
import unicodedata
import math
from fuzzywuzzy import fuzz

import math
from collections import deque, defaultdict
from collections import deque
# --- Configuration ---
FUZZY_MATCH_THRESHOLD = 98
MAX_PREVIEW_LINES = 15
MONOTONIC_WINDOW = 20


def normalize_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[‘’]", "'", text)
    return text.strip()


def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [normalize_text(line) for line in f.readlines() if line.strip()]
        return lines
    except FileNotFoundError:
        return []


def best_monotonic_fuzzy_match(target, candidates_map, start_cursor, max_window, threshold):
    best_index, best_score = -1, 0
    min_idx = max(0, start_cursor - 2)
    max_idx = min(len(candidates_map) - 1, start_cursor + max_window)

    for idx in range(min_idx, max_idx + 1):
        if idx in candidates_map:
            score = fuzz.token_sort_ratio(target, candidates_map[idx])
            if score > best_score:
                best_score, best_index = score, idx
            if score >= threshold:
                return best_index, best_score
    return best_index, best_score




def reorder_ladder_final_v3(raw_mappings):
    """
    1. Aggregates Arabic indices that map to the exact same NON-EMPTY English index list.
       Arabic-only lines ([a]:[]) are preserved as individual entries.
    2. Separates Arabic-containing entries from EN-only entries.
    3. Interleaves EN-only lines respecting the Arabic sequence order.
    """

    # --- Step 1: Aggregate Mappings (Conditional) ---

    ar_map = defaultdict(list)
    en_only_lines = []
    individual_ar_only_entries = []

    # Process all raw input lines
    for ar_list, en_list in raw_mappings:
        if ar_list:
            if en_list:
                # Case A: Arabic line with NON-EMPTY English list -> AGGREGATE
                # The EnList (as a tuple) is the key for aggregation.
                en_tuple = tuple(en_list)
                ar_map[en_tuple].extend(ar_list)
            else:
                # Case B: Arabic-only line (en_list is []) -> DO NOT AGGREGATE
                # Preserve as individual entries based on the Arabic index
                for ar_index in ar_list:
                    individual_ar_only_entries.append(([ar_index], []))
        elif en_list:
            # Case C: EN-only line -> Separate and explode
            for e in en_list:
                en_only_lines.append(([], [e]))

    # Combine aggregated and individual Arabic-only entries
    ar_entries = individual_ar_only_entries
    for en_tuple, ar_list in ar_map.items():
        ar_list.sort()  # Ensure the primary index is the smallest
        ar_entries.append((ar_list, list(en_tuple)))

    # --- Step 2 & 3: Sort and Interleave (The Reorder Logic) ---

    # Sort Arabic entries by the first (smallest) Arabic index. This preserves
    # the relative order of the individual Arabic-only lines.
    ar_entries.sort(key=lambda x: x[0][0])

    # Sort EN-only entries by the English index
    en_only = en_only_lines
    en_only.sort(key=lambda x: x[1][0])
    en_only = deque(en_only)

    result = []

    # Pre-calculate the English threshold (anchor) for each Arabic entry.
    ar_en_anchors = []
    next_en_anchor = math.inf
    # We look backwards to find the next meaningful English index
    for _, en_list in reversed(ar_entries):
        if en_list:
            next_en_anchor = min(en_list)
        ar_en_anchors.append(next_en_anchor)
    ar_en_anchors.reverse()

    # Interleave Arabic and EN-only lines
    for i, (ar_list, en_list) in enumerate(ar_entries):

        # The threshold for inserting EN-only lines is the anchor of the current line.
        current_en_threshold = ar_en_anchors[i]

        # Insert EN-only lines whose EN index is STRICTLY LESS THAN the threshold.
        # This is where the interleaving happens: EN-only lines are inserted
        # before the *next* Arabic line that is anchored at or after their index.
        while en_only and en_only[0][1][0] < current_en_threshold:
            result.append(en_only.popleft())

        # Append the Arabic line itself (the anchor)
        result.append((ar_list, en_list))

    # 4. Append remaining EN-only lines at the end
    while en_only:
        result.append(en_only.popleft())

    return result

def reorder_ladder_aggregated(raw_mappings):
    """
    1. Aggregates Arabic indices that map to the exact same English index list.
    2. Separates Arabic-containing entries from EN-only entries.
    3. Interleaves EN-only lines respecting the Arabic sequence order.
    """

    # --- Step 1: Aggregate Mappings ---

    # Note: We use the English list (as a tuple) as the key for aggregation.
    ar_map = defaultdict(list)
    en_only_lines = []

    for ar_list, en_list in raw_mappings:
        if ar_list:
            # Arabic-containing line: Add the Arabic index to the group defined by EnList
            # The EnList must be hashable to be a dictionary key, so convert it to a tuple.
            en_tuple = tuple(en_list)
            # ar_list is a list of single index e.g., [81], [82], etc.
            ar_map[en_tuple].extend(ar_list)
        elif en_list:
            # EN-only line: Keep separate for now, to be handled as single-index EN-only lines
            for e in en_list:
                en_only_lines.append(([], [e]))

    # Convert the aggregated map into the final 'ar_entries' list of (ArList, EnList) tuples
    ar_entries = []
    for en_tuple, ar_list in ar_map.items():
        # Sort the ArList to ensure the primary index is the smallest for sorting
        ar_list.sort()
        ar_entries.append((ar_list, list(en_tuple)))

    # --- Step 2 & 3: Separate, Sort, and Interleave (The Reorder Logic) ---

    # Sort Arabic entries by the first (smallest) Arabic index
    ar_entries.sort(key=lambda x: x[0][0])

    # Sort EN-only entries by the English index
    en_only = en_only_lines
    en_only.sort(key=lambda x: x[1][0])
    en_only = deque(en_only)

    result = []

    # Pre-calculate the English threshold for each Arabic entry.
    ar_en_anchors = []
    next_en_anchor = math.inf
    # Work backwards to find the next meaningful English index
    for _, en_list in reversed(ar_entries):
        if en_list:
            next_en_anchor = min(en_list)
        ar_en_anchors.append(next_en_anchor)
    ar_en_anchors.reverse()

    # Interleave Arabic and EN-only lines using the pre-calculated anchors
    for i, (ar_list, en_list) in enumerate(ar_entries):

        # The threshold for inserting EN-only lines is the EN anchor of the current line.
        current_en_threshold = ar_en_anchors[i]

        # Insert EN-only lines whose EN index is STRICTLY LESS THAN the threshold.
        while en_only and en_only[0][1][0] < current_en_threshold:
            result.append(en_only.popleft())

        # Append the Arabic line itself (the anchor)
        result.append((ar_list, en_list))

    # 4. Append remaining EN-only lines at the end
    while en_only:
        result.append(en_only.popleft())

    return result

def reorder_ladder(ladder_array):
    """
    Final robust reordering:
    - Arabic lines sorted by Arabic index
    - EN-only lines inserted respecting EN index order
    - Arabic-only lines ([a]:[]) must strictly follow the Arabic index order
      and should not be preceded by any EN-only line.
    """
    ar_entries = []
    en_only = []

    # 1. Separate entries
    for ar_list, en_list in ladder_array:
        if ar_list:
            ar_entries.append((ar_list, en_list))
        elif en_list:
            # EN-only lines are exploded into single-entry tuples
            for e in en_list:
                en_only.append(([], [e]))

    # 2. Sort entries
    ar_entries.sort(key=lambda x: x[0][0])
    en_only.sort(key=lambda x: x[1][0])
    en_only = deque(en_only)

    result = []

    for ar_list, en_list in ar_entries:
        # 3. Determine the insertion threshold for EN-only lines

        # Arabic-only lines (en_list is empty) have an infinite threshold,
        # meaning NO EN-only line should jump in front of them.
        if not en_list:
            current_min_en = math.inf
        else:
            # Arabic lines with English content are the anchors.
            # The smallest English index in this line is the threshold.
            current_min_en = min(en_list)

        # 4. Insert preceding EN-only lines (only if they are <= the threshold)
        # We must NOT check against 'inf' (Arabic-only lines)
        if current_min_en != math.inf:
            while en_only and en_only[0][1][0] < current_min_en:
                result.append(en_only.popleft())

        # 5. Append the current Arabic line (the anchor)
        result.append((ar_list, en_list))

    # 6. Append remaining EN-only lines at the end
    while en_only:
        result.append(en_only.popleft())

    return result


def extract_numbers(text):
    return [int(x) for x in re.findall(r'§(\d+)§', text)]

def create_master_ladder_alignment(file_base_name, pairs, source_lines, target_lines):

    ar_lines = source_lines
    en_lines = target_lines

    ar_map = {i: line for i, line in enumerate(ar_lines)}
    en_map = {i: line for i, line in enumerate(en_lines)}

    ar_cursor = 0
    en_cursor = 0
    raw_pairs = []

    for item in pairs:
        ar_nums = extract_numbers(item["Arabic Sentence"])
        en_nums = extract_numbers(item["English Sentence"])
        print(ar_nums, en_nums)
        if ar_nums:
            # map the first Arabic number to all English numbers found in that pair
            raw_pairs.append((ar_nums, en_nums))


    # --- Step 1: Merge all alignments into unique sets ---
    ar_to_en = {}
    en_to_ar = {}

    for ar_list, en_list in raw_pairs:
        for ar_idx in ar_list:
            ar_to_en.setdefault(ar_idx, set()).update(en_list)
        for en_idx in en_list:
            en_to_ar.setdefault(en_idx, set()).update(ar_list)

    total_ar = len(ar_map)
    total_en = len(en_map)

    # --- Step 2: Ensure full coverage ---
    # Every Arabic index should appear at least once
    for i in range(total_ar):
        ar_to_en.setdefault(i, set())
    # Every English index should appear at least once
    for j in range(total_en):
        en_to_ar.setdefault(j, set())

    # --- Step 3: Build clean monotonic ladder ---
    used_ar = set()
    used_en = set()
    ladder_array = []

    ar_i, en_i = 0, 0
    while ar_i < total_ar or en_i < total_en:
        # 3a. If both exist and linked
        if ar_i < total_ar and ar_to_en[ar_i]:
            ens = sorted(list(ar_to_en[ar_i]))
            ladder_array.append(([ar_i], ens))
            used_ar.add(ar_i)
            used_en.update(ens)
            ar_i += 1
        # 3b. If Arabic has no match but still exists
        elif ar_i < total_ar and not ar_to_en[ar_i]:
            ladder_array.append(([ar_i], []))
            used_ar.add(ar_i)
            ar_i += 1
        # 3c. If remaining English not yet used
        elif en_i < total_en and en_i not in used_en:
            ladder_array.append(([], [en_i]))
            used_en.add(en_i)
            en_i += 1
        else:
            ar_i += 1
            en_i += 1

    # --- Step 4: Sort strictly by numeric order of both sides ---
    ladder_array.sort(
        key=lambda p: (p[0][0] if p[0] else math.inf,
                       p[1][0] if p[1] else math.inf)
    )

    # --- Step 5: Remove any accidental duplicates ---
    clean_ladder = []
    seen = set()
    for a, e in ladder_array:
        key = (tuple(a), tuple(e))
        if key not in seen:
            seen.add(key)
            clean_ladder.append((a, e))

    ladder_array = reorder_ladder(clean_ladder)
    ladder_array = reorder_ladder_final_v3(ladder_array)


    return ladder_array




def output_reordered_text(final_reordered_ladder, source_lines, target_lines):
    """
    Maps the indices in the reordered ladder structure to actual text lines,
    prepends the line number (as $no$), and formats the output as a list of tuples.
    """
    output_tuples = []

    for ar_list, en_list in final_reordered_ladder:
        source_text = ""
        target_text = ""

        # --- Handle Arabic (Source) Text ---
        if ar_list:
            # first_ar_index = ar_list[0]
            # Retrieve and combine the actual source texts
            texts = [f"§{i}§ {source_lines[i]}"  for index, i in enumerate(ar_list) if i < len(source_lines)]
            # Format the source text: "$no$ text_1 text_2 ..."
            source_text = f" {' '.join(texts)}"

        if en_list:
            texts = [f"§{i}§ {target_lines[i]}"  for index, i in enumerate(en_list) if i < len(target_lines)]

            # Format the target text: "$no$ text_1 text_2 ..."
            target_text = f" {' '.join(texts)}"

        output_tuples.append((source_text, target_text))

    return output_tuples

