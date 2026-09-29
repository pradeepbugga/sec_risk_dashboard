

import re
import json
from chunk.extract_dom_slice import extract_dom_slice
from lxml import html, etree
import os
from chunk.blocks import get_block_nodes, slice_blocks, compute_body_font, compute_body_weight
from chunk.blocks import build_text_frequency, compute_body_color, normalize_color
from chunk.blocks import apply_font_relative_features, apply_colored_leadin_split
from chunk.blocks import merge_table_bullets, normalize_boundary_page_numbers
from chunk.blocks import remove_page_boundary_noise, merge_page_break_splits
from chunk.blocks import merge_same_row_table_headers, use_score_blocks, add_context_scores
from chunk.blocks import infer_color_from_candidates, is_candidate_header
from chunk.heading_clustering import cluster_heading_styles
import unicodedata
from sklearn.preprocessing import StandardScaler
from chunk.color_utils import color_distance
from chunk.capital_feature_utils import is_title_case
from chunk.risk_heading_utils import find_risk_factor_heading, normalize_heading_text
import numpy as np
from chunk.blocks import make_serializable



if __name__ == "__main__":

    ticker = 'MU'
    year = 2025

    html_path = f"./data/10K_Filings/raw/{ticker}/{year}.html"
    
    json_path = f"./data/processed_with_nodes/{ticker}/{year}.json"
    with open(json_path, "r") as f:
        data = json.load(f)

    print("Loaded config for", data["company"], data["year"])

    start_xpath = data["sections"]["risk_factors"]["start_node"]
    stop_xpath = data["sections"]["risk_factors"]["stop_node"]
    

    slice_nodes = extract_dom_slice(html_path, start_xpath, stop_xpath)

    #print(len(slice_nodes), "nodes extracted in slice")

   
    blocks = get_block_nodes(slice_nodes)
   
    #print(len(blocks), "initial blocks extracted")
    
    feature_blocks = slice_blocks(blocks)
    
    #print(len(feature_blocks), "initial feature blocks extracted")
       
    computed_body_font = compute_body_font(feature_blocks)

    #print("Computed body font size:", computed_body_font)

    body_weight = compute_body_weight(feature_blocks)

    #print("Computed body font weight:", body_weight)

    freq_map = build_text_frequency(feature_blocks)
    body_color = compute_body_color(feature_blocks) 
    body_color = normalize_color(body_color)
    
    print("Computed body color:", body_color)
    
    feature_blocks = apply_font_relative_features(feature_blocks, computed_body_font)
    
    feature_blocks = apply_colored_leadin_split(feature_blocks, body_color)
    bullet_merge = merge_table_bullets(feature_blocks)

    normalized_blocks = normalize_boundary_page_numbers(bullet_merge)
    feature_blocks = remove_page_boundary_noise(normalized_blocks)

    merged_blocks = merge_page_break_splits(feature_blocks)
    merged_blocks = merge_same_row_table_headers(merged_blocks)

    scored_blocks = use_score_blocks(merged_blocks, body_color=body_color, color_is_structural=False)
    
    scored_blocks = add_context_scores(scored_blocks)

    # Detect structural color
    color_is_structural = infer_color_from_candidates(scored_blocks, body_color)
    
    if color_is_structural:
        print("Color is structural, rescoring blocks")
        scored_blocks = use_score_blocks(merged_blocks, body_color=body_color, color_is_structural=True)
        scored_blocks = add_context_scores(scored_blocks)

    for b in scored_blocks:
        b["candidate_header"] = is_candidate_header(b)


    headings = [
        b for b in scored_blocks
        if b["candidate_header"]
    ]

    print("labels", cluster_heading_styles(headings, body_color))

   
    
   



    risk_factors_index = find_risk_factor_heading(headings)

# we will now slice the headings to only include those from risk factors onward 
def slice_to_risk_factors(headings):
    new_headings = []
    index = find_risk_factor_heading(headings)
    for i, h in enumerate(headings):
        if i >= index+1:
            new_headings.append(h)
    return new_headings



def generate_cluster(headings, labels):
    cluster_map = {}
    for heading, label in zip(headings, labels):
        if label not in cluster_map:
            cluster_map[label] = []
        cluster_map[label].append(heading)
    return cluster_map

new_headings = slice_to_risk_factors(headings)
new_labels = cluster_heading_styles(new_headings, body_color)

# Attach cluster labels to headings
for h, lbl in zip(new_headings, new_labels):
    h["cluster_label"] = lbl

