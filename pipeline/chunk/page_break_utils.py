
def is_page_break_node(node):
    tag = node.tag.lower()

    # Explicit page break rule
    if tag == "hr" and "page-break-after" in (node.attrib.get("style") or "").lower():
        return True
    return False
