import json
import numpy as np

def inspect(path):
    with open(path) as f:
        data = json.load(f)

    lengths = [len(x["text"].split()) for x in data]
    print("Chunks:", len(data))
    print("Mean words:", np.mean(lengths))
    print("Median words:", np.median(lengths))
    print("Min words:", np.min(lengths))
    print("Max words:", np.max(lengths))
    print("Short (<40 words):", sum(l < 40 for l in lengths))

inspect("./data/paragraph_chunks_postprocessed/QCOM/risk_factors/2024.json")
inspect("./data/paragraph_chunks_postprocessed/QCOM/risk_factors/2025.json")