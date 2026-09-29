import re


def get_font_size(node):
    """
    Extract numeric font size (pt or px) from inline style.
    Checks node and descendants.
    """
    def extract(style):
        match = re.search(
            r'font-size\s*:\s*([0-9]*\.?[0-9]+)\s*(pt|px)',
            style or "",
            re.IGNORECASE
        )
        if match:
            return float(match.group(1))
        return None

    # Check node itself
    size = extract(node.get("style", ""))
    if size is not None:
        return size

    # Check descendants
    for child in node.xpath(".//*"):
        size = extract(child.get("style", ""))
        if size is not None:
            return size

    return None


def looks_like_major_heading(text):
    if len(text.split()) > 12:
        return False
    if not re.match(r'^[A-Z0-9\s\-\&\',\.()]+$', text):
        return False
    return True

def extract_by_title(tree, start_pattern, stop_patterns=None):

    start_node = None
    pattern = re.compile(start_pattern, re.IGNORECASE)

    candidates = []

    # 1️⃣ Find exact heading match
    for node in tree.xpath('//div | //p | //span'):
        text = re.sub(r'\s+', ' ', " ".join(node.itertext())).strip()
        if not text:
            continue       
        if pattern.search(text):
            font_size = get_font_size(node)
            #print(f"Found candidate: {text} with font size {font_size}")
            candidates.append((node, font_size,text))
            
   
    if not candidates:
        return None, None, None

    candidates.sort(key=lambda x: x[1], reverse=True)

    start_node = candidates[0][0]

 
    
    # 2️⃣ Detect heading font size
    heading_font_size = get_font_size(start_node)

    

    section_text = []
    collecting = False

    heading_text = re.sub(r'\s+', ' ', " ".join(start_node.itertext())).strip()

    stop_node = None

    # 4️⃣ Traverse full DOM in order
    for node in tree.iter():

        if node == start_node:
            collecting = True
            continue

        if not collecting:
            continue

        if len(node) == 0:
            text = re.sub(r'\s+', ' ', (node.text or "")).strip()
        else:
            continue
        if not text:
            continue

        node_font = get_font_size(node)

 
        # 6️⃣ Optional regex stop safety
        if stop_patterns:
            for stop in stop_patterns:
                if node.xpath("self::tr or self::td or ancestor::tr"):
                    continue
                if re.search(stop, text, re.IGNORECASE):
                    stop_node = node
                    return "\n".join(section_text), start_node, stop_node

        # 7️⃣ Skip duplicate heading text
        if text.lower() == heading_text.lower():
            continue

        section_text.append(text)

    return "\n".join(section_text), start_node, stop_node