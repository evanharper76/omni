# semantic_recall.py
import json
import os
import numpy as np

def cosine_sim(v1, v2):
    a = np.array(v1)
    b = np.array(v2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def load_messages(path):
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def recall_similar(path, input_embedding, top_n=5):
    messages = load_messages(path)
    scored = []
    for msg in messages:
        sim = cosine_sim(input_embedding, msg.get("embedding", []))
        scored.append((sim, msg))
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[:top_n]
