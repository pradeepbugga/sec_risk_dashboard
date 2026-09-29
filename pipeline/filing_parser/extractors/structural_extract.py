import json
from pathlib import Path
from lxml import html
from filing_parser.parsers.structural_parser import (
    clean_tree,
    extract_structural_item_headers,
    deduplicate_headers,
    extract_section_by_index
    )
from filing_parser.parsers.form_detector import detect_form_type



def load_form_section_map(config_path="./filing_parser/config/form_sections.json"):
    with open(config_path, "r") as f:
        return json.load(f)

def find_header(headers, number, letter):
    for h in headers:
        if h["number"] == number and h["letter"] == letter:
            return h
    return None


def extract_sections_structural(tree, form_type):

    tree = clean_tree(tree)

    FORM_SECTION_MAP = load_form_section_map()
    config = FORM_SECTION_MAP[form_type]

    headers = extract_structural_item_headers(tree)
    print(f"Extracted {len(headers)} headers")
    headers = deduplicate_headers(headers)

    #for header in headers:
    #    print(header)

    extracted = {}

    for section_name, section_config in config.items():

        start_number, start_letter = section_config["start"]
        stop_number, stop_letter = section_config["stop"]

        text, start_node, stop_node = extract_section_by_index(
            tree,
            headers,
            start_number,
            start_letter,
            stop_number,
            stop_letter
        )

        if text:

            extracted[section_name] = {}
            extracted[section_name]["text"] = text
            extracted[section_name]["start_node"] = start_node
            extracted[section_name]["stop_node"] = stop_node 

    return extracted

if __name__ == "__main__":
    html_path = "./data/20F_Filings/raw/TSM/2018.html"
    form_type = detect_form_type(html_path)
    tree = html.parse(html_path)
    extracted_sections = extract_sections_structural(tree, form_type)
    
    print(f"Extracted sections: {list(extracted_sections.keys())}")


    #for section, content in extracted_sections.items():
    #    print(f"Section: {section}\nContent: {content[:2100]}...\n")