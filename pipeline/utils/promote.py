def promote_to_block(node):
    while node is not None:

        parent = node.getparent()
        if parent is None:
            return node

        # Stop climbing when parent is body or table
        if parent.tag in ["body", "table"]:
            return node

        node = parent

    return None