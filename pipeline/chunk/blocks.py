
import re, numpy as np
import json
from chunk.extract_dom_slice import extract_dom_slice
from filing_parser.extractors.title_extract2 import get_font_size
from chunk.chunk_utils import is_repeated_artifact, build_text_frequency
from lxml import html, etree
from chunk.page_break_utils import is_page_break_node
import os
from collections import Counter, defaultdict
#from chunk.layout_utils import is_layout_container
from chunk.page_number_utils import split_trailing_page_number
from chunk.color_utils import get_font_color, split_colored_leadin, get_dominant_color, detect_structural_color_usage
from chunk.color_utils import normalize_color, color_distance, get_dominant_text_color, parse_style
from chunk.heading_clustering import cluster_heading_styles
from chunk.table_utils import normalize_data_table, classify_table

def strip_ns(tag):
    if tag is None:
        return None
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def apply_font_relative_features(blocks, body_font):
    for b in blocks:
        if b.get("font_size") and body_font:
            b["larger_than_body"] = b["font_size"] > body_font
        else:
            b["larger_than_body"] = False
    return blocks

def build_global_frequency(blocks):
    texts = [b["text"] for b in blocks if b.get("text")]
    return Counter(texts)


def get_italic(node):
    total_text = "".join(node.itertext()).strip()
    if not total_text:
        return False

    italic_text = ""

    for el in node.iter():
        tag = strip_ns(el.tag).lower()
        style = parse_style(el.attrib.get("style", ""))

        if tag in {"i", "em"} or \
           style.get("font-style", "").lower().startswith("italic"):
            italic_text += "".join(el.itertext())

    return len(italic_text.strip()) > 0.5 * len(total_text)


def get_font_underline(node):

    # Check node itself
    style = (node.attrib.get("style") or "").lower()
    if "underline" in style:
        return True

    

    if node.tag == "u":
        return True

    # Check descendants
    for child in node.iter():
        if child is node:
            continue

        if child.tag == "u":
            return True

        child_style = (child.attrib.get("style") or "").lower()
        
        if "underline" in child_style:
            return True
        

    return False
def extract_deepest_text_nodes(node):
    """
    Return list of (element, text) pairs where:
    - element contains meaningful text
    - none of its children contain meaningful text
    """
    results = []

    def recurse(n):
        text = " ".join(n.itertext()).strip()
        if not text:
            return False

        # Check if any child also has meaningful text
        child_has_text = False
        for child in n:
            child_text = " ".join(child.itertext()).strip()
            if child_text:
                child_has_text = True
                recurse(child)

        if not child_has_text:
            results.append((n, text))

        return True

    recurse(node)
    return results

def is_true_block(node):
    BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "td", "li", "hr"}
    if node.tag not in BLOCK_TAGS:
        return False

    style = node.attrib.get("style", "")
    if "display:inline" in style.replace(" ", "").lower():
        return False

    return True

def get_block_nodes(slice_nodes):
    

    block_nodes = []
    skip_tables = set()

    counter = 0
    for node in slice_nodes:

    

        #skip descendants of processed tables
        table_ancestors = node.xpath("ancestor::table")
        if table_ancestors:
            table = table_ancestors[0]
            if table in skip_tables:
                continue
     
        

        if node.tag == "table":
            #print("TABLE NODE FOUND")
            #print(repr("".join(node.itertext()).strip()[:100]))
            #print("Table detected, classification:", classify_table(node))
            table_type = classify_table(node)
            if table_type == "data":

                #print("Normalizing data table...")
                normalized_text = normalize_data_table(node)

                #print("Normalized table text:", repr(normalized_text[:200]))

                synthetic_node = {
                    "node": node,
                    "tag": "table",
                    "text": normalized_text,
                    "is_table": True,
                }
                #print("Adding synthetic table node:", synthetic_node["text"][:200])

                block_nodes.append(synthetic_node)
                skip_tables.add(node)


                 # CRITICAL: prevent descendants from being processed
                for d in node.iterdescendants():
                    skip_tables.add(d)


                continue

        

        if not is_true_block(node):
            continue
        
        
        
        # Skip container blocks that contain other block-level children
        has_block_child = any(
            is_true_block(child) for child in node.iterdescendants()
        )

     
        if has_block_child:
            continue
        
      
        text = " ".join(node.itertext()).strip()
        if not text and node.tag.lower() != "hr":
            continue


        block_nodes.append({
            "node": node,
            "tag": node.tag.lower(),
            "text": text,
            "is_table": False,
        })
        

    return block_nodes
