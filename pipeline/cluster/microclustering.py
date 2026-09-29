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
     


def run_microclustering(ticker):

    #check that the paths exist

    embed_path = f"./data/embedded_with_heading/{ticker}/risk_factors/te3/"

    
    if not os.path.exists(embed_path):
        print(f"Embedding path {embed_path} does not exist.")
        return


    
    all_chunks = []
    all_embeddings = []


    #make sure there are files for 2018-2025  (embed_path + "2018.json")


    try:
        for year in range(2018, 2026):
            file_path = os.path.join(embed_path, f"{year}.json")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Missing year file: {file_path}")
    
           #-------- LOAD ALL YEARS --------

        for file in sorted(glob.glob(embed_path + "*.json")):
            
            year = int(os.path.basename(file).replace(".json", ""))
            
            with open(file, "r") as f:
                chunks = json.load(f)
            
            for c in chunks:
                c["year"] = year
                all_chunks.append(c)
                all_embeddings.append(c["embedding"])

    except FileNotFoundError as e:
        print("Data missing:", e)
        return
    except json.JSONDecodeError as e:
        print(f"Error: found a corrupted JSON file: {e}")
        return
    except Exception as e:
        print("An unexpected error occurred:", e)
        return
        
    #-------- STACK EMBEDDINGS --------

    all_embeddings = np.array(all_embeddings)

    #-------- NORMALIZE EMBEDDINGS --------

    all_embeddings = normalize(all_embeddings)

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

        # Build full chunk-level DataFrame
    chunk_df = pd.DataFrame(all_chunks)

    # Exclude noise
    chunk_df = chunk_df[chunk_df["cluster"] != -1]


    
    cluster_sizes = chunk_df["cluster"].value_counts()

    valid_clusters = cluster_sizes[cluster_sizes >= 8].index

    chunk_df = chunk_df[chunk_df["cluster"].isin(valid_clusters)]

    cluster_sizes = chunk_df["cluster"].value_counts()

    if chunk_df.empty:
        print("No valid clusters after filtering.")
        return

    # Build embedding matrix aligned with chunk_df
    X = np.vstack(chunk_df["embedding"].values)

    # Compute centroid per cluster
    cluster_centroids = {}
    for cluster in sorted(chunk_df["cluster"].unique()):
        cluster_embeddings = np.vstack(
            chunk_df[chunk_df["cluster"] == cluster]["embedding"].values
        )
        centroid = cluster_embeddings.mean(axis=0)
        cluster_centroids[cluster] = centroid

    # Convert to array
    clusters = [int(c) for c in cluster_centroids.keys()]
    cluster_sizes_clean = {int(k): int(v) for k, v in cluster_sizes.to_dict().items()}
    centroid_matrix = np.vstack([cluster_centroids[c] for c in clusters])

    # Normalize centroids (important for cosine geometry)
    centroid_matrix = normalize(centroid_matrix)

    #need to return chunk_df.parquet, centroids.npy and cluster_summary.json
    os.makedirs(f"./data/microclustering/{ticker}/risk_factors/", exist_ok=True)
    chunk_df.to_parquet(f"./data/microclustering/{ticker}/risk_factors/chunk_data.parquet", index=False)
    np.save(f"./data/microclustering/{ticker}/risk_factors/centroids.npy", centroid_matrix) 
    with open(f"./data/microclustering/{ticker}/risk_factors/cluster_summary.json", "w") as f:
        json.dump({
            "cluster_ids": clusters,
            "cluster_sizes": cluster_sizes_clean,
            "num_clusters": int(len(clusters))
        }, f)

    return chunk_df, centroid_matrix, clusters

if __name__ == "__main__":
    ticker = 'INTC'
    run_microclustering(ticker)