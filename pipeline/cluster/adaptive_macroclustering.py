import os
import glob
import json
import numpy as np

from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_distances


def cluster_internal_variance(points):
    if len(points) < 3:
        return 0.0
    dists = cosine_distances(points)
    return dists.mean()
    


def run_macroclustering_adaptive(
    base_micro_path="./data/microclustering/",
    n_macro_clusters=20,
    variance_threshold=0.25,
    min_cluster_fraction=0.20,
    n_subclusters=3
):
    """
    Adaptive macro clustering with optional subclustering of heterogeneous clusters.

    Parameters:
        n_macro_clusters: initial number of macro clusters
        variance_threshold: intra-cluster cosine distance threshold for splitting
        min_cluster_fraction: minimum fraction of total points to qualify for splitting
        n_subclusters: number of subclusters when splitting

    Returns:
        macro_assignments (list of dict)
    """

    firm_centroids = []
    metadata = []

    # ---- LOAD ALL MICRO CENTROIDS ----
    for firm_path in glob.glob(os.path.join(base_micro_path, "*")):
        risk_path = os.path.join(firm_path, "risk_factors")

        centroids_file = os.path.join(risk_path, "centroids.npy")
        summary_file = os.path.join(risk_path, "cluster_summary.json")

        if not os.path.exists(centroids_file):
            continue

        centroids = np.load(centroids_file)

        with open(summary_file, "r") as f:
            summary = json.load(f)

        cluster_ids = summary["cluster_ids"]
        firm_name = os.path.basename(firm_path)

        for i, cluster_id in enumerate(cluster_ids):
            firm_centroids.append(centroids[i])
            metadata.append({
                "firm": firm_name,
                "micro_cluster": int(cluster_id)
            })

    if len(firm_centroids) == 0:
        print("No centroids found.")
        return

    X = np.vstack(firm_centroids)
    X = normalize(X)

    # ---- INITIAL MACRO CLUSTERING ----
    clusterer = AgglomerativeClustering(
        n_clusters=n_macro_clusters,
        metric="cosine",
        linkage="average"
    )

    macro_labels = clusterer.fit_predict(X)

    total_points = len(X)
    unique_macro_ids = sorted(set(macro_labels))

    # ---- ADAPTIVE SPLITTING ----
    next_macro_id = max(unique_macro_ids) + 1
    new_macro_labels = macro_labels.copy()

    for macro_id in unique_macro_ids:

        mask = (macro_labels == macro_id)
        cluster_points = X[mask]

        cluster_size = len(cluster_points)
        cluster_fraction = cluster_size / total_points
        variance = cluster_internal_variance(cluster_points)

        print(f"Macro {macro_id}: size={cluster_size}, "
              f"fraction={cluster_fraction:.2f}, variance={variance:.3f}")

        if (
            cluster_fraction >= min_cluster_fraction and
            variance >= variance_threshold and
            cluster_size >= n_subclusters
        ):
            print(f" → Splitting macro cluster {macro_id}")

            subclusterer = AgglomerativeClustering(
                n_clusters=n_subclusters,
                metric="cosine",
                linkage="average"
            )

            sub_labels = subclusterer.fit_predict(cluster_points)

            # assign new macro ids
            for sub_id in range(n_subclusters):
                global_indices = np.where(mask)[0][sub_labels == sub_id]
                new_macro_labels[global_indices] = next_macro_id
                next_macro_id += 1

    macro_labels = new_macro_labels
    unique_macro_ids = sorted(set(macro_labels))

    # ---- BUILD ASSIGNMENTS ----
    macro_assignments = []

    for meta, macro_id in zip(metadata, macro_labels):
        macro_assignments.append({
            "firm": meta["firm"],
            "micro_cluster": meta["micro_cluster"],
            "macro_cluster": int(macro_id)
        })

    # ---- COMPUTE NEW MACRO CENTROIDS ----
    macro_centroids = []
    macro_cluster_ids = []

    for macro_id in unique_macro_ids:
        cluster_points = X[macro_labels == macro_id]
        centroid = cluster_points.mean(axis=0)
        centroid = centroid / np.linalg.norm(centroid)

        macro_centroids.append(centroid)
        macro_cluster_ids.append(int(macro_id))

    macro_centroids = np.vstack(macro_centroids)

    # ---- SAVE RESULTS ----
    os.makedirs("./data/adaptive_macroclustering/", exist_ok=True)

    np.save("./data/adaptive_macroclustering/macro_centroids.npy", macro_centroids)

    with open("./data/adaptive_macroclustering/macro_metadata.json", "w") as f:
        json.dump({"macro_cluster_ids": macro_cluster_ids}, f)

    with open("./data/adaptive_macroclustering/macro_assignments.json", "w") as f:
        json.dump(macro_assignments, f, indent=2)

    print(f"Final macro clusters: {len(unique_macro_ids)}")

    return macro_assignments


if __name__ == "__main__":
    run_macroclustering_adaptive(
        base_micro_path="./data/microclustering/",
        n_macro_clusters=20,
        variance_threshold=0.25,
        min_cluster_fraction=0.20,
        n_subclusters=3
    )