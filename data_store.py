import json
import pandas as pd

# Load JSON once
with open("./data/global_cluster_data.json", "r") as f:
    data = json.load(f)

# load ticker mapping
df = pd.read_csv("./data/tickers.csv")


firms = list(data["firms"].keys())

# get cluster ids
macro_lookup = {
    str(c["cluster_id"]): c
    for c in data["macro_clusters"]
}

# in dropdown, show full company name, but value is ticker

dropdown_options = [
    {"label": row['Company_Name'], "value": row['Ticker']} 
    for _, row in df.iterrows()
]
