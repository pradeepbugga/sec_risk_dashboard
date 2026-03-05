
def parse_summary(text):

    sections = []

    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]

    for block in blocks:

        # colon likely indicates header only if near beginning
        colon_pos = block.find(":")

        if 0 <= colon_pos <= 60:
            title = block[:colon_pos]
            content = block[colon_pos+1:]
        else:
            title = ""
            content = block

        sections.append((title.strip(), content.strip()))

    return sections