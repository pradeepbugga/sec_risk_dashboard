import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def compute_firm_similarity_matrix(all_chunk_df):
    """
    Cosine similarity between every (firm, year) pair's macro-cluster
    exposure profile, weighted by chunk text length.

    Returns a nested dict: {firm: {year: {"OTHERFIRM_year": similarity}}}
    """
    df = all_chunk_df.copy()
    df["weight"] = df["text"].str.len()

    weighted = (
        df.groupby(["firm", "year", "macro_cluster"])["weight"]
        .sum()
        .reset_index()
    )

    pivot_weighted = weighted.pivot(
        index=["firm", "year"],
        columns="macro_cluster",
        values="weight",
    ).fillna(0)

    pivot_weighted_pct = pivot_weighted.div(pivot_weighted.sum(axis=1), axis=0)

    sim_matrix = cosine_similarity(pivot_weighted_pct)
    sim_df = pd.DataFrame(
        sim_matrix,
        index=pivot_weighted_pct.index,
        columns=pivot_weighted_pct.index,
    )

    result = {}
    for firm, year in sim_df.index:
        result.setdefault(firm, {})[str(year)] = {
            f"{other_firm}_{other_year}": float(sim_df.loc[(firm, year), (other_firm, other_year)])
            for other_firm, other_year in sim_df.columns
        }

    return result
