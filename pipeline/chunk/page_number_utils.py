import re

def split_trailing_page_number(text):
    # Match number at end, optionally separated by space
    m = re.match(r"^(.*?)(\s*\b\d{1,4}\b)$", text)
    if not m:
        return text, None

    main = m.group(1).strip()
    number = m.group(2).strip()

    # Avoid splitting real numeric content like "Section 12"
    # Require that main part has reasonable length
    if len(main) > 10:
        return main, number

    return text, None