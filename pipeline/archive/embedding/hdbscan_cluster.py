import json
import numpy as np
import glob
import os
from sklearn.preprocessing import normalize
import hdbscan
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


BASE_PATH = "./data/embedded/INTC/risk_factors/"

all_chunks = []
all_embeddings = []


#-------- LOAD ALL YEARS --------

for file in sorted(glob.glob(BASE_PATH + "*.json")):
    year = int(os.path.basename(file).replace(".json", ""))
    
    with open(file, "r") as f:
        chunks = json.load(f)
    
    for c in chunks:
        c["year"] = year
        all_chunks.append(c)
        all_embeddings.append(c["embedding"])

#-------- STACK EMBEDDINGS --------

all_embeddings = np.array(all_embeddings)

#-------- NORMALIZE EMBEDDINGS --------

all_embeddings = normalize(all_embeddings)

print(np.mean(np.linalg.norm(all_embeddings, axis=1)))

#-------- RUN HDBSCAN CLUSTERING --------

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=10,      # adjust later
    min_samples=5,
    metric='euclidean',       # cosine doesn't work directly
    cluster_selection_method='eom'
)

cluster_labels = clusterer.fit_predict(all_embeddings)

#-------- ATTACH CLUSTER LABELS TO CHUNKS --------
for c, label in zip(all_chunks, cluster_labels):
    c["cluster"] = int(label)

#-------- BUILD YEAR X CLUSTER MATRIX --------

year_cluster_counts = defaultdict(lambda: defaultdict(int))
year_total_counts = defaultdict(int)

for chunk in all_chunks:
    year = chunk["year"]
    cluster = chunk["cluster"]
    
    if cluster != -1:  # ignore noise
        year_cluster_counts[year][cluster] += 1
    
    year_total_counts[year] += 1

#-------- CONVERT TO TOPIC SHARES --------
rows = []

for year in sorted(year_cluster_counts.keys()):
    total = year_total_counts[year]
    
    for cluster, count in year_cluster_counts[year].items():
        share = count / total
        
        rows.append({
            "year": year,
            "cluster": cluster,
            "count": count,
            "share": share
        })

df = pd.DataFrame(rows)

#-------- PIVOT FOR HEATMAP --------
pivot = df.pivot(index="year", columns="cluster", values="share").fillna(0)

#-------- PRINT PIVOT TABLE --------
plt.figure(figsize=(12, 6))
sns.heatmap(pivot, cmap="viridis", annot=True, fmt=".2f")
plt.title("Risk Topic Share by Year (HDBSCAN Clusters)")
plt.show()


#-------- INTERPRET CLUSTERS --------
def print_cluster_examples(cluster_id, n=5):
    examples = [c for c in all_chunks if c["cluster"] == cluster_id]
    
    for e in examples[:n]:
        print("="*60)
        print(f"Year: {e['year']}")
        print(e["heading"])
        print(e["text"][:2000])

# Example: Print examples from cluster 1,11,12, and 8
for cid in [2,3, 4,12, 13, 15]:
    print(f"\n\n--- Examples from Cluster {cid} ---\n")
    print_cluster_examples(cid, n=3)


# Build full chunk-level DataFrame
chunk_df = pd.DataFrame(all_chunks)

# Exclude noise
chunk_df = chunk_df[chunk_df["cluster"] != -1]

# Total chunks per year (correct)
total_per_year = chunk_df.groupby("year").size()

# Counts per year per cluster (correct)
counts = (
    chunk_df
    .groupby(["year", "cluster"])
    .size()
    .unstack(fill_value=0)
)


total_series = pd.Series(year_total_counts)
total_series.index = total_series.index.astype(int)

counts.index = counts.index.astype(int)

shares = counts.div(total_series, axis=0)

# Shares (correct)
shares = counts.div(total_series, axis=0)

cluster_variance = shares.var()


print("\nCluster Variances:\n")
print(cluster_variance.sort_values(ascending=False))

clusters_to_check = [2,3, 4,12, 13, 15]

for c in clusters_to_check:
    table = pd.DataFrame({
        "raw_count": counts[c],
        "share": shares[c]
    })
    print(f"\n=== Cluster {c} ===")
    print(table)















print("HI")
for year in sorted(year_total_counts):
    print(year, year_total_counts[year])

pivot_counts = df.pivot(index="year", columns="cluster", values="count").fillna(0)
delta_counts = pivot_counts.diff()

#print("\nYear-over-Year Cluster Count Changes:\n")
#print(delta_counts.fillna(0).astype(int))
# Example: Print examples from clusters with largest increase in 2022
#increase_2022 = delta_counts.loc[2022].sort_values(ascending=False)

print(np.mean(cluster_labels == -1))

print(len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0))