cluster_map = generate_cluster(new_headings, new_labels)

def mean_word_count_clusters(cluster_map):
    mean_wc = {}
    for label, headings in cluster_map.items():
        total_wc = sum(len(h["text"].split()) for h in headings)
        mean_wc[label] = total_wc / len(headings)
    return mean_wc


mean_wc = mean_word_count_clusters(cluster_map)
print("Mean word counts per cluster:", mean_wc)

#fraction ending with period - use parameter headings['ends_with_period']
def fraction_ending_with_period(cluster_map):
    fraction_map = {}
    for label, headings in cluster_map.items():
        count = sum(1 for h in headings if h['ends_with_period'])
        fraction_map[label] = count / len(headings)
    return fraction_map

fraction_map = fraction_ending_with_period(cluster_map)
print("Fraction of headings ending with period per cluster:", fraction_map)

#mean font size
def mean_font_size_clusters(cluster_map):
    mean_fs = {}
    for label, headings in cluster_map.items():
        total_fs = sum(h["font_size"] for h in headings if h["font_size"] is not None)
        count = sum(1 for h in headings if h["font_size"] is not None)
        mean_fs[label] = total_fs / count if count > 0 else 0
    return mean_fs

mean_fs = mean_font_size_clusters(cluster_map)
print("Mean font size per cluster:", mean_fs)

#all caps ratio - use paramter headings['is_all_caps']
def all_caps_ratio_clusters(cluster_map):
    ratio_map = {}
    for label, headings in cluster_map.items():
        count = sum(1 for h in headings if h['is_all_caps'])
        ratio_map[label] = count / len(headings)
    return ratio_map

all_caps_map = all_caps_ratio_clusters(cluster_map)
print("All caps ratio per cluster:", all_caps_map)

#bold ratio - use parameter headings['font_weight'], bold is 700
def bold_ratio_clusters(cluster_map):
    ratio_map = {}
    for label, headings in cluster_map.items():
        count = sum(1 for h in headings if h['font_weight'] is not None and h['font_weight'] >= 700)
        ratio_map[label] = count / len(headings)
    return ratio_map

bold_map = bold_ratio_clusters(cluster_map)
print("Bold ratio per cluster:", bold_map)

#italic ratio - use parameter headings['italic']
def italic_ratio_clusters(cluster_map):
    ratio_map = {}
    for label, headings in cluster_map.items():
        count = sum(1 for h in headings if h.get('italic', False))
        ratio_map[label] = count / len(headings)
    return ratio_map


#underline ratio
def underline_ratio_clusters(cluster_map):
    ratio_map = {}
    for label, headings in cluster_map.items():
        count = sum(1 for h in headings if h.get('underline', False))
        ratio_map[label] = count / len(headings)
    return ratio_map

#occurrence_count
def occurrence_count_clusters(cluster_map):
    count_map = {}
    for label, headings in cluster_map.items():
        count_map[label] = len(headings)
    return count_map

occurrence_map = occurrence_count_clusters(cluster_map)
print("Occurrence count per cluster:", occurrence_map)

def mean_text_length(cluster_map):
    mean_length = {}
    for label, headings in cluster_map.items():
        total_length = sum(len(h["text"]) for h in headings)
        mean_length[label] = total_length / len(headings)
    return mean_length

mean_length_map = mean_text_length(cluster_map)
print("Mean text length per cluster:", mean_length_map)


#print ratio of lines with word count > 12 
def long_heading_ratio(cluster_map):
    ratio_map = {}
    for label, headings in cluster_map.items():
        count = sum(1 for h in headings if len(h["text"].split()) > 12)
        ratio_map[label] = count / len(headings)
    return ratio_map

def is_title_ratio(cluster_map):
    ratio_map = {}
    for label, headings in cluster_map.items():
        count = sum(1 for h in headings if is_title_case(h["text"]) > 0.5)
        ratio_map[label] = count / len(headings)
    return ratio_map

def is_emphasis_color(sig, body_color, threshold=100):
    return 1.0 if sig["mean_color_distance"] > threshold else 0.0

#create color_ratio function using is_emphasis_color
def is_emphasis_color_ratio(cluster_map, body_color, threshold=100):
    ratio_map = {}
    for label, headings in cluster_map.items():
        sig = {
            "mean_color_distance": np.mean([
                color_distance(h["font_color"], body_color)
                for h in headings
                if h.get("font_color")
            ]) if any(h.get("font_color") for h in headings) else 0
        }
        ratio_map[label] = is_emphasis_color(sig, body_color, threshold)
    return ratio_map


