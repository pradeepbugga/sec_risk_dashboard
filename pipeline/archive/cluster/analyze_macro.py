import json
import pandas as pd
import numpy as np
import os

with open("./data/macroclustering/macro_assignments.json", "r") as f:
    macro_assignments = json.load(f)

macro_df = pd.DataFrame(macro_assignments)

# Create mapping: (firm, micro_cluster) → macro_cluster
macro_lookup = {
    (row["firm"], row["micro_cluster"]): row["macro_cluster"]
    for _, row in macro_df.iterrows()
}

base_micro_path = "./data/microclustering/"

rows = []

for firm in os.listdir(base_micro_path):

    chunk_path = os.path.join(
        base_micro_path, firm, "risk_factors", "chunk_data.parquet"
    )

    if not os.path.exists(chunk_path):
        continue

    chunk_df = pd.read_parquet(chunk_path)

    # Map to macro cluster
    chunk_df["macro_cluster"] = chunk_df["cluster"].apply(
        lambda x: macro_lookup.get((firm, int(x)), None)
    )

    chunk_df = chunk_df.dropna(subset=["macro_cluster"])

    # Word length
    chunk_df["word_count"] = chunk_df["text"].str.split().str.len()

    # Compute shares
    grouped = (
        chunk_df
        .groupby(["year", "macro_cluster"])["word_count"]
        .sum()
        .reset_index()
    )

    total_words = (
        chunk_df
        .groupby("year")["word_count"]
        .sum()
        .reset_index()
        .rename(columns={"word_count": "total_words"})
    )

    grouped = grouped.merge(total_words, on="year")
    grouped["share"] = grouped["word_count"] / grouped["total_words"]
    grouped["firm"] = firm

    rows.append(grouped)

firm_year_macro = pd.concat(rows, ignore_index=True)

txn_df = firm_year_macro[firm_year_macro["firm"] == "TXN"]

pivot = (
    txn_df
    .pivot(index="year", columns="macro_cluster", values="share")
    .fillna(0)
    .sort_index()
)

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 6))

pivot.plot.area(ax=ax)

ax.set_title("TXN Risk Exposure by Macro Cluster")
ax.set_ylabel("Share of Total Risk Disclosure")
ax.set_xlabel("Year")

ax.legend(title="Macro Cluster", bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.show()






industry_raw = (
    firm_year_macro
    .groupby(["year","macro_cluster"])["word_count"]
    .sum()
    .reset_index()
)

total_words = (
    industry_raw.groupby("year")["word_count"]
    .transform("sum")
)

industry_raw["share"] = industry_raw["word_count"] / total_words

#Pivot for plotting
industry = (
    industry_raw
    .pivot(index="year", columns="macro_cluster", values="share")
    .fillna(0)
    .sort_index()
)   
fig, ax = plt.subplots(figsize=(12, 6))
industry.plot.area(ax=ax)
ax.set_title("Industry Risk Exposure by Macro Cluster")
ax.set_ylabel("Share of Total Risk Disclosure")
ax.set_xlabel("Year")
ax.legend(title="Macro Cluster", bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.show()


'''
# Compute deviation of firm from industry
merged = firm_year_macro.merge(
    industry,
    on=["year", "macro_cluster"],
    suffixes=("_firm", "_industry")
)



merged["deviation"] = merged["share_firm"] - merged["share_industry"]

txn_deviation = merged[merged["firm"] == "TXN"]
# Pivot for plotting
deviation_pivot = (
    txn_deviation
    .pivot(index="year", columns="macro_cluster", values="deviation")
    .fillna(0)
    .sort_index()
)   
fig, ax = plt.subplots(figsize=(12, 6))
deviation_pivot.plot.area(ax=ax)
ax.set_title("TXN Deviation from Industry Risk Exposure by Macro Cluster")
ax.set_ylabel("Deviation in Share of Total Risk Disclosure")
ax.set_xlabel("Year")
ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
ax.legend(title="Macro Cluster", bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.show()
'''