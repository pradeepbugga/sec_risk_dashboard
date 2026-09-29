import re

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