#---------------------------------------------------
def build_cluster_vectors(cluster_signature):
    vectors = {}

    for c, sig in cluster_signature.items():
        vectors[c] = np.array([
            sig["mean_font_size"],
            sig["bold_ratio"],
            sig["italic_ratio"],
            sig["underline_ratio"],
            sig["all_caps_ratio"],
            sig["is_title_ratio"],
            sig["is_emphasis_color"],
        ], dtype=float)

    return vectors


def normalize_vectors(vectors):
    keys = list(vectors.keys())
    matrix = np.vstack([vectors[k] for k in keys])

    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0) + 1e-6

    normalized = {}
    for k in keys:
        normalized[k] = (vectors[k] - mean) / std

    return normalized, mean, std

def agglomerative_merge(cluster_signature, distance_threshold=1.0):

    clusters = {c: [c] for c in cluster_signature.keys()}

    def centroid(group):
        return np.mean([
            np.array([
                cluster_signature[c]["mean_font_size"],
                cluster_signature[c]["bold_ratio"],
                cluster_signature[c]["italic_ratio"],
                cluster_signature[c]["underline_ratio"],
                cluster_signature[c]["all_caps_ratio"],
                cluster_signature[c]["is_title_ratio"],
                cluster_signature[c]["is_emphasis_color"],
            ])
            for c in group
        ], axis=0)


    while True:
        keys = list(clusters.keys())
        min_dist = float("inf")
        pair_to_merge = None

        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                c1 = keys[i]
                c2 = keys[j]


            



                dist = np.linalg.norm(
                    centroid(clusters[c1]) - centroid(clusters[c2])
                )

                if dist < min_dist:
                    min_dist = dist
                    pair_to_merge = (c1, c2)

        if min_dist > distance_threshold:
            break

        c1, c2 = pair_to_merge
        clusters[c1] = clusters[c1] + clusters[c2]
        del clusters[c2]

    return clusters

def rebuild_cluster_signature(cluster_signature, merged_clusters):

    new_signature = {}

    for new_label, original_labels in merged_clusters.items():

        aggregated = {k: [] for k in cluster_signature[next(iter(cluster_signature))]}

        for old_label in original_labels:
            for key, value in cluster_signature[old_label].items():
                aggregated[key].append(value)

        new_signature[new_label] = {
            k: np.mean(v) for k, v in aggregated.items()
        }

    return new_signature


#----------------------------------------------------


def cluster_signature_analysis(cluster_map):
    
    cluster_signature = {}

    for c in cluster_map.keys():
        cluster_signature[c] = {
            "mean_word_count": mean_wc[c],
            "fraction_ending_with_period": fraction_map[c],
            "mean_font_size": mean_fs[c],
            "all_caps_ratio": all_caps_map[c],
            "bold_ratio": bold_map[c],
            "italic_ratio": italic_ratio_clusters(cluster_map)[c],
            "underline_ratio": underline_ratio_clusters(cluster_map)[c],
            "is_title_ratio": is_title_ratio(cluster_map)[c],
            "is_emphasis_color": is_emphasis_color_ratio(cluster_map, body_color)[c],
            "occurrence_count": occurrence_map[c],
            "mean_text_length": mean_length_map[c],
            "sentence_ratio": long_heading_ratio(cluster_map)[c]
        }

    return cluster_signature

def deepest_cluster(cluster_signature):
    deepest = max(
        cluster_signature,
        key=lambda c: cluster_signature[c]["mean_word_count"]
    )

    if cluster_signature[deepest]["sentence_ratio"] < 0.5:
        #fallback: choose cluster with highest sentence ratio
        deepest = max(
            cluster_signature,
            key=lambda c: cluster_signature[c]["sentence_ratio"] 
        )   
    return deepest


print("Cluster signature analysis:")
cluster_signature = cluster_signature_analysis(cluster_map)

#print number of different clusters before merging
print("Number of clusters before merging:", len(cluster_signature))


merged_clusters = agglomerative_merge(cluster_signature, distance_threshold=1.2)
print("Merged clusters:", merged_clusters)


# ----------------------------------------
# Remap original cluster labels to merged labels
# ----------------------------------------

cluster_remap = {}

for merged_label, original_labels in merged_clusters.items():
    for old_label in original_labels:
        cluster_remap[old_label] = merged_label

# Update headings to merged cluster labels
for h in new_headings:
    old = h["cluster_label"]
    h["cluster_label"] = cluster_remap.get(old, old)


