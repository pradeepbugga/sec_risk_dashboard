from openai import OpenAI
import numpy as np
import json, os

# ---------- CONFIG ----------
INPUT_PATH = "./data/paragraph_chunks_postprocessed/NVDA/risk_factors/2025.json"
OUTPUT_PATH = "./data/embedded_with_heading/NVDA/risk_factors/te3/2025.json"
MODEL_NAME = "text-embedding-3-large"
BATCH_SIZE = 100

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

client = OpenAI()

# ---------- EMBEDDING FUNCTION ----------
def embed_texts(texts, model=MODEL_NAME, batch_size=BATCH_SIZE):
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]

        response = client.embeddings.create(
            model=model,
            input=batch
        )

        batch_embeddings = [d.embedding for d in response.data]
        all_embeddings.extend(batch_embeddings)

    return np.array(all_embeddings)

# ---------- LOAD CHUNKS ----------
with open(INPUT_PATH, "r") as f:
    chunks = json.load(f)

filtered_chunks = []

for chunk in chunks:
    if "non-GAAP" in " ".join(chunk["path"]):
        continue
    filtered_chunks.append(chunk)

# ---------- PREPARE TEXTS ----------
texts = [
    c["heading"] + " " + c["text"]
    for c in filtered_chunks
]

# ---------- CREATE EMBEDDINGS ----------
embeddings = embed_texts(texts)

# ---------- ATTACH EMBEDDINGS ----------
for i, emb in enumerate(embeddings):
    filtered_chunks[i]["embedding"] = emb.tolist()

# ---------- SAVE ----------
with open(OUTPUT_PATH, "w") as f:
    json.dump(filtered_chunks, f)

print(f"✅ Saved {len(filtered_chunks)} embedded chunks to {OUTPUT_PATH}")
print(len(embeddings), "embeddings created.")
print(len(embeddings[0]), "dimensions each.")
print("Embedding complete.")