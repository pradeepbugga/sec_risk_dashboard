def extract_section_from_nodes(tree, start_node, stop_node=None):
    section_text = []

    for node in start_node.xpath("./following::*"):
        if stop_node is not None and node == stop_node:
            break

        text = node.text_content().strip()
        if text:
            section_text.append(text)

    return "\n".join(section_text)