# Rebuild cluster signature after merging
cluster_signature = rebuild_cluster_signature(cluster_signature, merged_clusters)
print("Number of clusters after merging:", len(cluster_signature))


deepest_cluster = deepest_cluster(cluster_signature)
print("Deepest cluster:", deepest_cluster)

print("\n=== TRUE DEEPEST MEMBERS ===")
for h in new_headings:
    if h["cluster_label"] == deepest_cluster:
        print(h["text"][:120])

# ----------------------------------------
# Build normalized centroid space
# ----------------------------------------

cluster_vectors = build_cluster_vectors(cluster_signature)
cluster_vectors_norm, norm_mean, norm_std = normalize_vectors(cluster_vectors)

deepest_centroid = cluster_vectors_norm[deepest_cluster]

#----------------------------------------

def remaining_clusters(cluster_signature, deepest_cluster):
    return [
        c for c in cluster_signature
        if c != deepest_cluster
    ]

print("Remaining clusters:", remaining_clusters(cluster_signature, deepest_cluster))


    
    

def normalize(values):
    min_v = min(values)
    max_v = max(values)
    return {
        k: (v - min_v) / (max_v - min_v + 1e-6)
        for k, v in values.items()
    }
def level_mapping(cluster_signature, remaining_clusters, deepest_cluster):

    level_map = {}

    if not remaining_clusters:
        level_map[deepest_cluster] = 2
        return level_map

    # ---- Step 1: sort by font size first (dominant signal) ----
    font_sizes = {
        c: cluster_signature[c]["mean_font_size"]
        for c in remaining_clusters
    }

    sorted_by_font = sorted(
        remaining_clusters,
        key=lambda c: font_sizes[c],
        reverse=True
    )

    # ---- Step 2: group clusters by font size ----
    font_groups = {}
    for c in sorted_by_font:
        fs = cluster_signature[c]["mean_font_size"]
        font_groups.setdefault(fs, []).append(c)

    current_level = 2

    # ---- Step 3: within each font tier, rank by shortness/title ----
    for fs in sorted(font_groups.keys(), reverse=True):

        group = font_groups[fs]

        wc_norm = normalize({
            c: cluster_signature[c]["mean_word_count"]
            for c in group
        })

        caps_norm = normalize({
            c: cluster_signature[c]["is_title_ratio"]
            for c in group
        })

        sorted_group = sorted(
            group,
            key=lambda c: (
                2 * caps_norm[c]
                - 2 * wc_norm[c]
            ),
            reverse=True
        )

        for c in sorted_group:
            level_map[c] = current_level
            current_level += 1

    level_map[deepest_cluster] = current_level

    return level_map

full_level_map = {}

#risk factors root
full_level_map["RISK FACTORS"] = 1

internal_level_map = level_mapping(
    cluster_signature,
    remaining_clusters(cluster_signature, deepest_cluster),
    deepest_cluster
)

# Add internal cluster levels
for cluster_label, level in internal_level_map.items():
    full_level_map[cluster_label] = level

print("Full level map:", full_level_map)


#----------------------------------------
# Assign resolved hierarchy levels
# ----------------------------------------

def assign_levels(headings, level_map):
    for h in headings:
        cluster = h["cluster_label"]
        h["level"] = level_map.get(cluster, 3)
    return headings

new_headings = assign_levels(new_headings, full_level_map)



def build_style_vector(block, body_color):
    return np.array([
        block["font_size"] or 0,
        block["font_weight"] or 400,
        int(block.get("italic", False)),
        int(block.get("underline", False)),
        int(block.get("is_all_caps", False)),
        1.0 if (
            block.get("font_color")
            and color_distance(block["font_color"], body_color) > 100
        ) else 0.0
    ], dtype=float)




# ----------------------------------------
# STYLE SPACE MODEL OF DEEPEST CLUSTER
# ----------------------------------------

deep_blocks = [
    h for h in new_headings
    if h["cluster_label"] == deepest_cluster
]

deep_vectors = np.array([
    build_style_vector(h, body_color)
    for h in deep_blocks
])

scaler = StandardScaler()
deep_vectors_scaled = scaler.fit_transform(deep_vectors)

deep_centroid = deep_vectors_scaled.mean(axis=0)

# Empirical cluster radius
true_dists = np.linalg.norm(
    deep_vectors_scaled - deep_centroid,
    axis=1
)

cluster_mean = true_dists.mean()
cluster_std = true_dists.std()

recovery_radius = cluster_mean + 2 * cluster_std

