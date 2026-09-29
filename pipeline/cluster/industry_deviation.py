import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


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