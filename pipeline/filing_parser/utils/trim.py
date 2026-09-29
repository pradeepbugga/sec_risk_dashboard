import re
from utils.promote import promote_to_block
from utils.normalize import normalize_text

def trim_to_risk_heading(text):
    # Normalize spacing for safety
    text_norm = re.sub(r'\s+', ' ', text)

    # Look for common 20-F / 10-K patterns
    patterns = [
        r'ITEM\s+3\.?\s*D\.?\s+RISK\s+FACTORS',
        r'ITEM\s+1A\.?\s+RISK\s+FACTORS',
        r'\bRISK\s+FACTORS\b'
    ]

    for pattern in patterns:
        match = re.search(pattern, text_norm, re.IGNORECASE)
        if match:
            return text_norm[match.start():]

    return text_norm  # fallback if not found


def postprocess_20F_risk(tree, start_node, stop_node):
    patterns = [
        r'ITEM\s+3\.?\s*D\.?\s+RISK\s+FACTORS',
        r'ITEM\s+1A\.?\s+RISK\s+FACTORS',
        r'\bRISK\s+FACTORS\b'
        ]

    new_start_node = None
    
    section_text = []

        # 4️⃣ Traverse only after start node
    for node in start_node.xpath("./following::*"):

        if node == stop_node:
            break


        text = re.sub(r'\s+', ' ', " ".join(node.itertext())).strip()
        
        if not text:
            continue


        for pattern in patterns:
            if re.fullmatch(pattern, text, re.IGNORECASE):
                
                new_start_node = promote_to_block(node)
                break

        if new_start_node is not None:
            return new_start_node, stop_node

    return start_node, stop_node
















