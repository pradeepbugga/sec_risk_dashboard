
from transformers import AutoTokenizer
import re, os
import json
from glob import glob

tokenizer = AutoTokenizer.from_pretrained(
    "sentence-transformers/all-mpnet-base-v2"
)

tokenizer.model_max_length = 100000
def count_tokens(t):
    return len(tokenizer(t, add_special_tokens=False)["input_ids"])

def split_large_chunk(chunk, max_tokens=350, overlap_tokens=50):
    text = chunk["text"]
    sentences = re.split(r'(?<=[.!?])\s+', text)

    subchunks = []
    buffer = []
    buffer_tokens = 0
    sub_index = 0

    

    for sentence in sentences:
        sent_tokens = count_tokens(sentence)

        # Handle pathological long sentence
        if sent_tokens > max_tokens:
            words = sentence.split()
            temp = []
            temp_tokens = 0

            for word in words:
                w_tokens = count_tokens(word)
                if temp_tokens + w_tokens > max_tokens:
                    subchunks.append({
                        **chunk,
                        "text": " ".join(temp),
                        "sub_index": sub_index
                    })
                    sub_index += 1
                    temp = [word]
                    temp_tokens = w_tokens
                else:
                    temp.append(word)
                    temp_tokens += w_tokens

            if temp:
                subchunks.append({
                    **chunk,
                    "text": " ".join(temp),
                    "sub_index": sub_index
                })
                sub_index += 1

            continue

        # Normal sentence packing
        if buffer_tokens + sent_tokens > max_tokens:
            subchunks.append({
                **chunk,
                "text": " ".join(buffer),
                "sub_index": sub_index
            })
            sub_index += 1

            # Overlap logic
            overlap = []
            overlap_token_count = 0
            for s in reversed(buffer):
                s_tokens = count_tokens(s)
                if overlap_token_count + s_tokens > overlap_tokens:
                    break
                overlap.insert(0, s)
                overlap_token_count += s_tokens

            buffer = overlap
            buffer_tokens = overlap_token_count

        buffer.append(sentence)
        buffer_tokens += sent_tokens

    if buffer:
        subchunks.append({
            **chunk,
            "text": " ".join(buffer),
            "sub_index": sub_index
        })
        

    return subchunks


if __name__ == "__main__":
    
    for json_path in glob("./data/paragraph_chunks/AVGO/risk_factors/*.json"):
        with open(json_path, "r") as f:
            paragraph_chunks = json.load(f)
        
                

        final_chunks = []

        for chunk in paragraph_chunks:
            tokens = count_tokens(chunk["text"])

            if tokens > 400:
                final_chunks.extend(split_large_chunk(chunk))
            else:
                final_chunks.append(chunk)

        output_path = json_path.replace(
            "paragraph_chunks", "paragraph_chunks_postprocessed"
        )   
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(final_chunks, f, indent=2)
        