'''
def get_font_weight(node):
    # Check this node
    style = (node.attrib.get("style") or "").lower()
    weight = _extract_weight(style)
    if weight:
        return weight

    # Check children
    for child in node.iter():
        style = (child.attrib.get("style") or "").lower()
        weight = _extract_weight(style)
        if weight:
            return weight

    return None
'''
def get_font_weight(node):

    total_text = "".join(node.itertext()).strip()
    if not total_text:
        return 400

    bold_text = ""

    for el in node.iter():
        tag = strip_ns(el.tag).lower()
        style = parse_style(el.attrib.get("style", ""))

        # Case 1: explicit <b> or <strong> with real text
        if tag in {"b", "strong"}:
            if (el.text and el.text.strip()) or \
               any((child.text and child.text.strip()) for child in el):
                bold_text += "".join(el.itertext())

        # Case 2: inline style bold
        fw = style.get("font-weight", "")
        if fw.isdigit() and int(fw) >= 600:
            bold_text += "".join(el.itertext())
        if fw.lower() == "bold":
            bold_text += "".join(el.itertext())

    # Require majority bold text
    if len(bold_text.strip()) > 0.5 * len(total_text):
        return 700

    return 400

def _extract_weight(style):
    if "font-weight" not in style:
        return None

    match = re.search(r"font-weight\s*:\s*([0-9]+)", style)
    if match:
        return int(match.group(1))

    if "bold" in style:
        return 700

    return None

def get_font_style(node):
    # Check this node
    style = (node.attrib.get("style") or "").lower()
    if "font-style" in style:
        match = re.search(r"font-style\s*:\s*([a-z]+)", style)
        if match:
            return match.group(1).strip()

    # Check children
    for child in node.iter():
        style = (child.attrib.get("style") or "").lower()
        if "font-style" in style:
            match = re.search(r"font-style\s*:\s*([a-z]+)", style)
            if match:
                return match.group(1).strip()

    return None

def check_table(node):
    if node.tag in {"table", "tr", "td"}:
        return True

    for child in node.iter():
        if child.tag in {"table", "tr", "td"}:
            return True
    
    parent = node
    while parent is not None:
        if parent.tag in {"table", "tr", "td"}:
            return True
        parent = parent.getparent()
    return False

def extract_weight_from_element(el):
    # Tag-based bold
    if el.tag and el.tag.lower() in {"b", "strong"}:
        return 700

    style = (el.attrib.get("style") or "").lower()

    if not style:
        return None

    # Properly anchored CSS match
    m = re.search(r'(?:^|;)\s*font-weight\s*:\s*([^;]+)', style)
    if not m:
        return None

    val = m.group(1).strip()

    # Numeric
    if val.isdigit():
        return int(val)

    # Keyword values
    if val == "bold":
        return 700

    if val == "normal":
        return 400

    return None

