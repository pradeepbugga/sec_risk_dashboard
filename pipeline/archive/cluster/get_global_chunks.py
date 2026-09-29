import numpy as np
import os
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

def get_cluster_representatives_global(all_chunk_df,
                                       macro_cluster_id,
                                       centroid_matrix,
                                       macro_cluster_ids,
                                       top_k=15):

    idx = macro_cluster_ids.index(macro_cluster_id)
    centroid = centroid_matrix[idx]

    cluster_chunks = all_chunk_df[
        all_chunk_df["macro_cluster"] == macro_cluster_id
    ].copy()

    if cluster_chunks.empty:
        return None

    embeddings = np.vstack(cluster_chunks["embedding"].values)

    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    centroid = centroid / np.linalg.norm(centroid)

    sims = embeddings @ centroid
    cluster_chunks["similarity"] = sims

    cluster_chunks = cluster_chunks.sort_values("similarity", ascending=False)

        # Deduplicate
    embeddings = np.vstack(cluster_chunks["embedding"].values)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    selected_indices = []
    seen_vectors = []

    for idx, vec in zip(cluster_chunks.index, embeddings):
        if not seen_vectors:
            selected_indices.append(idx)
            seen_vectors.append(vec)
            continue

        sims = np.dot(seen_vectors, vec)
        if np.max(sims) < 0.95:
            selected_indices.append(idx)
            seen_vectors.append(vec)

    cluster_chunks = cluster_chunks.loc[selected_indices]

    # Firm diversity constraint
    cluster_chunks = cluster_chunks.groupby("firm").head(4)

    return cluster_chunks.head(top_k)

