import json
from lxml import html
import re
from chunk.page_break_utils import is_page_break_node

BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "table"}
def has_block_ancestor(node):
    parent = node.getparent()
    while parent is not None:
        if parent.tag in BLOCK_TAGS:
            return True
        parent = parent.getparent()
    return False


def extract_dom_slice(html_path, start_xpath, stop_xpath):

    tree = html.parse(html_path)
    root = tree.getroot()

    start_node = tree.xpath(start_xpath)[0]
    stop_node  = tree.xpath(stop_xpath)[0]

    slice_nodes = []
    collecting = False

    for node in root.iter():

        if node is start_node:
            collecting = True
            

        if node is stop_node:
            break

        if not collecting:
            continue

        if node.tag == "hr":
            slice_nodes.append(node)
            continue

        if node.tag not in BLOCK_TAGS:
            continue

        text = re.sub(r'\s+', ' ', " ".join(node.itertext())).strip()
        if not text:
            continue

        if re.fullmatch(r"\d+", text):
            continue
        if text.lower() == "table of contents":
            continue

        slice_nodes.append(node)

    return slice_nodes

if __name__ == "__main__":
    html_path = "./data/10K_Filings/raw/MU/2018.html"
    
    json_path = "./data/processed_with_nodes/MU/2018.json"
    with open(json_path, "r") as f:
        data = json.load(f)

    start_xpath = data["sections"]["risk_factors"]["start_node"]
    stop_xpath = data["sections"]["risk_factors"]["stop_node"]

    print(f"Extracting DOM slice between {start_xpath} and {stop_xpath}")

    nodes = extract_dom_slice(html_path, start_xpath, stop_xpath)


  
    for i,node in enumerate(nodes):
        print("Node", html.tostring(node, pretty_print=True, encoding='unicode'), "Node text:", node.text_content().strip()[:100])
        print("-----")
        if i ==10:
            break
        