def apply_colored_leadin_split(blocks, body_color):

    new_blocks = []

    for b in blocks:            
        node = b["node"]
        split = split_colored_leadin(node, body_color)

        if not split:
            #print("MISSING SPLIT FOR:", b["text"][:60])
            new_blocks.append(b)
            continue

        heading_text, body_text, heading_nodes, body_nodes, heading_color, body_span_color = split

        # ---- HEADING BLOCK ----
        heading_node = heading_nodes[0]

        heading_features = extract_block_features({
            "node": heading_node,
            "text": heading_text,
            "is_table": False
        })

        heading_features["font_color"] = heading_color
        heading_features["page_break_before"] = b["page_break_before"]
        heading_features["page_break_after"] = False

        # ---- BODY BLOCK ----
        # Use original node to preserve paragraph structure
        body_features = extract_block_features({
            "node": node,           # full original node
            "text": body_text,      # but replace text
            "is_table": False
        })

        # Force paragraph behavior
        body_features["font_color"] = body_span_color or body_color
        body_features["is_heading_tag"] = False
        body_features["is_bullet"] = False
        body_features["force_paragraph"] = True

        body_features["page_break_before"] = False
        body_features["page_break_after"] = b["page_break_after"]

        new_blocks.append(heading_features)
        new_blocks.append(body_features)

    return new_blocks


def extract_block_features_from_text(node, text, body_font=None):

    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return None

    font_size = get_font_size(node)
    font_weight = get_font_weight(node)
    font_style = get_font_style(node)

    italic = get_italic(node)
    

    is_table = check_table(node)

    word_count = len(text.split())
    text_len = len(text)

    is_all_caps = text.isupper()

    ends_with_period = text.strip().endswith(".")

    is_heading_tag = node.tag in {"h1","h2","h3","h4","h5"}

    is_bullet = (
        text.startswith(("•","-","*", "▪", "◦"))
        or detect_table_bullet(node)
    )

    
    font_color = get_dominant_text_color(node) or '#000000'

    return {
        "node": node,
        "tag": node.tag,
        "text": text,
        "font_color": font_color,
        "font_size": font_size,
        "font_weight": font_weight,
        "italic": italic,
        "is_table": is_table,
        "word_count": word_count,
        "text_len": text_len,
        "is_all_caps": is_all_caps,
        "ends_with_period": ends_with_period,
        "is_heading_tag": is_heading_tag,
        "is_bullet": is_bullet,
        "larger_than_body": False,
        "page_number": None,
        "page_break_before": False,
        "page_break_after": False,
        
    }




def compute_body_weight(blocks):
    weights = [
        b["font_weight"]
        for b in blocks
        if b["font_weight"]
    ]
    if not weights:
        return None
    return max(set(weights), key=weights.count)  # most common

def extract_block_features(block, body_font=None):


    node = block["node"]
    # ---- USE PROVIDED TEXT IF PRESENT ----
    if "text" in block and block["text"] is not None:
        text = block["text"]
    else:
        text = re.sub(r'\s+', ' ', " ".join(node.itertext())).strip()

    if not text:
        return None

    is_table = block.get("is_table", False)


    
    font_size = get_font_size(node)
    font_weight = get_font_weight(node)
    font_style = get_font_style(node)
    italic = get_italic(node)
    underline = get_font_underline(node)
    
    
    is_table = block.get("is_table", False)

    word_count = len(text.split())
    text_len = len(text)

    is_all_caps = text.isupper()
    ends_with_period = text.endswith(".")

    is_heading_tag = node.tag in {"h1","h2","h3","h4","h5"}

    is_bullet = (
        text.startswith(("•","-","*", "▪", "◦"))
        or detect_table_bullet(node)
    )

    larger_than_body = (
        font_size and body_font and font_size > body_font
    )

    font_color = get_dominant_text_color(node) or '#000000'

    return {
        "node": node,
        "tag": node.tag,
        "text": text,
        "font_color": font_color,
        "font_size": font_size,
        "font_weight": font_weight,
        "italic": italic,
        "underline": underline,
        "is_table": is_table,
        "word_count": word_count,
        "text_len": text_len,
        "is_all_caps": is_all_caps,
        "ends_with_period": ends_with_period,
        "is_heading_tag": is_heading_tag,
        "is_bullet": is_bullet,
        "larger_than_body": larger_than_body,
        "page_number": None,
        "page_break_before": False
        }

