import json
import numpy as np

# -------- CONFIG --------
YEAR_BASE = 2018
YEAR_COMPARE = 2022
THRESHOLD = 0.40

BASE_PATH = "./data/embedded/INTC/risk_factors/"
# ------------------------

def load_year(year):
    with open(f"{BASE_PATH}{year}.json", "r") as f:
        return json.load(f)

def compute_theme_scores(chunks, theme_vec):
    scores = []
    for c in chunks:
        score = np.dot(c["embedding"], theme_vec)
        scores.append(score)
    return np.array(scores)

def compute_centroid(chunks, scores, threshold):
    selected = [
        c["embedding"]
        for c, s in zip(chunks, scores)
        if s > threshold
    ]
    if len(selected) == 0:
        raise ValueError("No chunks above threshold.")
    return np.mean(selected, axis=0)

# -------- LOAD DATA --------
chunks_2018 = load_year(YEAR_BASE)
chunks_2022 = load_year(YEAR_COMPARE)

# -------- LOAD THEME VECTOR (MUST MATCH PREVIOUS RUN) --------
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

theme_text = "new or revised export and import regulations, trade sanctions, and tariffs"
theme_vec = model.encode(theme_text, normalize_embeddings=True)

# -------- COMPUTE SCORES --------
scores_2018 = compute_theme_scores(chunks_2018, theme_vec)
scores_2022 = compute_theme_scores(chunks_2022, theme_vec)

# -------- COMPUTE CENTROIDS --------
centroid_2018 = compute_centroid(chunks_2018, scores_2018, THRESHOLD)
centroid_2022 = compute_centroid(chunks_2022, scores_2022, THRESHOLD)

# -------- COMPUTE DRIFT VECTOR --------
drift_vec = centroid_2022 - centroid_2018
drift_vec = drift_vec / np.linalg.norm(drift_vec)

# -------- PROJECT 2022 CHUNKS ONTO DRIFT VECTOR --------
drift_scores = []

for c in chunks_2022:
    score = np.dot(c["embedding"], drift_vec)
    drift_scores.append((score, c))

# Sort descending
drift_scores = sorted(drift_scores, key=lambda x: x[0], reverse=True)

# -------- PRINT TOP DRIFT DRIVERS --------
print("\nTop Drift-Driving Chunks (2022 vs 2018):\n")

for score, chunk in drift_scores[:5]:
    print("=" * 80)
    print(f"Drift Projection Score: {score:.4f}")
    print(f"Heading: {chunk['heading']}")
    print("Text Snippet:")
    print(chunk["text"][:2000])