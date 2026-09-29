# this script detects the string 'items' in the normalized 10-K filings

import re
from filing_parser.utils.normalize import normalize_text
from lxml import html
from collections import defaultdict
def clean_tree(tree):

   
    # remove script, style, and noscript elements
    for element in tree.xpath('//script | //style | //noscript'):
        element.getparent().remove(element)
    
    # remove comments
    comments = tree.xpath('//comment()')
    for comment in comments:
        parent = comment.getparent()
        if parent is not None:
            parent.remove(comment)
    
    return tree

# function to check if a node is inside a table (not desired)
def is_inside_table(node):
    parent = node
    while parent is not None:
        if parent.tag in {"table", "tr"}:
            return True
        parent = parent.getparent()
    return False

def extract_structural_item_headers(tree):

    candidates = tree.xpath('//p | //div | //td')

    headers = []
    pattern = re.compile(r'^ITEM\s*([0-9]+)([A-Z]?)\b', re.IGNORECASE)

    for node in candidates:

        if is_inside_table(node):
            continue

        

        raw_text = " ".join(node.itertext())
        text = re.sub(r'\s+', ' ', raw_text).strip()

        if not text:
            continue

     
        
        match = pattern.match(text.upper())
        if match:

            number = int(match.group(1))
            letter = match.group(2)

            headers.append({
                "text": text,
                "number": number,
                "letter": letter if letter else None,
                "node": node,
                "position": len(headers)
            })

    headers = sorted(headers, key=lambda x: x["position"])

    return headers


def deduplicate_headers(headers):

    grouped = defaultdict(list)

    for h in headers:
        grouped[h["number"], h["letter"]].append(h)

    selected = []

    for value, candidates in grouped.items():

        # choose longest text; if tie, choose later sourceline
        best = max(
            candidates,
            key=lambda x: (len(x["text"]), x["position"])
        )

        selected.append(best)

    # sort final selection by position
    selected = sorted(selected, key=lambda x: x["position"])

    return selected


def extract_section_by_index(
    tree,
    headers,
    start_number,
    start_letter=None,
    stop_number=None,
    stop_letter=None
):

    start_node = None
    stop_node = None

    # Locate start header
    for h in headers:
        if h["number"] == start_number and h["letter"] == start_letter:
            start_node = h["node"]
            break

    if start_node is None:
        return None, None, None

    # Locate stop header (if provided)
    if stop_number is not None:
        for h in headers:
            if h["number"] == stop_number and h["letter"] == stop_letter:
                stop_node = h["node"]
                break

    section_text = []
    collecting = False
    seen = set()  # prevent duplicates

    for node in tree.iter():

        if node == start_node:
            collecting = True
            continue

        if stop_node is not None and node == stop_node:
            break

        if collecting:

            # Only capture visible content containers
            if node.tag not in ("div", "p", "td"):
                continue

            text = node.text_content().strip()

            if text and text not in seen:
                section_text.append(text)
                seen.add(text)

    return "\n".join(section_text), start_node, stop_node



if __name__ == "__main__":
    
    tree = extract_text("./data/10K_Filings/raw/MU/2018.html")
    headers = extract_structural_item_headers(tree)

    headers = deduplicate_headers(headers)

    #for header in headers:
    #    print(header["text"])
    
    text = extract_section_by_index(tree, headers, 1, "A")
    print(text[:1000])
