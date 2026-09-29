
import re
import unicodedata

def normalize_heading_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()



def find_risk_factor_heading(headings):
    candidates = []

    for i, h in enumerate(headings):
        text = normalize_heading_text(h["text"].strip().lower())
        
        if re.search(r"\brisk\s+factors\b", text, re.IGNORECASE):
            candidates.append((i, text))                        

    if not candidates:
        raise ValueError("Risk Factors heading not found")
 
    # Prefer Item 1A
    for i, text in candidates:
        if re.search(r"\bitem\s+1a\.?\b",text):
            return i
    
    # Otherwise choose shortest canonical heading
    return min(candidates, key=lambda x: len(x[1]))[0]