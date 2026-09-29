from pathlib import Path
from lxml import html, etree
from filing_parser.parsers.form_detector import detect_form_type
from filing_parser.extractors.anchor_extract import extract_section_from_anchor
from filing_parser.extractors.dom_extract import extract_section_from_anchor_flat
from filing_parser.extractors.structural_extract import extract_sections_structural, load_form_section_map
from filing_parser.parsers.toc_parser import parse_TOC
from filing_parser.parsers.dom_parser import dom_parse
from filing_parser.utils.trim import postprocess_20F_risk
from filing_parser.extractors.title_extract2 import extract_by_title
from filing_parser.extractors.node_extract import extract_section_from_nodes

DATA_DIR = "./data"


def parse_html(html_path):
    with open(html_path, "rb") as f:
        content = f.read()
    return html.fromstring(content)


def process_file(html_path):

    print(f"\nProcessing: {html_path}")

    tree = parse_html(html_path)

    form_type = detect_form_type(html_path)
    if not form_type:
        print("Could not detect form type")
        return None

    print(f"Detected form: {form_type}")

  
    FORM_SECTION_MAP = load_form_section_map()
    config = FORM_SECTION_MAP[form_type]
       
 
    # 1️⃣ Anchor attempt
    try:
        toc_dict = parse_TOC(tree)
        toc_dict = { (k[0], (None if k[1] == "" else k[1])): v for k, v in toc_dict.items() }
        

        sections = {}
        #get headers
        for section_name, section_config in config.items():
            start_num = int(section_config['start'][0])
            start_letter = section_config['start'][1] or None

            stop_num = int(section_config['stop'][0])
            stop_letter = section_config['stop'][1] or None

            start_header = toc_dict.get((start_num, start_letter))
            stop_header = toc_dict.get((stop_num, stop_letter))
            
            if not start_header or not stop_header:
                print(f"Missing headers for section: {section_name}")
                continue

       
            text, start_node, stop_node = extract_section_from_anchor(tree, start_header, stop_header)
           
            print("Start Node", start_node)
            print("Stop Node", stop_node)

            print((" ".join(start_node.getparent().itertext())))
            print((" ".join(stop_node.getparent().itertext())))



            if text:
                print(f"Extracting section: {section_name} from {start_header} to {stop_header}")
                sections[section_name] = {}

                if form_type == "20-F" and section_name == "risk_factors":
                    new_start_node, new_stop_node = postprocess_20F_risk(tree, start_node, stop_node)
                    text = extract_section_from_nodes(tree, new_start_node, new_stop_node)
                    start_node = new_start_node
                    stop_node = new_stop_node
                
                sections[section_name]["text"] = text
                sections[section_name]["start_node"] = start_node
                sections[section_name]["stop_node"] = stop_node

           
        if sections:
            sections['extractor'] = "anchor"
            print("Anchor extractor succeeded")
            return sections, tree
    except Exception as e:
        print(f"Anchor extractor failed: {e}")


    # 2️⃣ flattened anchor fallback
    try:
        toc_dict = dom_parse(tree)
        toc_dict = { (k[0], (None if k[1] == "" else k[1])): v for k, v in toc_dict.items() }
        

             
        sections = {}

        for section_name, section_config in config.items():

            start_num = int(section_config['start'][0])
            start_letter = section_config['start'][1] or None

            stop_num = int(section_config['stop'][0])
            stop_letter = section_config['stop'][1] or None

            start_header = toc_dict.get((start_num, start_letter))
            stop_header = toc_dict.get((stop_num, stop_letter))

            if not start_header or not stop_header:
                print(f"Missing headers for section: {section_name}")
                continue

            print(f"Extracting section: {section_name} from {start_header} to {stop_header}")

            text, start_node, stop_node = extract_section_from_anchor_flat(tree, start_header, stop_header)

            if text:
                sections[section_name] = {}

                #for 20-F risk factors, do postprocessing
                if form_type == "20-F" and section_name == "risk_factors":
                    new_start_node, new_stop_node = postprocess_20F_risk(tree, start_node, stop_node)
                    text = extract_section_from_nodes(tree, new_start_node, new_stop_node)
                    start_node = new_start_node
                    stop_node = new_stop_node
                
                sections[section_name]["text"] = text
                sections[section_name]["start_node"] = start_node
                sections[section_name]["stop_node"] = stop_node

        if sections:
            sections['extractor'] = "flattened"
            print("flattened extractor succeeded")
            return sections,tree

    except Exception as e:
        print(f"flattened extractor failed: {e}")

    # 3️⃣ Structural fallback
    
    try:
        print("Attempting structural extraction")
        sections = extract_sections_structural(tree, form_type)

        if form_type == "20-F" and "risk_factors" in sections:
            new_start_node, new_stop_node = postprocess_20F_risk(
                tree, 
                sections["risk_factors"]["start_node"],
                sections["risk_factors"]["stop_node"]
            )
            text = extract_section_from_nodes(tree, new_start_node, new_stop_node)
            sections["risk_factors"]["text"] = text
            sections["risk_factors"]["start_node"] = new_start_node
            sections["risk_factors"]["stop_node"] = new_stop_node

        if sections:
            print("Structural extractor succeeded")
            sections['extractor'] = "structural"
            return sections, tree
    except Exception as e:
        print(f"Structural extractor failed: {e}")


    #Title Extraction Fallback
    try:
        sections = {}
        print("Attempting title extraction")
        risk_text, start_node, stop_node = extract_by_title(
            tree,
            r"\bRISK FACTORS\b",
            stop_patterns = [
                r"UNRESOLVED STAFF COMMENTS",
                r"PROPERTIES"
            ]
        )

        if risk_text:
            sections["risk_factors"] = {}

            if form_type == "20-F":
                new_start_node, new_stop_node = postprocess_20F_risk(tree, start_node, stop_node)
                risk_text = extract_section_from_nodes(tree, new_start_node, new_stop_node)
                start_node = new_start_node
                stop_node = new_stop_node

            sections["risk_factors"]["text"] = risk_text
            sections["risk_factors"]["start_node"] = start_node
            sections["risk_factors"]["stop_node"] = stop_node


            print("Title extraction RISK FACTORS succeeded")
        
        mda_text, start_node, stop_node = extract_by_title(
            tree,
            r"\bMANAGEMENT'?S DISCUSSION.*",
            stop_patterns = [
                r"quantitative and qualitative disclosures"
            ]
        )
        if mda_text:
            sections["mda"] = {}
            sections["mda"]["text"] = mda_text
            sections["mda"]["start_node"] = start_node
            sections["mda"]["stop_node"] = stop_node
            print("Title extraction MDA succeeded")
        sections['extractor'] = "title"
        return sections, tree

    except Exception as e:
        print(f"Title extraction failed: {e}")

    
    print("All extractors failed")
    return None
   

