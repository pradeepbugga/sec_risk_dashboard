import json
import pandas as pd
from llm_api.prompt_helpers import get_top_5_exposures, top_3_over_underindexed, global_drift, cluster_drift, cluster_top_snippet
import os
from openai import OpenAI






def executive_summary_prompt(json_data, firm, year, macro_lookup):

    exposure_result = get_top_5_exposures(json_data, firm, year, macro_lookup)

    first_cluster_id = exposure_result["first_cluster_id"]
    second_cluster_id =exposure_result["second_cluster_id"]

    
    index_result = top_3_over_underindexed(data, firm, year, macro_lookup)
    over_indexed = index_result["over_indexed"]
    under_indexed = index_result["under_indexed"]   

    third_cluster_id = index_result["top_cluster_id"]

    global_drift_result = global_drift(data, firm, year, macro_lookup)
    latest = global_drift_result["latest"]
    baseline_mean = global_drift_result["baseline_mean"]
    baseline_std = global_drift_result["baseline_std"]
    trend = global_drift_result["trend"]
    zscore = global_drift_result["z_score"]

    cluster_drift_result = cluster_drift(data, firm, year, macro_lookup)
    over_drift = cluster_drift_result["over_drift"]
    under_drift = cluster_drift_result["under_drift"]

    fourth_cluster_id = cluster_drift_result["first_cluster_id"]

    unique_ids = set([
        first_cluster_id,
        second_cluster_id,
        third_cluster_id,
        fourth_cluster_id
    ])

    #snippets are in format: { "cluster": cluster_label, "heading": heading, "excerpt": excerpt }

    snippets = ""
    for cid in unique_ids:
        snippet_result = cluster_top_snippet(data, firm, year, cid, macro_lookup)
        cluster_label = snippet_result["cluster_label"]
        heading = snippet_result["heading"]
        excerpt = snippet_result["excerpt"]
        if heading is not None and excerpt is not None:
            snippets += f"Cluster: {cluster_label}\nHeading: {heading}\nExcerpt: {excerpt}\n\n"

  

    PROMPT = f"""         
            Firm: {firm}
            Year: {year}

            Structural Risk Exposure:
            {exposure_result['top_exposures']}

            Relative Positioning vs Industry:
            Over-indexed: {over_indexed}
            Under-indexed: {under_indexed}

            Narrative Drift:
            Latest drift: {latest}
            3-year trend: {trend}
            Z-score vs historical: {zscore} (mean: {baseline_mean}, std: {baseline_std})

            Representative Risk Language:
            {snippets}

            Write a concise 200–250 word executive risk brief including:
            - Dominant structural themes
            - How the firm differs from peers
            - Whether narrative risk is intensifying or stabilizing
            - Forward-looking implications
            Do not restate data mechanically. Synthesize it analytically.
            """
    
    return PROMPT


def call_API(data, firm, year, lookup):
    PROMPT = executive_summary_prompt(data , firm, year, lookup)

    client = OpenAI()

    response = client.responses.create(
        model="gpt-5-mini",
        reasoning ={"effort": "high"},
        input = [
            {"role": "system", "content": "You are a senior institutional equity risk analyst writing for a portfolio manager.."},
            {"role": "user", "content": PROMPT}
        ]
    )

    return response.output_text

if __name__ == "__main__":

    #------- import master json ------  

    with open("./data/global_cluster_data.json", "r") as f:
        data = json.load(f)

    macro_lookup = {
        str(c["cluster_id"]): c
        for c in data["macro_clusters"]
    }

    firm_list = list(data["firms"].keys())
    year = 2025

    for firm in firm_list:

        print(f"Generating executive summary for {firm} in {year}...")
        
       
        
        summary = call_API(data, firm, year, macro_lookup)
    
        #write to file
        output_path = f"./data/executive_summaries/{firm}/{year}.txt"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(summary)
