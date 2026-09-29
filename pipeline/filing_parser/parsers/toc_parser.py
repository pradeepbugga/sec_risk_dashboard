import re
from lxml import html
from filing_parser.utils.normalize import normalize_text


ITEM_PATTERN = re.compile(
    r'^ITEM\s+([0-9]+)([A-Z]?)\.', 
    re.IGNORECASE
)

def parse_TOC(tree):

    
    

    rows = tree.xpath('//tr')
    
    toc_dict = {}

    for row in rows:
        row_text = normalize_text(row.text_content()).upper()

        match = ITEM_PATTERN.search(row_text)
        if not match:
            continue

        item_num = int(match.group(1))
        item_letter = match.group(2)

        # Find anchor link in this row
        link = row.xpath('.//a[contains(@href, "#")]')
        if not link:
            continue

        href = link[0].get('href')
        if not href or not href.startswith('#'):
            continue

        anchor_id = href[1:]  # remove '#'

        toc_dict[(item_num, item_letter)] = anchor_id

    return  toc_dict

if __name__ == "__main__":
    html_path = "./data/10K_Filings/raw/INTC/2018.html"

    toc_dict = parse_TOC(html_path)

    print("Table of Contents Dictionary:")
    #for key, value in toc_dict.items():
    #    print(f"Item {key[0]}{key[1] or ''}: {value}")
    for key in toc_dict:
        print(key, toc_dict[key])


