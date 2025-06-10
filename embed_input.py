import os
import json
import time
import hashlib
import random
import re
from collections import defaultdict

# === Fake embedding (placeholder) ===
def fake_embed(text, dim=32):
    random.seed(hash(text))
    return [round(random.uniform(-1, 1), 4) for _ in range(dim)]

def compute_signal_score(text):
    return round(0.7 + 0.3 * random.random(), 3)

def generate_memory_node(user_id, username, room, content):
    text_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
    return {
        "id": f"msg_{text_hash}",
        "user_id": user_id,
        "username": username,
        "room": room,
        "timestamp": int(time.time()),
        "content": content,
        "embedding": fake_embed(content),
        "tags": ["chat"],
        "signal_score": compute_signal_score(content)
    }

def load_stopwords(filepath="stopwords.csv"):
    with open(filepath, "r", encoding="utf-8") as f:
        return set(word.strip().lower() for word in f if word.strip())

def extract_words(text):
    return re.findall(r'\b\w+\b', text.lower())

def build_user_word_profile(user_id, room="room_1"):
    folder = os.path.join("memory_logs", f"user_{user_id}")
    log_path = os.path.join(folder, f"{room}_log.jsonl")
    if not os.path.exists(log_path):
        return {}

    stopwords = load_stopwords()
    word_counts = defaultdict(int)
    total_words = 0

    # Count words excluding stopwords
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                words = extract_words(entry.get("content", ""))
                for w in words:
                    if w not in stopwords:
                        word_counts[w] += 1
                        total_words += 1
            except:
                continue

    if total_words == 0:
        return {
            "user_id": user_id,
            "total_words": 0,
            "word_freq": {}
        }

    # Normalize and sort
    word_freq = {
        word: round(count / total_words, 6)
        for word, count in word_counts.items()
    }
    sorted_freq = dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True))

    return {
        "user_id": user_id,
        "total_words": total_words,
        "word_freq": sorted_freq
    }