print("Style-space recovery radius:", recovery_radius)

("\n=== FINAL HEADING STATE BEFORE TREE ===")
for h in new_headings:
    print(
        h["text"][:60],
        "| cluster:", h["cluster_label"],
        "| level:", h["level"]
    )


# ----------------------------------------
# Build hierarchical tree
# ----------------------------------------

def build_tree(headings):

    root = {
        "text": "RISK FACTORS",
        "level": 1,
        "children": []
    }

    stack = [root]

    for h in headings:

        node = {
            "text": h["text"],
            "level": h["level"],
            "children": []
        }

        while stack and stack[-1]["level"] >= node["level"]:
            stack.pop()

        stack[-1]["children"].append(node)
        stack.append(node)

    return root

def recover_missing_deepest_blocks(
    scored_blocks,
    headings,
    scaler,
    deep_centroid,
    recovery_radius,
    body_color
):

    existing_texts = {h["text"] for h in headings}
    recovered = []

    for b in scored_blocks:

        if b.get("is_bullet", False):
            continue

        if b["text"] in existing_texts:
            continue

        wc = b["word_count"]

        # --------------------------
        # HARD GATES (CRITICAL)
        # --------------------------

        # Only recover mid-length edge cases
        if wc <= 45 or wc > 85:
            continue

        # Must have visual emphasis
        visual_emphasis = (
            b["font_weight"] > 400
            or b["larger_than_body"]
            or b["italic"]
            or b["is_all_caps"]
            or (
                body_color
                and b.get("font_color")
                and color_distance(b["font_color"], body_color) > 100
            )
        )

        if not visual_emphasis:
            continue

        # Must NOT look like a sentence
        if b["ends_with_period"] and wc > 55:
            continue

        # --------------------------
        # Style similarity
        # --------------------------

        vec = build_style_vector(b, body_color)
        vec_scaled = scaler.transform([vec])[0]
        dist = np.linalg.norm(vec_scaled - deep_centroid)

        if dist <= recovery_radius:
            print("Recovered missing deepest heading:", b["text"][:60])

            recovered.append(b)

    return recovered


recovered = recover_missing_deepest_blocks(
    scored_blocks,
    new_headings,
    scaler,
    deep_centroid,
    recovery_radius,
    body_color
)

for b in recovered:
    b["level"] = full_level_map[deepest_cluster]
    b["candidate_header"] = True 
    new_headings.append(b)

# Rebuild heading list in original DOM order
def rebuild_headings_in_doc_order(scored_blocks, headings):

    heading_ids = set(id(h) for h in headings)
    ordered = []

    for b in scored_blocks:
        for h in headings:
            if b is h:
                ordered.append(h)

    return ordered

new_headings = rebuild_headings_in_doc_order(scored_blocks, new_headings)

# ----------------------------------------
# Freeze structural header truth
# ----------------------------------------

# Reset all blocks
for b in scored_blocks:
    b["is_header"] = False

# Mark only final hierarchy headings
for h in new_headings:
    h["is_header"] = True



def serialize_headings(headings):
    allowed = {
        "text",
        "level",
        "cluster_label",
        "font_size",
        "font_weight",
        "is_all_caps",
        "italic",
        "underline",
        "ends_with_period"
    }

    serialized = []

    for h in headings:
        entry = {}

        for k in allowed:
            if k in h:
                value = h[k]

                # Convert numpy scalars
                if isinstance(value, np.generic):
                    value = value.item()

                entry[k] = value

        serialized.append(entry)

    return serialized


#save new_headings
output_headings_path = f"./data/level_headings/{ticker}/risk_factors/{year}.json"
os.makedirs(os.path.dirname(output_headings_path), exist_ok=True)
with open(output_headings_path, "w") as f:
    json.dump(serialize_headings(new_headings), f, indent=2)

#resave scored blocks with is_header updated
scored_blocks_path = f'./data/scored_blocks/{ticker}/risk_factors/{year}.json'
os.makedirs(os.path.dirname(scored_blocks_path), exist_ok=True)
with open(scored_blocks_path, 'w', encoding='utf-8') as f:
    json.dump(make_serializable(scored_blocks), f, indent=2)




#print("Building hierarchical tree...")
hierarchy_tree = build_tree(new_headings)
import json
#print(json.dumps(hierarchy_tree, indent=2))

#write to file
output_path = f"./data/heading_tree/{ticker}/risk_factors/{year}.json"
#make directories if not exist
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as f:
    json.dump(hierarchy_tree, f, indent=2)