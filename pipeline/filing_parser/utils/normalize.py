import re

def normalize_text(text):
    text = text.replace('\xa0', ' ')

    # remove multiple newlines
    text = re.sub(r'\n+', '\n', text)

    text = text.strip()

    return text