def run_on_directory(directory):
    results = {}

    for file in Path(directory).rglob("*.htm*"):
        try:
            extracted = process_file(str(file))
            if extracted:
                results[str(file)] = extracted
        except Exception as e:
            print(f"Error processing {file}: {e}")

    return results


if __name__ == "__main__":
    #results = run_on_directory(DATA_DIR)
    #print(f"\nFinished. Parsed {len(results)} filings.")

    cleaned, tree =process_file("./data/20F_Filings/raw/TSM/2018.html")
    start_node = cleaned["risk_factors"]["start_node"]
    stop_node = cleaned["risk_factors"]["stop_node"]

    print(start_node.getroottree().getpath(start_node) if start_node is not None else None)
    print(start_node.text_content() if start_node is not None else None)
    #print(start_node.getparent().text_content() if start_node is not None else None)

    '''
    node = tree.xpath("/html/body/table[26]/tr/td[1]/b/a")[0]
    print("TAG:", node.tag)
    print("TEXT:", repr(" ".join(node.itertext())))

    parent = node.getparent()
    print("PARENT TAG:", parent.tag)
    print("PARENT TEXT:", repr(" ".join(parent.itertext())))

    grandparent = parent.getparent()
    print("GRANDPARENT TAG:", grandparent.tag)
    print("GRANDPARENT TEXT:", repr(" ".join(grandparent.itertext())))
    '''
    '''
    print(start_node.getroottree().getpath(start_node) if start_node is not None else None)
    print(stop_node.getroottree().getpath(stop_node) if stop_node is not None else None)


    print(cleaned["risk_factors"]["start_node"])
    print(cleaned["risk_factors"]["stop_node"])
    print(cleaned["mda"]["start_node"])
    print(cleaned["mda"]["stop_node"])

    print(cleaned["risk_factors"]["text"][:500])
    print(cleaned["mda"]["text"][:500])

    #start_node = cleaned["mda"]["start_node"]
    #print(etree.tostring(start_node, pretty_print=True, encoding="unicode"))
    #stop_node = cleaned["mda"]["stop_node"]
    #print(etree.tostring(stop_node, pretty_print=True, encoding="unicode"))

    #for key, value in cleaned.items():
    #    print(f"{key}: {value[:1500]}...")  # Print first 100 characters of each section
    
    #for key in cleaned:
    #    print(key)
    '''