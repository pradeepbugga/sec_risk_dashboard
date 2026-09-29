import numpy as np
import os
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

def get_representative_chunks_by_year(chunk_df, macro_cluster_id,
                              centroid_matrix,
                              macro_cluster_ids,year,
                              top_k=15):

    # Get centroid index
    idx = macro_cluster_ids.index(macro_cluster_id)
    centroid = centroid_matrix[idx]

    # Filter chunks belonging to macro cluster
    cluster_chunks = chunk_df[
        (chunk_df["macro_cluster"] == macro_cluster_id) & 
        (chunk_df["year"] == year)
    ].copy()

    if cluster_chunks.empty:
        return None

    # Stack embeddings
    embeddings = np.vstack(cluster_chunks["embedding"].values)

    # Ensure normalized
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    centroid = centroid / np.linalg.norm(centroid)

    # Cosine similarity (dot product)
    sims = embeddings @ centroid

    cluster_chunks["similarity"] = sims

    # Sort descending
    cluster_chunks = cluster_chunks.sort_values(
        by="similarity",
        ascending=False
    )

    return cluster_chunks.head(top_k)







if __name__ == "__main__":

    firm = "QCOM"

    # ---- Load chunk data ----
    chunk_path = f"./data/microclustering/{firm}/risk_factors/chunk_data.parquet"
    chunk_df = pd.read_parquet(chunk_path)

    # ---- Load macro centroids ----
    macro_centroids = np.load("./data/macroclustering/macro_centroids.npy")

    # ---- Load macro cluster ids ----
    with open("./data/macroclustering/macro_metadata.json", "r") as f:
        macro_meta = json.load(f)

    macro_cluster_ids = macro_meta["macro_cluster_ids"]

    # ---- Load macro assignments ----
    with open("./data/macroclustering/macro_assignments.json", "r") as f:
        macro_assignments = json.load(f)

    macro_df = pd.DataFrame(macro_assignments)

    # Filter to this firm
    macro_df = macro_df[macro_df["firm"] == firm]

    # Merge macro labels into chunk_df
    chunk_df = chunk_df.merge(
        macro_df,
        left_on="cluster",
        right_on="micro_cluster",
        how="left"
    )

    # Now chunk_df has "macro_cluster"


    print("Available macro clusters for QCOM:")
    print(sorted(chunk_df["macro_cluster"].dropna().unique()))

    print("All macro cluster IDs:")
    print(sorted(macro_cluster_ids))

 

    rep = get_representative_chunks_by_year(
    chunk_df,
    macro_cluster_id=0,
    centroid_matrix=macro_centroids,
    macro_cluster_ids=macro_cluster_ids, year = 2018,
    top_k=20
)

    for i, row in rep.iterrows() if rep is not None else []:
        print("\n---")
        print("Year:", row["year"])
        print("Similarity:", round(row["similarity"], 4))
        print(row["text"][:600])

    from collections import Counter
    Counter([a["macro_cluster"] for a in macro_assignments])
    print(Counter([a["macro_cluster"] for a in macro_assignments]))

    