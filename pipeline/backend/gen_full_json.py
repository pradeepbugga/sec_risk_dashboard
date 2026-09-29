import json

from cluster.cluster_weights import compute_firm_year_cluster_weights
from cluster.drift import compute_yoy_drift
from cluster.cluster_deltas import compute_cluster_deltas
from cluster.industry_deviation import compute_deviation_from_industry
from cluster.firm_year_matrix_pct import compute_firm_year_matrix_pct
import numpy as np
import pandas as pd

from cluster.get_representative_chunks_year import get_representative_chunks_by_year
from cluster.firm_similarity import compute_firm_similarity_matrix





#create empty dict

json_data = {}

#populate ["macro_clusters"]

macro_clusters_path = "./data/adaptive_macroclustering/global_labels.json"

with open(macro_clusters_path, "r") as f:
    macro_clusters = json.load(f)

json_data["macro_clusters"] = macro_clusters

firm_list = ["AMD", "AVGO", "INTC", "MU", "NVDA", "QCOM", "TXN", "TSM"]
year_list = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]


# ---- Load macro centroids ----
macro_centroids = np.load("./data/adaptive_macroclustering/macro_centroids.npy")

# ---- Load macro metadata ----
with open("./data/adaptive_macroclustering/macro_metadata.json", "r") as f:
    macro_meta = json.load(f)

macro_cluster_ids = macro_meta["macro_cluster_ids"]

# ---- Load macro assignments ----
with open("./data/adaptive_macroclustering/macro_assignments.json", "r") as f:
    macro_assignments = json.load(f)

macro_df = pd.DataFrame(macro_assignments)

all_chunks = []

# ---- Load and merge chunk data for each firm ----
for firm in firm_list:

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


noise_clusters = [2,12, 15]

filtered_df = all_chunk_df[
    ~all_chunk_df["macro_cluster"].isin(noise_clusters)
].copy()

firm_year_matrix_pct = compute_firm_year_matrix_pct(filtered_df) # this contains all firms

industry_year_mean = (
    firm_year_matrix_pct
    .groupby("year")
    .mean()
)




firm_year_weights = compute_firm_year_cluster_weights(filtered_df)


json_data['firms'] = {}

for firm in firm_list:
    
    json_data['firms'][firm] = {}
    json_data['firms'][firm]['years'] = {}

   

    firm_year_pct = compute_firm_year_matrix_pct(
        filtered_df[filtered_df["firm"] == firm]
    )

    # Compute drift values
    drift_df = compute_yoy_drift(
        firm_year_pct, 
        firm
    )
    drift_df = drift_df.set_index("to_year")

    # compute industry deviation

    industry_deviation_df = compute_deviation_from_industry(
        firm_year_matrix_pct,
        industry_year_mean,
        firm
    )
    industry_deviation_df = industry_deviation_df.set_index("year")
 

    # compute cluster deltas
    cluster_deltas_df = compute_cluster_deltas(
        firm_year_pct, firm
    )




    for year in year_list:
        json_data['firms'][firm]['years'][str(year)] = {}

        
        #------ POPULATE CLUSTER WEIGHTS ------

        json_data['firms'][firm]['years'][str(year)]['cluster_weights'] = {}

        #create a dictionary of cluster weights for this firm-year  
        if (firm, year) in firm_year_weights.index:
            weights_series = firm_year_weights.loc[(firm, year)]
            for cluster_id in macro_cluster_ids:
                if cluster_id in [2,12,15]:
                    # skip
                    continue

                weight = weights_series.get(cluster_id, 0.0)
                json_data['firms'][firm]['years'][str(year)]['cluster_weights'][str(cluster_id)] = weight
        else:
            for cluster_id in macro_cluster_ids:
                json_data['firms'][firm]['years'][str(year)]['cluster_weights'][str(cluster_id)] = 0.0



        #------ POPULATE DRIFT VALUES ------

        json_data['firms'][firm]['years'][str(year)]['drift_from_prev'] = None

        if year in drift_df.index:
            drift_value = drift_df.loc[year, 'cosine_drift']
            json_data['firms'][firm]['years'][str(year)]['drift_from_prev'] = float(drift_value)


        #------ POPULATE INDUSTRY DEVIATION ------

        json_data['firms'][firm]['years'][str(year)]['industry_deviation'] = {}

        if year in industry_deviation_df.index:
            deviation_value = industry_deviation_df.loc[year]['deviation_from_industry']
            json_data['firms'][firm]['years'][str(year)]['industry_deviation'] = deviation_value
            

        #------ POPULATE CLUSTER DELTA VALUES ------

        json_data['firms'][firm]['years'][str(year)]['cluster_deltas'] = {}

        delta_rows = cluster_deltas_df[cluster_deltas_df['year'] == year]
        if not delta_rows.empty:
            delta_dict = delta_rows.iloc[0]['cluster_deltas']
            json_data['firms'][firm]['years'][str(year)]['cluster_deltas'] = delta_dict


        #------ POPULATE REPRESENTATIVE CHUNKS ------

        json_data['firms'][firm]['years'][str(year)]['representative_chunks'] = {}

        for macro_cluster_id in macro_cluster_ids:

            if macro_cluster_id in [2,12,15]:
                # skip
                continue

            rep_chunks_df = get_representative_chunks_by_year(
                chunk_df=filtered_df[filtered_df["firm"] == firm],
                macro_cluster_id=macro_cluster_id,
                centroid_matrix=macro_centroids,
                macro_cluster_ids=macro_cluster_ids,
                year=year,
                top_k=5
            )

            rep_chunks_list = []

            if rep_chunks_df is not None:
                for _, row in rep_chunks_df.iterrows():

                    rep_chunks_list.append({
                        "heading_path":  [str(x) for x in row["path"]],
                        "heading_text": row["heading"],
                        "level": row["level"],
                        "text": row["text"],
                        "similarity": row["similarity"]
                    })

            json_data['firms'][firm]['years'][str(year)]['representative_chunks'][str(macro_cluster_id)] = rep_chunks_list


#--------- POPULATE INDUSTRY VALUES ---------

json_data['industry'] = {}
json_data['industry']['similarity_matrix'] = {}

similarity_matrix = compute_firm_similarity_matrix(filtered_df)

for firm in firm_list:
    json_data['industry']['similarity_matrix'][firm] = {}
    for year in year_list:
        json_data['industry']['similarity_matrix'][firm][str(year)] = (
            similarity_matrix.get(firm, {}).get(str(year), {})
        )


# centroids

json_data['industry']['centroids'] = {}

industry_centroid = (firm_year_weights.fillna(0)
                     .groupby("year")
                     .mean())

for year in year_list:
    json_data['industry']['centroids'][str(year)] = {}
    if year in industry_centroid.index:
        centroid_series = industry_centroid.loc[year]
        for cluster_id in macro_cluster_ids:
            
            if cluster_id in [8,15]:
                # skip
                continue

            weight = centroid_series.get(cluster_id, 0.0)
            json_data['industry']['centroids'][str(year)][str(cluster_id)] = weight
    else:
        for cluster_id in macro_cluster_ids:
            json_data['industry']['centroids'][str(year)][str(cluster_id)] = 0.0








#output json

output_path = "./data/global_cluster_data.json"
with open(output_path, "w") as f:
    json.dump(json_data, f, indent=4)

       



    
