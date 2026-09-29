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


BASE_PATH = "./data/embedded_with_heading/TXN/risk_factors/te3/"

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

year_cluster_words = defaultdict(lambda: defaultdict(int))
year_total_words = defaultdict(int)

for chunk in all_chunks:
    year = chunk["year"]
    cluster = chunk["cluster"]
    
    length = len(chunk["text"].split())
    
    if cluster != -1:
        year_cluster_words[year][cluster] += length
    
    year_total_words[year] += length

#-------- CONVERT TO TOPIC SHARES --------
rows = []

for year in sorted(year_cluster_words.keys()):
    total = year_total_words[year]
    
    for cluster, words in year_cluster_words[year].items():
        share = words / total
        
        rows.append({
            "year": year,
            "cluster": cluster,
            "word_count": words,
            "share": share
        })

df = pd.DataFrame(rows)





#-------- INTERPRET CLUSTERS --------
def print_cluster_examples(cluster_id, n=5):
    examples = [c for c in all_chunks if c["cluster"] == cluster_id]
    
    for e in examples[:n]:
        print("="*60)
        print(f"Year: {e['year']}")
        print(e["heading"])
        print(e["text"][:2000])
'''
# Example: Print examples from cluster 1,11,12, and 8
for cid in [0,1,2,3,4,5,6]:
    print(f"\n\n--- Examples from Cluster {cid} ---\n")
    print_cluster_examples(cid, n=3)
'''

# Build full chunk-level DataFrame
chunk_df = pd.DataFrame(all_chunks)

# Exclude noise
chunk_df = chunk_df[chunk_df["cluster"] != -1]


cluster_first_year = (
    chunk_df.groupby("cluster")["year"].min()
)

print("\nCluster First Appearance Years:\n")
print(cluster_first_year.sort_values())


risk_diversity = (
    chunk_df.groupby("year")["cluster"].nunique()
)
print("\nRisk Topic Diversity Over Years:\n")
print(risk_diversity)


#-------- PIVOT --------
pivot = df.pivot(index="year", columns="cluster", values="share").fillna(0)

# Ensure all clusters exist for all years
cluster_order = cluster_first_year.sort_values().index
pivot = pivot.reindex(columns=cluster_order, fill_value=0)

pivot = pivot.sort_index()

#-------- STACKED AREA --------
fig, ax = plt.subplots(figsize=(14,6))

pivot.plot.area(ax=ax)

ax.set_title("Risk Category Composition Over Time (Word-Weighted)")
ax.set_ylabel("Share of Total Risk Disclosure")
ax.set_xlabel("Year")

ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

plt.tight_layout()
plt.show()


for cluster in sorted(chunk_df["cluster"].unique()):
    texts = chunk_df[chunk_df["cluster"] == cluster]["text"]
    print(cluster)
    print(texts.iloc[0][:300])



for cluster_id in sorted(chunk_df["cluster"].unique()):

    subset = chunk_df[chunk_df["cluster"] == cluster_id]

    print("Cluster", cluster_id)
    print("\nUnique Headings:\n")

    print(
        subset["heading"]
        .value_counts()
        .head(20)
    )


# Build embedding matrix aligned with chunk_df
X = np.vstack(chunk_df["embedding"].values)

# Compute centroid per cluster
cluster_centroids = {}
for cluster in sorted(chunk_df["cluster"].unique()):
    cluster_embeddings = X[chunk_df["cluster"] == cluster]
    centroid = cluster_embeddings.mean(axis=0)
    cluster_centroids[cluster] = centroid

# Convert to array
clusters = list(cluster_centroids.keys())
centroid_matrix = np.vstack([cluster_centroids[c] for c in clusters])

# Normalize centroids (important for cosine geometry)
centroid_matrix = normalize(centroid_matrix)

import umap

reducer = umap.UMAP(
    n_neighbors=5,
    min_dist=0.2,
    metric="cosine",
    random_state=42
)

centroid_2d = reducer.fit_transform(centroid_matrix)

plt.figure(figsize=(10,8))

for i, cluster in enumerate(clusters):
    x, y = centroid_2d[i]
    plt.scatter(x, y)
    plt.text(x, y, str(cluster), fontsize=9)

plt.title("Cluster Centroids (2D Projection)")
plt.xlabel("Dim 1")
plt.ylabel("Dim 2")
plt.tight_layout()
plt.show()

from sklearn.metrics.pairwise import cosine_similarity

similarity_matrix = cosine_similarity(centroid_matrix)

similar_pairs = []

pairs = []

for i in range(len(clusters)):
    for j in range(i+1, len(clusters)):
        sim = similarity_matrix[i, j]
        pairs.append((clusters[i], clusters[j], sim))

pairs_sorted = sorted(pairs, key=lambda x: -x[2])

for p in pairs_sorted[:10]:
    print(p)

def print_cluster_paragraphs(cluster_id, n=5):
    subset = chunk_df[chunk_df["cluster"] == cluster_id]
    
    print(f"\n===== Cluster {cluster_id} =====")
    print(f"Total paragraphs: {len(subset)}\n")
    
    for i, (_, row) in enumerate(subset.head(n).iterrows()):
        print(f"--- Paragraph {i+1} (Year {row['year']}) ---")
        print(f"Heading: {row['heading']}")
        print(row["text"])
        print("\n")

print_cluster_paragraphs(0, n=5)
print_cluster_paragraphs(1, n=5)
print_cluster_paragraphs(2, n=5)
print_cluster_paragraphs(3, n=5)
print_cluster_paragraphs(4, n=5)
print_cluster_paragraphs(5, n=5)
print_cluster_paragraphs(6, n=5)

