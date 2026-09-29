
import pandas as pd
import numpy as np


def compute_firm_year_cluster_weights(all_chunk_df, normalize=True):

    df = all_chunk_df.copy()

    # Weight definition (you can swap later)
    df["weight"] = df["text"].str.len()

    # Aggregate weight per firm-year-cluster
    weighted = (
        df
        .groupby(["firm", "year", "macro_cluster"])["weight"]
        .sum()
        .reset_index()
    )

    # Pivot into matrix
    pivot_weighted = weighted.pivot(
        index=["firm", "year"],
        columns="macro_cluster",
        values="weight"
    ).fillna(0)

    if normalize:
        pivot_weighted = pivot_weighted.div(
            pivot_weighted.sum(axis=1),
            axis=0
        )

    return pivot_weighted