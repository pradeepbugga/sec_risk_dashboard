import re
from lxml import html

import json

def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()

def find_start_node(html_path, section_text, anchor_len=80):
    """
    Locate the DOM node corresponding to the start of Item 1A
    using the first anchor_len characters of the extracted section text.
    """

    with open(html_path, "r", encoding="utf-8") as f:
        tree = html.parse(f)

    # Normalize extracted section text
    normalized_section = normalize(section_text)

    # Take first N characters as anchor
    anchor_text = normalized_section[:anchor_len]

    # Escape for regex search
    anchor_pattern = re.escape(anchor_text[:60])  # slightly shorter to tolerate noise
    pattern = re.compile(anchor_pattern, re.IGNORECASE)

    print(f"Searching for anchor: '{anchor_text[:60]}...'")

    raw_candidates = []

    # Search block-level elements
    for node in tree.xpath('//div | //p'):
        text = normalize(" ".join(node.itertext()))
        if not text:
            continue

        if pattern.search(text):
            raw_candidates.append(node)

    if not raw_candidates:
        print("No start node found.")
        return None

    # If multiple matches, choose the earliest in document order
    start_node = raw_candidates[0]

    print("Start node detected:")
    print(normalize(" ".join(start_node.itertext()))[:200])

    return start_node

if __name__ == '__main__':
    html_path = "./data/10K_Filings/raw/MU/2018.html"
    
    json_path = "./data/processed/MU/2018.json"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f) 

    section_text = data["sections"]["risk_factors"]["text"]

    node = find_start_node(html_path, section_text)
    print(node)