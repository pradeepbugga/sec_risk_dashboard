import re
from lxml import html
from filing_parser.utils.normalize import normalize_text


def extract_section_from_anchor(tree, start_header, stop_header=None):
    """
    Extract text between two anchor ids/names using document order traversal.
    """

    # Find start anchor
    start_nodes = tree.xpath(
        f'//*[@name="{start_header}"] | //*[@id="{start_header}"]'
    )

    if not start_nodes:
        print(f"No start anchor found for {start_header}")
        return None

    start_node = start_nodes[0]

    # Find stop anchor if provided
    stop_node = None
    if stop_header:
        stop_nodes = tree.xpath(
            f'//*[@name="{stop_header}"] | //*[@id="{stop_header}"]'
        )
        if stop_nodes:
            stop_node = stop_nodes[0]

    section_text = []

    # Traverse document order from start_node forward
    current_level = start_node
    while current_level.getparent() is not None and current_level.getnext() is None:
        current_level = current_level.getparent()

    # 4. Traverse siblings at that level
    # We use following::* but filter it to only include top-level elements 
    # that aren't contained within each other.
    last_processed = None
    
    # Grab all elements after the start_node in document order
    for node in start_node.xpath("following::*"):
        if stop_node is not None and node == stop_node:
            break
        
        # KEY FIX: If we just processed a node, and this current 'node' 
        # is actually INSIDE that previous node, skip it to avoid duplicates.
        if last_processed is not None and last_processed in node.xpath("ancestor::*"):
            continue

        text = node.text_content().strip()
        if text:
            section_text.append(text)
            last_processed = node # Update the "container" we just read

    return "\n".join(section_text), start_node, stop_node



if __name__ == "__main__":
    test_html = "./data/10-K_Filings/raw/TSM/2018.html"

    print(extract_section_from_anchor(test_html, "item1a_risk_factors"))

    #tree, start_header_risks, stop_header_risks, start_header_mda, stop_header_mda = extract_headers_20F(test_html)

    #risk_text = extract_section_from_anchor_20F(tree, start_header_risks, stop_header_risks)
    #mda_text = extract_section_from_anchor_20F(tree, start_header_mda, stop_header_mda)

    #risk_text = trim_to_risk_heading(risk_text)

    #print(risk_text[:1500])
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