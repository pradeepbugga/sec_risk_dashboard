import pandas as pd
import numpy as np


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

    return pd.DataFrame(delta_records)