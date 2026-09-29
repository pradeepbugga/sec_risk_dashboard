import numpy as np
from sentence_transformers import SentenceTransformer
import json


model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

with open("./data/embedded/INTC/risk_factors/2022.json", "r") as f:
    chunks = json.load(f)

theme = "new or revised export and import regulations, trade sanctions, and tariffs"
theme_vec = model.encode(theme, normalize_embeddings=True)

scores = []

for chunk in chunks:
    score = np.dot(chunk["embedding"], theme_vec)
    scores.append((score, chunk))

scores = sorted(scores, key=lambda x: x[0], reverse=True)

for score, chunk in scores[:5]:
    print("\n---")
    print("Score:", score)
    print("Heading:", chunk["heading"])
    print("Text:", chunk["text"][:1000])  # truncate for readability

def compute_theme_intensity(chunks, theme_vec, k=3):
    import numpy as np
    
    scores = [np.dot(c["embedding"], theme_vec) for c in chunks]
    scores.sort(reverse=True)
    return np.mean(scores[:k]), max(scores), sum(s > 0.40 for s in scores)

mean_top3, max_score, count_above_threshold = compute_theme_intensity(chunks, theme_vec)
print(f"\nTheme Intensity Metrics:\nMean Top 3 Scores: {mean_top3}\nMax Score: {max_score}\nCount Above 0.40: {count_above_threshold}")