if __name__ == "__main__":

    firms = ["NVDA", "TXN", "INTC", "AVGO", "QCOM", "AMD", "MU"]

    # ---- Load macro centroids ----
    macro_centroids = np.load("./data/macroclustering/macro_centroids.npy")

    # ---- Load macro metadata ----
    with open("./data/macroclustering/macro_metadata.json", "r") as f:
        macro_meta = json.load(f)

    macro_cluster_ids = macro_meta["macro_cluster_ids"]

    # ---- Load macro assignments ----
    with open("./data/macroclustering/macro_assignments.json", "r") as f:
        macro_assignments = json.load(f)

    macro_df = pd.DataFrame(macro_assignments)

    all_chunks = []

    # ---- Load and merge chunk data for each firm ----
    for firm in firms:

        chunk_path = f"./data/microclustering/{firm}/risk_factors/chunk_data.parquet"
        chunk_df = pd.read_parquet(chunk_path)

        # Filter macro assignments for this firm
        firm_macro_df = macro_df[macro_df["firm"] == firm]

        # Merge macro labels into chunk_df
        chunk_df = chunk_df.merge(
            firm_macro_df,
            left_on="cluster",
            right_on="micro_cluster",
            how="left"
        )

        chunk_df["firm"] = firm

        all_chunks.append(chunk_df)

    # ---- Concatenate all firms ----
    all_chunk_df = pd.concat(all_chunks, ignore_index=True)

    print("All macro cluster IDs:")
    print(sorted(macro_cluster_ids))

    # ---- Choose macro cluster to inspect ----
    macro_cluster_id = 0

    rep = get_cluster_representatives_global(
        all_chunk_df,
        macro_cluster_id=macro_cluster_id,
        centroid_matrix=macro_centroids,
        macro_cluster_ids=macro_cluster_ids,
        top_k=25
    )

    if rep is None:
        print("No chunks found for cluster", macro_cluster_id)
    else:
        for _, row in rep.iterrows():
            print("\n---")
            print("Firm:", row["firm"])
            print("Year:", row["year"])
            print("Similarity:", round(row["similarity"], 4))
            print(row["text"][:600])


    # ---- Compute firm-cluster weighted presence ----

    all_chunk_df["weight"] = all_chunk_df["text"].str.len()


    print(all_chunk_df[all_chunk_df["macro_cluster"] == 3]["firm"].value_counts())


    
    weighted = (
        all_chunk_df
        .groupby(["firm", "year", "macro_cluster"])["weight"]
        .sum()
        .reset_index()
    )

    pivot_weighted = weighted.pivot(
        index=["firm","year"],
        columns="macro_cluster",
        values="weight"
    ).fillna(0)

    pivot_weighted_pct = pivot_weighted.div(
        pivot_weighted.sum(axis=1),
        axis=0
    )

    for firm in pivot_weighted_pct.index:
        print("\nFirm:", firm)
        print(
            pivot_weighted_pct.loc[firm]
            .sort_values(ascending=False)
            .head(5)
        )
    '''
    from sklearn.metrics.pairwise import cosine_similarity

    sim_matrix = cosine_similarity(pivot_weighted_pct)
    sim_df = pd.DataFrame(
        sim_matrix,
        index=pivot_weighted_pct.index,
        columns=pivot_weighted_pct.index
    )

    print(sim_df)
    
    #save as json

    sim_df.to_json("firm_similarity_macro_exposure.json")


    sim2_matrix = cosine_similarity(macro_centroids)

    sim2_df = pd.DataFrame(
        sim2_matrix,
        index=macro_cluster_ids,
        columns=macro_cluster_ids
    )
    
   
    noise_clusters = [8, 15]

    filtered_df = all_chunk_df[
        ~all_chunk_df["macro_cluster"].isin(noise_clusters)
    ].copy()

    filtered_df["weight"] = filtered_df["text"].str.len()

    weighted = (
        filtered_df
        .groupby(["firm", "year", "macro_cluster"])["weight"]
        .sum()
        .reset_index()
    )

    pivot_weighted = weighted.pivot_table(
        index=["firm", "year"],
        columns="macro_cluster",
        values="weight",
        fill_value=0
    )

    firm_year_exposure = pivot_weighted.div(
        pivot_weighted.sum(axis=1),
        axis=0
    )

    print(firm_year_exposure.loc["QCOM"].head(10))

    #convert to json

    exposure_json = firm_year_exposure.reset_index().to_json(orient="records")
    with open("firm_year_macro_exposure.json", "w") as f:
        f.write(exposure_json)
    '''















    '''
    #print to csv with pd
    with open("macro_cluster_similarity.csv", "w") as f:
        sim2_df.to_csv(f)

    '''

    

        
    firm_year_cluster = (
        all_chunk_df
        .groupby(["firm", "year", "macro_cluster"])["weight"]
        .sum()
        .reset_index()
    )

    #---- Pivot to create firm-year by macro cluster matrix ----

    firm_year_matrix = firm_year_cluster.pivot_table(
        index=["firm", "year"],
        columns="macro_cluster",
        values="weight",
        fill_value=0
    )

    #---- Normalize rows to get percentages ----

    firm_year_matrix_pct = firm_year_matrix.div(
        firm_year_matrix.sum(axis=1),
        axis=0
    )


    
    def compute_yoy_drift_all(firm_year_matrix_pct):

        drift_records = []

        for firm in firm_year_matrix_pct.index.get_level_values(0).unique():
            
            firm_data = firm_year_matrix_pct.loc[firm].sort_index()
            years = firm_data.index.tolist()

            for i in range(1, len(years)):

                prev_vec = firm_data.loc[years[i-1]].values.reshape(1, -1)
                curr_vec = firm_data.loc[years[i]].values.reshape(1, -1)

                sim = cosine_similarity(prev_vec, curr_vec)[0][0]

                drift_records.append({
                    "firm": firm,
                    "from_year": years[i-1],
                    "to_year": years[i],
                    "cosine_drift": 1 - sim
                })

        return pd.DataFrame(drift_records)

    def compute_cluster_deltas(firm_year_matrix_pct, firm):

        firm_data = firm_year_matrix_pct.loc[firm].sort_index()
        years = firm_data.index.tolist()

        delta_records = []

        for i in range(1, len(years)):

            prev_year = years[i-1]
            curr_year = years[i]

            delta = firm_data.loc[curr_year] - firm_data.loc[prev_year]

            top_moves = (
                delta.abs()
                .sort_values(ascending=False)
                .head(5)
            )

            delta_records.append({
                "firm": firm,
                "year": curr_year,
                "cluster_deltas": delta[top_moves.index].to_dict()
            })

        return delta_records

    drift_df = compute_yoy_drift_all(firm_year_matrix_pct)
    print(drift_df[drift_df["firm"] == "QCOM"].head(10))

    print("\nTop cluster moves per year for QCOM:")
    delta_records = compute_cluster_deltas(firm_year_matrix_pct, "QCOM")
    for record in delta_records:
        print("\nYear:", record["year"])
        for cluster, delta in record["cluster_deltas"].items():
            print(f"  Cluster {cluster}: Delta {round(delta,4)}")



    #print(df)

    #compute industry mean exposure drift

    industry_year_mean = (
        firm_year_matrix_pct
        .groupby("year")
        .mean()
    )

    def compute_deviation_from_industry(firm_year_matrix_pct, industry_year_mean, firm):
        
        firm_data = firm_year_matrix_pct.loc[firm]
        
        deviations = []
        
        for year in firm_data.index:
            firm_vec = firm_data.loc[year].values.reshape(1, -1)
            industry_vec = industry_year_mean.loc[year].values.reshape(1, -1)
            
            sim = cosine_similarity(firm_vec, industry_vec)[0][0]
            deviation = 1 - sim
            
            deviations.append({
                "firm": firm,
                "year": year,
                "deviation_from_industry": deviation
            })
        
        return pd.DataFrame(deviations)

    #deviation_df = compute_deviation_from_industry(firm_year_matrix_pct, industry_year_mean, "QCOM")
    #print(deviation_df)


    # alternative simpler calculation of year-over-year changes
    #print(firm_year_matrix_pct.loc["QCOM"].diff())

    #qcom_diff = firm_year_matrix_pct.loc["QCOM"].diff()

    #row_2020 = qcom_diff.loc[2020]
    #row_2020.abs().sort_values(ascending=False).head(5)
    #print(row_2020.abs().sort_values(ascending=False).head(5))
    
    '''
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    deviation_records = []

    for (firm, year), row in firm_year_matrix_pct.iterrows():
        
        firm_vec = row.values.reshape(1, -1)
        industry_vec = industry_year_mean.loc[year].values.reshape(1, -1)
        
        sim = cosine_similarity(firm_vec, industry_vec)[0][0]
        
        deviation_records.append({
            "firm": firm,
            "year": year,
            "cosine_deviation": 1 - sim,
            "L1_deviation": np.sum(np.abs(firm_vec - industry_vec))
        })

    deviation_df = pd.DataFrame(deviation_records)

    print(deviation_df[deviation_df["firm"] == "QCOM"].head(10))
    '''

    #--------- CLUSTER MOVEMENT ACROSS INDUSTRY MEAN OVER TIME ---------

    industry_delta = industry_year_mean.diff()

    def top_industry_shock(year, industry_delta, top_n=5):
    
        delta = industry_delta.loc[year]
        
        return (
            delta.abs()
            .sort_values(ascending=False)
            .head(top_n)
        )

    print(top_industry_shock(2022, industry_delta))

    industry_drift_records = []

    years = industry_year_mean.index.tolist()

    for i in range(1, len(years)):
        
        prev_vec = industry_year_mean.loc[years[i-1]].values.reshape(1, -1)
        curr_vec = industry_year_mean.loc[years[i]].values.reshape(1, -1)
        
        sim = cosine_similarity(prev_vec, curr_vec)[0][0]
        
        industry_drift_records.append({
            "from_year": years[i-1],
            "to_year": years[i],
            "industry_drift": 1 - sim
        })

    industry_drift_df = pd.DataFrame(industry_drift_records)

    print("\nIndustry mean drift over time:")
    print(industry_drift_df)