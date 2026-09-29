import json
from lxml import html
from filing_parser.main import process_file
from glob import glob
from pathlib import Path
from utils.promote import promote_to_block



def add_start_stop(input_json, output_dir):

    with open(input_json, "r") as f:
        data = json.load(f)


    output_path = Path(output_dir) / data['company'] / f"{data['year']}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print(f"Output file {output_path} already exists. Skipping.")
        return       

    
    if data.get('form_type') == "10-K":
        html_path = Path('./data/10K_Filings/raw') / data['company'] / f"{data['year']}.html"
    elif data.get('form_type') == "20-F":
        html_path = Path('./data/20F_Filings/raw') / data['company'] / f"{data['year']}.html"
    else:
        print(f"Unknown form type for {data['company']} {data['year']}")
        return
    
    

    processed, tree = process_file(html_path)
    if not processed or not tree:
        print(f"Failed to process {html_path}")
        return

    #iterate through keys in data.sections
    for key in data.get("sections", {}):
        if key in processed:
            start_node = processed[key].get("start_node")
            stop_node = processed[key].get("stop_node")

            print(start_node, stop_node)

            start_node = promote_to_block(start_node)
            stop_node = promote_to_block(stop_node)
            print(start_node, stop_node)

            data["sections"][key]["start_node"] = start_node.getroottree().getpath(start_node) if start_node is not None else None
            data["sections"][key]["stop_node"] = stop_node.getroottree().getpath(stop_node) if stop_node is not None else None
        else:
            print(f"Section {key} not found in processed data for {html_path}")         
    
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return


if __name__ == "__main__":
    input_jsons = Path("./data/processed").rglob("*.json")
    for json_path in input_jsons:
        add_start_stop(json_path, "./data/processed_with_nodes")
