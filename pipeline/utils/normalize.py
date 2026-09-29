import re

def normalize_text(text):
    
    if not text:
        return None
    
    # Replace non-breaking spaces with regular spaces
    text = text.replace('\xa0', ' ')


    # Replace carriage returns with newlines
    text = re.sub(r'\r', '\n', text)

    # Replace multiple newlines with a single newline
    text = re.sub(r'\n\s*\n', '\n\n', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    # Strip leading and trailing whitespace
    text = text.strip()

    return text