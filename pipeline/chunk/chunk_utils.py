from collections import Counter

def build_text_frequency(blocks):
    
    texts = [b["text"] for b in blocks if b and b["text"]]
    return Counter(texts)

def is_repeated_artifact(text, freq_map, min_repeats=3):
    if not text:
        return False

    # repeated exact text
    if freq_map.get(text, 0) >= min_repeats:
        return True

    # very short numeric-only (page numbers)
    if text.strip().isdigit() and len(text.strip()) <= 3:
        return True

    # Table of Contents
    if text.lower() == "table of contents":
        return True

    return False
    