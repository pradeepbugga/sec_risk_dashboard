import pandas as pd
import numpy as np


def compute_firm_year_matrix_pct(all_chunk_df):

    #---- Compute firm-year-cluster weights ----

    all_chunk_df = all_chunk_df.copy()

    # Weight definition (you can swap later)
    all_chunk_df["weight"] = all_chunk_df["text"].str.len()

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

    return firm_year_matrix_pct