def is_in_bullet_cluster(i, blocks):
    curr = blocks[i]
    n = len(blocks)

    count = 0

    for j in range(max(0, i-2), min(n, i+3)):
        if blocks[j].get("is_bullet"):
            count += 1

    return count >= 2

def detect_table_bullet(node):
    # only relevant if node is td or p inside td
    td = node if node.tag == "td" else node.getparent()

    if td is None or td.tag != "td":
        return False

    tr = td.getparent()
    if tr is None or tr.tag != "tr":
        return False

    cells = tr.findall("td")
    if len(cells) < 2:
        return False

    bullet_text = "".join(cells[1].itertext()).strip()

    return bullet_text in {"•", "-", "*", "▪", "◦"}

def slice_blocks(block_nodes):
    feature_blocks = []
    page_break_flag = False
    last_block = None
    
    for block in block_nodes:

        node = block["node"]
        tag = block["tag"]
        text = block["text"]
        is_table = block.get("is_table", False)

       

        # ---- Page Break Handling ----
        if is_page_break_node(node):
            if last_block is not None:
                last_block["page_break_after"] = True
            page_break_flag = True
            continue

        # ---- Extract Features ----
        features = extract_block_features(block)   # pass block, not raw node
        if not features:
            continue

        features["page_break_before"] = page_break_flag
        features["page_break_after"] = False

        page_break_flag = False

        feature_blocks.append(features)
        last_block = features

    return feature_blocks


def normalize_boundary_page_numbers(blocks):
    cleaned = []

    for b in blocks:

        text = b["text"].replace("\xa0", " ").strip()

        # Only operate near page boundaries
        if b.get("page_break_before") or b.get("page_break_after"):

            parts = text.rsplit(" ", 1)

            if len(parts) == 2:
                main, last = parts

                if re.fullmatch(r"\d{1,4}", last) and len(main) > 10:
                    b["text"] = main.strip()
                    b["page_number"] = last

            # Remove pure numeric boundary blocks (AVGO style)
            if re.fullmatch(r"\d{1,4}", text):
                continue

        cleaned.append(b)

    return cleaned

