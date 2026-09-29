import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity


def compute_yoy_drift(firm_year_matrix_pct, firm):
    
    firm_data = firm_year_matrix_pct.loc[firm]
    firm_data = firm_data.sort_index()  # sort by year
    
    years = firm_data.index.tolist()
    drifts = []
    
    for i in range(1, len(years)):
        prev_vec = firm_data.loc[years[i-1]].values.reshape(1, -1)
        curr_vec = firm_data.loc[years[i]].values.reshape(1, -1)
        
        sim = cosine_similarity(prev_vec, curr_vec)[0][0]
        drift = 1 - sim
        
        drifts.append({
            "firm": firm,
            "from_year": years[i-1],
            "to_year": years[i],
            "cosine_drift": drift
        })
    
    return pd.DataFrame(drifts)
