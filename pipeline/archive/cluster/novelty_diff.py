import json
import numpy as np
from sentence_transformers import SentenceTransformer

# -------- CONFIG --------
YEAR_BASE = 2018
YEAR_COMPARE = 2022
THRESHOLD = 0.40
BASE_PATH = "./data/embedded/INTC/risk_factors/"
# ------------------------

def load_year(year):
    with open(f"{BASE_PATH}{year}.json", "r") as f:
        return json.load(f)

# -------- LOAD DATA --------
chunks_2018 = load_year(YEAR_BASE)
chunks_2022 = load_year(YEAR_COMPARE)

# -------- LOAD THEME --------
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
theme_text = "Bureau of Industry and Security export license requirements and Entity List designations restricting sales to Chinese entities"
theme_vec = model.encode(theme_text, normalize_embeddings=True)

# -------- COMPUTE THEME SCORES --------
def compute_scores(chunks):
    return np.array([np.dot(c["embedding"], theme_vec) for c in chunks])

scores_2018 = compute_scores(chunks_2018)
scores_2022 = compute_scores(chunks_2022)

# -------- FILTER EXPORT-RELEVANT CHUNKS --------
export_2018 = [
    c["embedding"]
    for c, s in zip(chunks_2018, scores_2018)
    if s > THRESHOLD
]

export_2022 = [
    (c, s)
    for c, s in zip(chunks_2022, scores_2022)
    if s > THRESHOLD
]

export_2018 = np.array(export_2018)

# -------- NOVELTY-WEIGHTED DRIFT --------
results = []

for chunk, theme_score in export_2022:
    
    v = np.array(chunk["embedding"])
    
    # Compute similarity to all 2018 export chunks
    sims = np.dot(export_2018, v)
    max_similarity_2018 = np.max(sims)
    
    novelty = 1 - max_similarity_2018
    
    novelty_weighted_score = theme_score * novelty
    
    results.append((novelty_weighted_score, theme_score, novelty, chunk))

# Sort descending
results = sorted(results, key=lambda x: x[0], reverse=True)

# -------- PRINT TOP DRIFT-NOVELTY DRIVERS --------
print("\nTop Novelty-Weighted Drift Drivers:\n")

for score, theme_score, novelty, chunk in results[:5]:
    print("=" * 80)
    print(f"Novelty-Weighted Score: {score:.4f}")
    print(f"Theme Similarity: {theme_score:.4f}")
    print(f"Novelty vs 2018: {novelty:.4f}")
    print(f"Heading: {chunk['heading']}")
    print("Text Snippet:")
    print(chunk["text"][:500])