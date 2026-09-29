
import re
from collections import Counter
import math

def parse_style(style):
    props = {}
    for part in style.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            props[k.strip().lower()] = v.strip()
    return props

def get_font_color(node):
    style = node.attrib.get("style", "")
    props = parse_style(style)
    

    return props.get("color")
def split_colored_leadin(node, body_color):

    spans = node.xpath("./span | ./font | ./b | ./strong")   

    if len(spans) < 2:
        return None

    heading_nodes = []
    body_nodes = []

    heading_parts = []
    body_parts = []

    heading_color = None
    body_span_color = None
    encountered_body = False

    for span in spans:

        text = "".join(span.itertext())
        
        if not text.strip():
            if not encountered_body:
                heading_parts.append(text)
                heading_nodes.append(span)
            else:
                body_parts.append(text)
                body_nodes.append(span)
            continue

        span_color = normalize_color(get_font_color(span))

        # ---- First colored span defines heading color ----
        if not encountered_body and heading_color is None:
            

            heading_color = span_color

            # Reject off-black fake lead-ins
            if heading_color and body_color:
                if color_distance(heading_color, body_color) < 100:
                    return None


            heading_parts.append(text)
            heading_nodes.append(span)
            continue

        # ---- If color matches heading color → still heading ----
        if not encountered_body and span_color and heading_color and color_distance(span_color, heading_color) < 100:
            

            heading_parts.append(text)
            heading_nodes.append(span)
            continue

        # ---- Otherwise → switch to body ----
        encountered_body = True
        body_parts.append(text)
        body_nodes.append(span)

        if body_span_color is None:
           

            body_span_color = span_color

    heading_text = re.sub(r'\s+', ' ', "".join(heading_parts)).strip()
    body_text = re.sub(r'\s+', ' ', "".join(body_parts)).strip()

    if not heading_text or not body_text:
        return None

    wc = len(heading_text.split())
    if not (2 <= wc <= 60):
        return None

    return heading_text, body_text, heading_nodes, body_nodes, heading_color, body_span_color

def get_dominant_color(node):
    colors = []

    # Collect colors from spans
    for span in node.xpath(".//span"):
        style = span.attrib.get("style", "")
        m = re.search(r"color:\s*([^;]+)", style)
        if m:
            colors.append(m.group(1).lower())

    if not colors:
        return None

    # Return most common
    from collections import Counter
    return Counter(colors).most_common(1)[0][0]

def detect_structural_color_usage(blocks, body_color):
    """
    Returns True if color appears to be used intentionally
    for subheadings or structure.
    """

    color_counts = Counter(
        b["font_color"]
        for b in blocks
        if b.get("font_color") and b["font_color"] != body_color
    )

    # If only one non-body color appears very rarely → ignore
    if not color_counts:
        return False

    most_common_color, count = color_counts.most_common(1)[0]

    # Require repetition to consider structural
    return count >= 3

def normalize_color(color):
    if not color:
        return None

    color = color.strip().lower()

    # Remove trailing semicolon
    color = color.rstrip(";")

    # Normalize rgb() → hex
    if color.startswith("rgb"):
        nums = [int(x) for x in re.findall(r"\d+", color)]
        if len(nums) == 3:
            return "#{:02x}{:02x}{:02x}".format(*nums)

    # Expand shorthand #abc → #aabbcc
    m = re.fullmatch(r"#([0-9a-f]{3})", color)
    if m:
        short = m.group(1)
        return "#" + "".join([c * 2 for c in short])

    return color

def hex_to_rgb(hex_color):
    hex_color = normalize_color(hex_color)
    if not hex_color or not hex_color.startswith("#"):
        return None
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def color_distance(c1, c2):

    if not c1:
        c1 = "#000000"
    if not c2:
        c2 = "#000000"

    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return math.sqrt((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)

def get_dominant_text_color(node):
    colors = []

    # Include node itself
    node_color = get_font_color(node)
    if node_color:
        colors.append(node_color)

    # Check descendants
    for el in node.iter():
        color = get_font_color(el)
        if color:
            colors.append(color)

    if not colors:
        return None

    # Return most common
    from collections import Counter
    return Counter(colors).most_common(1)[0][0]

    
if __name__ == "__main__":
    # Simple test
    c1 = "#000000"
    c2 = "#262626"
    dist = color_distance(c1, c2)
    print(f"Color distance between {c1} and {c2} is {dist}")