def compute_body_font(blocks):
    if not blocks:
        return None

    if not isinstance(blocks[0], dict):
        raise TypeError(
            f"compute_body_font expected dict blocks, got {type(blocks[0])}"
        )

    fonts = [
        b.get("font_size")
        for b in blocks
        if b.get("font_size") and not b.get("bold")
    ]

    if not fonts:
        return None

    return sorted(fonts)[len(fonts) // 2]  # median

def score_block(i, blocks, body_weight, body_font=None, body_color=None, color_is_structural=False):

    block = blocks[i]
    prev_block = blocks[i-1] if i > 0 else None
    next_block = blocks[i+1] if i < len(blocks)-1 else None

    score = 0
    wc = block["word_count"]

    # ----------------------------
    # 1. Length heuristics
    # ----------------------------

    if wc <= 25:
        score += 2

    #print("With wc <=25, score is now", score)

    if wc <= 15:
        score += 1

    #print("With wc <=15, score is now", score)

    if wc > 60:
        score -= 3

    #print("With wc >60, score is now", score)


    # ----------------------------
    # 2. Context signals
    # ----------------------------

    if next_block:
        if wc < 30 and next_block["word_count"] > wc * 2:
            score += 2
        if wc < 30 and next_block["word_count"] > 40:
            score += 1

    if prev_block:
        if prev_block["word_count"] > 50 and wc < 30:
            score += 1



    # ----------------------------
    # 3. Sentence suppression
    # ----------------------------

    sentence_like = (
        wc < 30
        and block["ends_with_period"]
        and not block["is_all_caps"]
        and not block["is_heading_tag"]
    )

    

    

    # ----------------------------
    # 4. Visual emphasis detection
    # ----------------------------

    visual_emphasis = False

    # Bold
    if block["font_weight"] > body_weight:
        visual_emphasis = True

    # Larger font
    if block["larger_than_body"]:
        visual_emphasis = True

    #italics
    if block["italic"]:
        visual_emphasis = True

    #all caps
    if block["is_all_caps"]:
        visual_emphasis = True

    #underline
    if block.get("underline"):
        visual_emphasis = True

    # Structural color difference
    #print(visual_emphasis, color_is_structural,body_color, block.get("font_color"))
    if (
        color_is_structural
        and body_color
        and block.get("font_color")
        and color_distance(block["font_color"], body_color) > 100
    ):
        visual_emphasis = True
    #print("After color check, visual emphasis is", visual_emphasis)
    
    # 5. Visual override (dominant)
    # ----------------------------

    if visual_emphasis and wc <= 45:
        score += 5
      

    # ----------------------------
    # 6. Bullet suppression
    # ----------------------------

    if block["is_bullet"] and is_in_bullet_cluster(i, blocks):
        score -= 10

    #print("After bullet suppression, score is now", score)


    # ----------------------------
    # 7. Sentence suppression
    # ---------------------------

    if sentence_like and not visual_emphasis:
        score -= 3
    #print("After sentence suppression, score is now", score)


    # ----------------------------
    # 8. Table suppression
    # ---------------------------


    if block["is_table"]:
        return 0

    block["table_before"] = prev_block["is_table"] if prev_block else False 
    if block["table_before"]:
        if (
            block.get("font_weight", 400) <= 400
            and block["italic"] == True
            and color_is_structural
            and body_color
            and block.get("font_color")
            and color_distance(block["font_color"], body_color) < 100
        ):
            score -=5
            
    #Lead in suppression

    if block.get("force_paragraph"):
        score -= 10

    return score

def use_score_blocks(blocks, body_color=None, color_is_structural=False):
    body_font = compute_body_font(blocks)
    body_color = compute_body_color(blocks)
    body_weight = compute_body_weight(blocks)

    scored = []
    for i in range(len(blocks)):
        s = score_block(i, blocks, body_weight, body_font, body_color, color_is_structural=color_is_structural)
        block = blocks[i].copy()
        block["base_score"] = s
        scored.append(block)

    return scored



def add_context_scores(blocks):
    n = len(blocks)

    for i, b in enumerate(blocks):
        context_score = 0

        visual = b.get("visual_emphasis", False)

        # --- Look ahead ---
        if i + 1 < n:
            next_block = blocks[i + 1]

            # Colon before bullet cluster (only if not visually emphasized)
            if (
                b["text"].endswith(":")
                and not b["is_bullet"]
                and not visual
            ):
                if next_block["is_bullet"]:
                    bullet_count = 0
                    j = i + 1
                    while j < n and blocks[j]["is_bullet"]:
                        bullet_count += 1
                        j += 1
                    if bullet_count >= 1:
                        context_score -= 6

                #penalize table 
                if next_block["is_table"]:
                    context_score -= 2

        # --- Sandwich short line penalty ---
        if i > 0 and i + 1 < n:
            prev_block = blocks[i - 1]
            next_block = blocks[i + 1]

            prev_long = prev_block["word_count"] > 60
            next_long = next_block["word_count"] > 60
            curr_short = b["word_count"] < 20

            same_font = (
                b["font_size"] == prev_block["font_size"] ==
                next_block["font_size"]
            )

            same_weight = (
                b["font_weight"] == prev_block["font_weight"] ==
                next_block["font_weight"]
            )

            same_style = (
                b["italic"] == prev_block["italic"] ==
                next_block["italic"]
            )

            neighbors_body_like = (
                not prev_block.get("visual_emphasis", False)
                and not next_block.get("visual_emphasis", False)
            )

            if (
                prev_long and next_long
                and curr_short
                and same_font and same_weight and same_style
                and neighbors_body_like
                and not visual
                and not b["is_bullet"]
            ):
                context_score -= 5

        # Long paragraph suppression
        if b["word_count"] > 80:
            context_score -= 3

        b["context_score"] = context_score
        b["final_score"] = b["base_score"] + context_score

    return blocks



def remove_page_boundary_noise(blocks):

    body_font = compute_body_font(blocks)
    freq = build_global_frequency(blocks)

    cleaned = []

    for b in blocks:
        
        remove = False

        near_page_break = (
            b.get("page_break_before") or b.get("page_break_after")
        )
        #print("CHECKING:", repr(b["text"]))
        #print("NEAR PAGE BREAK:", near_page_break)
        
        if near_page_break:
        

            text = b["text"].strip()
            '''
            print("REMOVED BLOCK:")
            print("TEXT:", text)
            print("TABLE:", b["is_table"])
            print("ALL CAPS:", b["is_all_caps"])
            print("WORDS:", b["word_count"])
            print("PB_BEFORE:", b.get("page_break_before"))
            print("PB_AFTER:", b.get("page_break_after"))
            print("FONT SIZE:", b.get("font_size"))
            print("NODE", b.get("node").getroottree().getpath(b.get("node")))
            print("---")
            '''

            smaller_font = (
                body_font
                and b.get("font_size")
                and b["font_size"] < body_font
            )

            repeated = freq[text] >= 2

            # --- Type 1: repeated small-font footer ---
            if smaller_font and repeated:
                remove = True

            # --- Type 2: pure numeric page number ---
            elif re.fullmatch(r"\d{1,4}", text):
                remove = True

            # --- Type 3: page chrome like "26 | 2021 10-K" ---
            elif (
                re.search(r"\b\d{1,4}\s*\|\s*\d{4}", text)
                and b["word_count"] <= 6
            ):
                remove = True
            elif b["word_count"] <= 6:
                deeper_nodes = extract_deepest_text_nodes(b["node"])

                for child_node, child_text in deeper_nodes:

                    child_text_clean = child_text.strip()

                    # footer signature:
                    if (
                        check_table(child_node)
                        and child_text_clean.isupper()
                        and 1 <= len(child_text_clean.split()) <= 6
                    ):
                        remove = True
                        #print("REMOVED VIA DEEPER NODE:", child_text_clean)
                        break
      
            #if remove:
                #print("-> REMOVED", repr(b["text"]))
        if not remove:
            cleaned.append(b)

    return cleaned


def compute_body_color(blocks):

    color_counts = Counter()

    for b in blocks:

        # Exclude page boundary noise
        if b.get("page_break_before") or b.get("page_break_after"):
            continue

        # Must look like body paragraph
        if (
            b["word_count"] > 40
            and not b["is_all_caps"]
            and not b["is_bullet"]
            and not b["is_heading_tag"]
        ):

            #print("Considering block for body color:", b["text"][:120])

            color = b.get("font_color")
            #print("Color is",color)
            if color:
                color_counts[color] += 1

    if not color_counts:
        return None

    #print(color_counts.most_common(1)[0][0])
    return color_counts.most_common(1)[0][0] 




def is_candidate_header(block):
    return block["final_score"] > 3


def merge_page_break_splits(blocks):
    merged = []
    i = 0

    while i < len(blocks):
        current = blocks[i]

        if i + 1 < len(blocks):
            next_block = blocks[i + 1]

            if next_block.get("page_break_before", False):

                no_sentence_end = not current["text"].strip().endswith((".", "?", "!"))
                same_font = current["font_weight"] == next_block["font_weight"]

                if no_sentence_end and same_font:
                    combined = current.copy()
                    combined["text"] = current["text"] + " " + next_block["text"]
                    combined["word_count"] = len(combined["text"].split())
                    merged.append(combined)
                    i += 2
                    continue

        merged.append(current)
        i += 1

    return merged

def merge_table_bullets(blocks):

    merged = []
    processed_trs = set()

    for b in blocks:

        tr_list = b["node"].xpath("ancestor::tr")
        tr = tr_list[0] if tr_list else None

        if tr is None:
            merged.append(b)
            continue

        if tr in processed_trs:
            continue

        cells = tr.xpath("./td")

        bullet_present = False
        if len(cells) >= 1:
            first_cell_text = "".join(cells[0].itertext()).replace("\xa0","").strip()
            if first_cell_text in {"•","-","*","▪","◦"}:
                bullet_present = True

        if bullet_present:

            row_blocks = [
                x for x in blocks
                if x["node"].xpath("ancestor::tr")
                and x["node"].xpath("ancestor::tr")[0] == tr
            ]

            content_blocks = [x for x in row_blocks if x["word_count"] > 1]

            if content_blocks:
                content = content_blocks[0]
                merged_block = content.copy()
                merged_block["is_bullet"] = True
                merged.append(merged_block)

            processed_trs.add(tr)
            continue

        merged.append(b)

    return merged

def merge_same_row_table_headers(blocks):
    merged = []
    i = 0

    while i < len(blocks):
        curr = blocks[i]

        if i + 1 < len(blocks):
            next_b = blocks[i + 1]

            curr_tr = curr["node"].xpath("ancestor::tr")
            next_tr = next_b["node"].xpath("ancestor::tr")

            same_row = (
                curr_tr
                and next_tr
                and curr_tr[0] == next_tr[0]
            )

            both_short = (
                curr["word_count"] <= 10
                and next_b["word_count"] <= 10
            )

            both_bold = (
                curr["font_weight"] >= 600
                and next_b["font_weight"] >= 600
            )

            if same_row and both_short and both_bold:
                combined = curr.copy()
                combined["text"] = curr["text"].strip() + " " + next_b["text"].strip()
                combined["word_count"] = len(combined["text"].split())
                merged.append(combined)
                i += 2
                continue

        merged.append(curr)
        i += 1

    return merged

def infer_color_from_candidates(blocks, body_color):

    if not body_color:
        print("WARNING: body_color is None — defaulting to black")
        body_color = "#000000"

    candidates = [b for b in blocks if b["final_score"] >= 5]

    print("Total heading candidates:", len(candidates))

    color_counts = {}

    for b in candidates:

        font_color = b.get("font_color")

        #print("----")
        #print("TEXT:", b["text"][:120])
        #print("FONT COLOR:", font_color)
        #print("BODY COLOR:", body_color)

        if not font_color:
            #print("-> NO FONT COLOR")
            continue

        dist = color_distance(font_color, body_color)
        #print("Color distance:", dist)

        if dist > 100:
            #print("-> COUNTED AS STRUCTURAL COLOR")
            color_counts[font_color] = color_counts.get(font_color, 0) + 1
        #else:
            #print("-> NOT STRUCTURAL")

    print("Color counts:", color_counts)

    # --- Structural decision rule ---
    # Color is structural if:
    #   • At least one non-body color appears
    #   • AND it appears more than once (avoids one-off noise)
    structural = any(count >= 2 for count in color_counts.values())

    print("Color structural detected:", structural)

    return structural

def make_serializable(blocks):
    cleaned = []

    for b in blocks:
        b_copy = {}

        for k, v in b.items():

            # Remove DOM node
            if k == "node":
                continue

            # Convert numpy scalar → native python
            if isinstance(v, np.generic):
                v = v.item()

            b_copy[k] = v

        cleaned.append(b_copy)

    return cleaned
    
    


if __name__ == "__main__":
    html_path = "./data/10K_Filings/raw/AMD/2025.html"
    
    json_path = "./data/processed_with_nodes/AMD/2025.json"
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

   
    clean_blocks = make_serializable(scored_blocks)


     #save scored blocks to file for inspection
    outpath = './data/scored_blocks/AMD/risk_factors/2025.json'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, 'w', encoding='utf-8') as file:
        json.dump(clean_blocks, file, indent=2)







    headings = [
        b for b in scored_blocks
        if is_candidate_header(b)
    ]

    
    #outpath = './data/headings/INTC/risk_factors/2024.txt'
    #os.makedirs(os.path.dirname(outpath), exist_ok=True)
    #with open(outpath, 'w', encoding='utf-8') as file:
    #    for block in headings:
    #        file.write(block['text'] + '\n\n')
    
    #create visual signature vector
    
    labels = cluster_heading_styles(headings, body_color)

    print(labels)
    '''
    import csv
    
    outpath = './data/headings/INTC/risk_factors/2025_headings.csv'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)

    keys = ['index', 'final_score', 'base_score', 'context_score', 
            'font_size', 'font_weight', 'word_count', 'text_len', 
            'is_all_caps', 'is_table', 'is_bullet', 
            'text',  'underline', 'italic', "color_distance", 'cluster_label', 'level',
            "prev_is_heading", "next_is_heading"]

    with open(outpath, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        
        for i, block in enumerate(scored_blocks):
            
            color_dist = color_distance(block.get("font_color"), body_color) if block.get("font_color") else None
            prev_is_heading = is_candidate_header(scored_blocks[i-1]) if i > 0 else False
            next_is_heading = is_candidate_header(scored_blocks[i+1]) if i < len(scored_blocks)-1 else False
            
            row = {
                'index': i,
                'final_score': block['final_score'],
                'base_score': block['base_score'],
                'context_score': block['context_score'],
                'font_size': block['font_size'],
                'font_weight': block['font_weight'],
                'word_count': block['word_count'],
                'text_len': block['text_len'],
                'is_all_caps': block['is_all_caps'],
                'is_table': block['is_table'],
                'is_bullet': block['is_bullet'],
                'text': block['text'],
                'underline': block.get('underline', False),
                'italic': block.get('italic', False),
                'color_distance': color_dist,
                'cluster_label': None,
                'level': None,
                'prev_is_heading': prev_is_heading,
                'next_is_heading': next_is_heading
            }
            writer.writerow(row)
   
    '''


    for i, block in enumerate(scored_blocks):
        
            print(
                f"SCORE={block['final_score']:>3} "
                f"BASE={block['base_score']:>2} "
                f"CTX={block['context_score']:>2} "
                #f"TAG={block['tag']:<5} "
                f"FONT={block['font_size']} "
                f"COLOR={block.get('font_color', None)} "
                f"TABLE_BEFORE={block.get('table_before', False)} "
                f"WORDS={block['word_count']:>3} "
                f"LEN={block['text_len']:>4} "
                f"ALLCAPS={block['is_all_caps']} "
                f"PERIOD={block['ends_with_period']} "
                f"TABLE={block['is_table']} "
                f"BULLET={block['is_bullet']} "
                f"LARGER={block['larger_than_body']} "
                f"FREQ={freq_map.get(block['text'],0)} "
                f"TEXT={block['text']} "
                #f"TEXT={block['text'][:100]}"
                f"PAGENUM={block.get('page_number', None)} "
                f"PB_AFTER={block.get('page_break_after', False)} "
                f"PB_BEFORE={block.get('page_break_before', False)}"
                f"UNDERLINE={block.get('underline', False)} "
                f"FONT_WEIGHT={block['font_weight']} "
                f"ITALIC={block['italic']} "
                #f"NODE={block['node'].getroottree().getpath(block['node'])} "

                #print full HTML of block node, truncated to first 200 characters
                #f"HTML={html.tostring(block['node'], pretty_print=True,encoding='unicode')[:500]}"
            )
    
    

    import matplotlib.pyplot as plt
    scores = [b["final_score"] for b in scored_blocks]
    
    #plot index vs score, then have a label on each point that corresponds to first two words of the block
    plt.plot(range(0,len(scores)), scores, marker='o')
    plt.xlabel("Block Index")
    plt.ylabel("Final Score")
    for i, block in enumerate(scored_blocks):
        label = " ".join(block["text"].split()[:5])
        plt.text(i, scores[i], label, fontsize=8, rotation=90)
        
    #add threshold at y = 3
    plt.axhline(y=3, color='r', linestyle='--', label='Header Threshold')
    plt.legend()

    plt.title("Block Final Scores with Labels")
   #plt.show()
