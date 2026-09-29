import json
import pandas as pd

from openai import OpenAI


def get_top_5_exposures(json_data, firm, year, macro_lookup):
     
    years_dict = json_data["firms"][firm]["years"] 

   
    dist_df = pd.DataFrame({
    year: years_dict[year]["cluster_weights"]
        for year in years_dict
    }).T.fillna(0)

    dist_df = dist_df.sort_index()

    total_weights = dist_df.sum().sort_values(ascending=False)
    dist_df = dist_df[total_weights.index]


    
    #get top 5 exposures for the given year
    year_weights = dist_df.loc[str(year)]

    top_5 = year_weights.sort_values(ascending=False).head(5)

    #generate labels for clusters
    top_exposures = []
    for cluster_id, weight in top_5.items():
        cluster_meta = macro_lookup.get(str(cluster_id), {})
        name = cluster_meta.get("label", f"Cluster {cluster_id}")
        top_exposures.append(f"{name}: {weight:.2%} ")

    # return top two cluster ids
    for i, (cluster_id, weight) in enumerate(top_5.items()):
        if i == 0:
            first_cluster_id = cluster_id
        if i == 1:
            second_cluster_id = cluster_id
            break
            
    return {
        "top_exposures": "; ".join(top_exposures),
        "first_cluster_id": first_cluster_id,
        "second_cluster_id": second_cluster_id
    }




def top_3_over_underindexed(data, firm, year, macro_lookup):
    years_dict = data["firms"][firm]["years"] 


    year = str(year)

    firm_weights = pd.Series(
        years_dict[year]["cluster_weights"]).astype(float)

    industry_weights = {}

     # --- Industry weights for selected year ---
    cluster_accumulator = []

    for other_firm in data["firms"]:
        if year in data["firms"][other_firm]["years"]:
            cluster_accumulator.append(
                data["firms"][other_firm]["years"][year]["cluster_weights"]
            )

    industry_df = pd.DataFrame(cluster_accumulator).fillna(0)

    industry_mean = industry_df.mean()
    industry_std = industry_df.std().replace(0, 1e-6)

    z = (firm_weights - industry_mean) / industry_std


    # top 3 positive differences
    over_indexed = z.sort_values(ascending=False).head(3)
    

    #identify cluster id for top difference
    top_cluster_id = over_indexed.index[0]


    over_labels = [
        macro_lookup[str(cid)]["label"]
        for cid in over_indexed.index
    ]
    over_strings = [
        f"{label}: +{value:.2f}σ"
        for label, value in zip(over_labels, over_indexed.values)
    ]
    over_result = "; ".join(over_strings)
    # top 3 negative differences
    under_indexed = z.sort_values(ascending=True).head(3)
    under_labels = [
        macro_lookup[str(cid)]["label"]
        for cid in under_indexed.index
    ]
    under_strings = [
        f"{label}: {value:.2f}σ"
        for label, value in zip(under_labels, under_indexed.values)
    ]
    under_result = ", ".join(under_strings)

    return {
        "over_indexed": over_result,
        "under_indexed": under_result,
        "top_cluster_id": top_cluster_id

    }



def global_drift(data, firm, year, macro_lookup):
    years_dict = data["firms"][firm]["years"] 

    year = str(year)

    year_drift = years_dict[year]["drift_from_prev"]

    #get all drift values historically
    drift_values = []
    for y in years_dict:
        if years_dict[y]["drift_from_prev"] is not None:
            drift_values.append(years_dict[y]["drift_from_prev"])

    #compute mean and std of drift values
    baseline_mean = pd.Series(drift_values).mean()
    baseline_std = pd.Series(drift_values).std()

    #average drift over last 3 years
    last_3_years = drift_values[-3:]
    trend = pd.Series(last_3_years).mean()    


    #calculate z score of latest
    z_score = (year_drift - baseline_mean) / baseline_std

    #round floats to 3 decimals
    return {"latest": f"{float(year_drift):.3g}",
            "trend": f"{float(trend):.3g}",
            "baseline_mean": f"{float(baseline_mean):.3g}",
            "baseline_std": f"{float(baseline_std):.3g}",
            "z_score": f"{float(z_score):.3g}"
            }


def cluster_drift(data, firm, year, macro_lookup):
    years_dict = data["firms"][firm]["years"] 


    from_year = str(year - 1)
    to_year = str(year)

    # --- Firm drift ---
    w1 = pd.Series(
        data["firms"][firm]["years"][from_year]["cluster_weights"]
    ).astype(float)

    w2 = pd.Series(
        data["firms"][firm]["years"][to_year]["cluster_weights"]
    ).astype(float)

    firm_delta = w2 - w1

    # --- Collect industry drift ---
    industry_deltas = []

    for other_firm in data["firms"]:

        years = data["firms"][other_firm]["years"]

        if from_year in years and to_year in years:

            ow1 = pd.Series(
                years[from_year]["cluster_weights"]
            ).astype(float)

            ow2 = pd.Series(
                years[to_year]["cluster_weights"]
            ).astype(float)

            industry_deltas.append(ow2 - ow1)

    industry_df = pd.DataFrame(industry_deltas).fillna(0)

    industry_mean = industry_df.mean()
    industry_std = industry_df.std().replace(0, 1e-6)

    # Align indices
    firm_delta = firm_delta.reindex(industry_mean.index).fillna(0)

    # --- Z score drift ---
    z_drift = (firm_delta - industry_mean) / industry_std


    # get top 3 drift positive
    over_drift = z_drift.sort_values(ascending=False).head(3)

    first_cluster_id = over_drift.index[0]

    under_drift = z_drift.sort_values(ascending=True).head(3)


    over_labels = [
        macro_lookup[str(cid)]["label"]
        for cid in over_drift.index
    ]

    under_labels = [
        macro_lookup[str(cid)]["label"]
        for cid in under_drift.index
    ]

    over_strings = [
        f"{label}: +{value:.2f}σ"
        for label, value in zip(over_labels, over_drift.values)
    ]

    under_strings = [   
        f"{label}: {value:.2f}σ"
        for label, value in zip(under_labels, under_drift.values)
    ]

    over_result = "; ".join(over_strings)
    under_result = ", ".join(under_strings)

    return {
        "over_drift": over_result,
        "under_drift": under_result,
        "first_cluster_id": first_cluster_id
    }

    return over_result, under_result, first_cluster_id


def cluster_top_snippet(data, firm, year, cluster_id, macro_lookup):

    years_dict = data["firms"][firm]["years"]
    year = str(year)
    cluster_id = str(cluster_id)

    chunks = years_dict[year]["representative_chunks"].get(cluster_id, [])

    if not chunks:
        
        return {
            "cluster_label": macro_lookup.get(cluster_id, {}).get("label", f"Cluster {cluster_id}"),
            "heading": None,
            "excerpt": None
        }

    # choose highest similarity chunk if available
    best_chunk = max(chunks, key=lambda x: x.get("similarity", 0))

    cluster_label = macro_lookup.get(cluster_id, {}).get("label", f"Cluster {cluster_id}")

    heading = " > ".join(best_chunk.get("heading_path", []))
    excerpt = best_chunk.get("text", "")

    return {
        "cluster_label": cluster_label,
        "heading": heading,
        "excerpt": excerpt
    }





