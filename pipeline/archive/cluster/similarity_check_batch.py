import numpy as np
from sentence_transformers import SentenceTransformer
import json, os
from glob import glob
import pandas as pd

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

theme = "U.S. Bureau of Industry and Security export licensing restrictions on advanced semiconductor and AI chips to China"
theme_vec = model.encode(theme, normalize_embeddings=True)

def compute_theme_intensity(chunks, theme_vec, k=3):
    import numpy as np
    
    scores = [np.dot(c["embedding"], theme_vec) for c in chunks]
    scores.sort(reverse=True)
    return np.mean(scores[:k]), max(scores), sum(s > 0.40 for s in scores)


df_list = []


for chunk_file in glob("./data/embedded/INTC/risk_factors/*.json"):

    with open(chunk_file, "r") as f:
        chunks = json.load(f)
        
    scores = []

    for chunk in chunks:
        score = np.dot(chunk["embedding"], theme_vec)
        scores.append((score, chunk))
    
    scores = sorted(scores, key=lambda x: x[0], reverse=True)
   

    mean_top3, max_score, count_above_threshold = compute_theme_intensity(chunks, theme_vec)
    print(f"\nTheme Intensity Metrics:\nMean Top 3 Scores: {mean_top3}\nMax Score: {max_score}\nCount Above 0.40: {count_above_threshold}")

    #add metrics to csv
    #parse chunk_file to get year and company
    year = chunk_file.split("/")[-1].split(".")[0]
    company = chunk_file.split("/")[-4]


    df = pd.DataFrame({
        "company": [company],
        "year": [year],
        "mean_top3": [mean_top3],
        "max_score": [max_score],
        "count_above_0.40": [count_above_threshold],
        "query": [theme]
    })
    df_list.append(df)


#combine all dataframes
final_df = pd.concat(df_list, ignore_index=True)
os.makedirs("./data/theme_intensity/INTC/risk_factors/", exist_ok=True)
final_df.to_csv("./data/theme_intensity/INTC/risk_factors/metrics_2.csv", index=False)

print(f"✅ Saved theme intensity metrics to ./data/theme_intensity/INTC/risk_factors/metrics_2.csv")