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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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


chunk_df = pd.DataFrame(all_chunks)

#print columns names
print(chunk_df.columns)

cluster_drift_results = {}

for cluster_id in sorted(chunk_df["cluster"].unique()):

    cluster_data = chunk_df[chunk_df["cluster"] == cluster_id]

    texts = cluster_data["text"].tolist()
    years = cluster_data["year"].tolist()

    if len(texts) < 20:
        continue  # skip tiny clusters

    # ---- TF-IDF within cluster ----
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words='english',
        ngram_range=(1,2),
        min_df=3,
        max_df=0.85
    )

    X = vectorizer.fit_transform(texts)

    tfidf_df = pd.DataFrame(X.toarray(), columns=vectorizer.get_feature_names_out())
    tfidf_df["year"] = years

    # ---- Compute year centroids ----
    year_means = tfidf_df.groupby("year").mean()

    baseline_year = 2018
    if baseline_year not in year_means.index:
        continue

    baseline_vec = year_means.loc[baseline_year].values.reshape(1, -1)

    drift_by_year = {}

    for year in year_means.index:
        year_vec = year_means.loc[year].values.reshape(1, -1)
        similarity = cosine_similarity(baseline_vec, year_vec)[0][0]
        drift = 1 - similarity
        drift_by_year[year] = drift

    cluster_drift_results[cluster_id] = drift_by_year

#-------- CONVERT TO DATAFRAME --------
drift_df = pd.DataFrame(cluster_drift_results).T
drift_df.index.name = "cluster"
drift_df.columns.name = "year"


#-------- PLOT HEATMAP --------
plt.figure(figsize=(12, 6))
sns.heatmap(drift_df, cmap="YlGnBu", annot=True, fmt=".2f")
plt.title("Cluster Drift Over Years (HDBSCAN Clusters)")
#plt.show()

baseline_year = 2018
compare_year = 2022

X_global = vectorizer.fit_transform(chunk_df["text"])
feature_names = vectorizer.get_feature_names_out()

for cluster_id in sorted(chunk_df["cluster"].unique()):
    
      
    cluster_mask = (chunk_df["cluster"] == cluster_id).values
    cluster_df = chunk_df[cluster_mask]

    # ---- Count paragraphs per year ----
    counts_per_year = cluster_df.groupby("year").size()

    print(f"\nCluster {cluster_id} year counts:")
    print(counts_per_year)


    if cluster_df.shape[0] < 20:
        print(f"\n\n=== Cluster {cluster_id} skipped due to small size ===")
        continue  # skip tiny clusters


    if len(counts_per_year) < 5:
        print(f"\n\n=== Cluster {cluster_id} skipped due to insufficient years ===")
        continue # skip clusters without enough years

       # ---- Use dynamic baseline ----
    baseline_year = counts_per_year.index.min()

    print(f"Using baseline year: {baseline_year}")




    # Subset TF-IDF rows
    X_cluster = X_global[cluster_mask]

    years_cluster = cluster_df["year"].values

    # Separate baseline and comparison year
    baseline_mask = (years_cluster == baseline_year)
    compare_mask = (years_cluster == compare_year)

   

    if baseline_mask.sum() == 0 or compare_mask.sum() == 0:
        print(f"\n\n=== Cluster {cluster_id} skipped due to insufficient data in baseline or comparison year ===")
       
        continue
        
    baseline_vec = X_cluster[baseline_mask].mean(axis=0)
    compare_vec = X_cluster[compare_mask].mean(axis=0)

    drift = np.asarray(compare_vec - baseline_vec).ravel()

    top_idx = drift.argsort()[::-1][:20]

    print(f"\n\n=== Cluster {cluster_id} ===")
    print("Top Positive Drift Terms:\n")
    
    for idx in top_idx:
        print(f"{feature_names[idx]:30s}  {drift[idx]:.5f}")











'''
#print(chunk_df.groupby("year")["heading"].nunique())

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
for cid in [0,1,2,3,4,5,6]:
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

clusters_to_check = [0,1,2,3,4,5,6]

for c in clusters_to_check:
    table = pd.DataFrame({
        "raw_count": counts[c],
        "share": shares[c]
    })
    print(f"\n=== Cluster {c} ===")
    print(table)





'''









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
