
from chunk.risk_heading_utils import find_risk_factor_heading, normalize_heading_text

def extract_leaf_nodes(node, parent_path=None):
    if parent_path is None:
        parent_path = []

    current_path = parent_path + [node["text"]]

    leaves = []

    if not node.get("children"):
        leaves.append({
            "heading": node["text"],
            "level": node["level"],
            "path": current_path
        })
    else:
        for child in node["children"]:
            leaves.extend(
                extract_leaf_nodes(child, current_path)
            )

    return leaves


def extract_paragraph_segments(scored_blocks, heading_positions,leaf_lookup):
    """
    leaf_lookup: dict mapping heading_text -> path
    """

    chunks = []

    for idx, (start_i, heading_block) in enumerate(heading_positions):

        heading_text = heading_block["text"]
        level = heading_block["level"]

        # Only process deepest headings
        if heading_text not in leaf_lookup:
            continue

        # Find structural boundary
        end_i = len(scored_blocks)

        for j in range(start_i + 1, len(scored_blocks)):
            if scored_blocks[j].get("is_header", False):
                if scored_blocks[j]["level"] <= level:
                    end_i = j
                    break

        k = start_i + 1
        paragraph_index = 0

        while k < end_i:

            b = scored_blocks[k]

            if b.get("is_header", False):
                k += 1
                continue

            text = b["text"].strip()

            # -------------------------------------------------
            # CASE 1 — Lead-in to bullet cluster
            # -------------------------------------------------
            if (
                text.endswith(":")
                and k + 1 < end_i
                and scored_blocks[k + 1].get("is_bullet")
            ):

                combined = text
                k += 1

                # collect bullet cluster
                while k < end_i and scored_blocks[k].get("is_bullet"):
                    combined += " " + scored_blocks[k]["text"].strip()
                    k += 1

                chunks.append({
                    "heading": heading_text,
                    "level": level,
                    "path": leaf_lookup[heading_text],
                    "paragraph_index": paragraph_index,
                    "text": combined
                })

                paragraph_index += 1
                continue

            # -------------------------------------------------
            # CASE 2 — Standalone bullet cluster (no colon)
            # -------------------------------------------------
            if b.get("is_bullet"):

                combined = ""

                while k < end_i and scored_blocks[k].get("is_bullet"):
                    combined += " " + scored_blocks[k]["text"].strip()
                    k += 1

                chunks.append({
                    "heading": heading_text,
                    "level": level,
                    "path": leaf_lookup[heading_text],
                    "paragraph_index": paragraph_index,
                    "text": combined.strip()
                })

                paragraph_index += 1
                continue

            # -------------------------------------------------
            # CASE 3 — Normal paragraph
            # -------------------------------------------------
            chunks.append({
                "heading": heading_text,
                "level": level,
                "path": leaf_lookup[heading_text],
                "paragraph_index": paragraph_index,
                "text": text
            })

            paragraph_index += 1
            k += 1

    return chunks



if __name__ == "__main__":
    import json
    import os

    year = 2018
    ticker = 'MU'

    # Example usage
    input_path = f"./data/heading_tree/{ticker}/risk_factors/{year}.json"
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path = f"./data/heading_leaves/{ticker}/risk_factors/{year}.json"


    with open(input_path, "r") as f:
        hierarchy_tree = json.load(f)

    leaves = extract_leaf_nodes(hierarchy_tree)

    #os.makedirs(os.path.dirname(output_path), exist_ok=True)
    #with open(output_path, "w") as f:
    #    json.dump(leaves, f, indent=2)

    #print json
    #print(json.dumps(leaves, indent=2))

    leaf_lookup = {
        leaf["heading"]: leaf["path"]
        for leaf in leaves
        }
  
    
    scored_blocks_path = f'./data/scored_blocks/{ticker}/risk_factors/{year}.json'
    if not os.path.exists(scored_blocks_path):
        raise FileNotFoundError(f"Scored blocks file not found: {scored_blocks_path}")
    with open(scored_blocks_path, 'r', encoding='utf-8') as f:
        scored_blocks = json.load(f)

    new_headings_path = f'./data/level_headings/{ticker}/risk_factors/{year}.json'
    if not os.path.exists(new_headings_path):
        raise FileNotFoundError(f"New headings file not found: {new_headings_path}")
    with open(new_headings_path, 'r', encoding='utf-8') as f:
        new_headings = json.load(f)

    print(len(scored_blocks), "scored blocks loaded")

    risk_start = find_risk_factor_heading(scored_blocks)
    print("Risk Factors heading at block index:", risk_start)

    header_indices = [
        i for i, b in enumerate(scored_blocks)
        if b.get("is_header", False) and i > risk_start
                    ]

    print(len(header_indices), "headers after risk factors heading")
    print(len(new_headings), "new headings loaded")
    
    
    if len(header_indices) != len(new_headings):

        block_headers = [
            scored_blocks[i]["text"].strip()
            for i in header_indices
        ]

        new_heading_texts = [
            h["text"].strip()
            for h in new_headings
        ]

        missing_in_blocks = set(new_heading_texts) - set(block_headers)
        missing_in_new = set(block_headers) - set(new_heading_texts)

        print("Missing in blocks:", missing_in_blocks)
        print("Missing in new:", missing_in_new)

        raise ValueError("Mismatch between headings and block headers")

    for idx, block_index in enumerate(header_indices):
        scored_blocks[block_index]["level"] = new_headings[idx]["level"]

    heading_positions = [
        (i, scored_blocks[i])
        for i in header_indices
        ]


    paragraph_chunks = extract_paragraph_segments(
        scored_blocks,
        heading_positions,
        leaf_lookup
    )

 

    outpath = f'./data/paragraph_chunks/{ticker}/risk_factors/{year}.json'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, 'w', encoding='utf-8') as file:
        json.dump(paragraph_chunks, file, indent=2)
        