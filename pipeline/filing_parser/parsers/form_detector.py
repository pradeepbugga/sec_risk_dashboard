from lxml import html

def detect_form_type(html_path):
    with open(html_path, 'rb') as f:
        tree = html.fromstring(f.read())


    for div in tree.xpath('//div[@style="display:none"]'):
        div.getparent().remove(div)



    text = tree.text_content().upper()

    
    #remove empty lines
    text = "\n".join([line for line in text.splitlines() if line.strip()])

    #remove whitespace 
    text = " ".join(text.split())


    if "FORM 20-F" in text[:10000]:
        return "20-F"
    if "FORM 10-K" in text[:10000]:
        return "10-K"

    return "UNKNOWN"



if __name__ == "__main__":
    html_path = "./data/10K_Filings/raw/INTC/2021.html"
    form_type = detect_form_type(html_path)
    print(f"Detected form type: {form_type}")