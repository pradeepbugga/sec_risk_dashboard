import re
from lxml import html
from filing_parser.utils.normalize import normalize_text


def extract_section_from_anchor_flat(tree, start_header, stop_header):

    start_nodes = tree.xpath(
        f'//*[@name="{start_header}"] | //*[@id="{start_header}"]'
    )
    stop_nodes = tree.xpath(
        f'//*[@name="{stop_header}"] | //*[@id="{stop_header}"]'
    )

    if not start_nodes:
        print(f"No start anchor found for {start_header}")
        return None

    if not stop_nodes:
        print(f"No stop anchor found for {stop_header}")
        return None

    start_node = start_nodes[0]
    stop_node = stop_nodes[0]

    all_nodes = list(tree.iter())

    try:
        start_index = all_nodes.index(start_node)
        stop_index = all_nodes.index(stop_node)
    except ValueError:
        print("Anchor nodes not found in flattened tree")
        return None

    if stop_index <= start_index:
        print("Stop appears before start — malformed document")
        return None

    section_text = []

    for node in all_nodes[start_index:stop_index]:

        # Only collect block-level containers
        if node.tag in {"div", "p", "td"}:
            text = node.text_content().strip()
            if text:
                section_text.append(text)

    return "\n".join(section_text), start_node, stop_node


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


if __name__ == "__main__":
    test_html = "./data/10-K_Filings/raw/TSM/2018.html"

    tree, start_header_risks, stop_header_risks, start_header_mda, stop_header_mda = extract_headers_20F(test_html)

    risk_text = extract_section_from_anchor_20F(tree, start_header_risks, stop_header_risks)
    mda_text = extract_section_from_anchor_20F(tree, start_header_mda, stop_header_mda)

    risk_text = trim_to_risk_heading(risk_text)

    print(risk_text[:1500])
    #print(mda_text[:1500])

    #print first 1500 characters 
    #print(text_output[:1500])
    #print(mda_text)

    #if you find "Item 1A" in the text, print the string
    #item_1a_pos = text_output.find("Item 1A")
    #if item_1a_pos != -1:
    #    print(text_output[item_1a_pos:item_1a_pos+100])
        

    #with open('./test2.txt', 'w', encoding='utf-8') as file:
    #   file.write(extract_text(test_html))


        # Further processing can be added here