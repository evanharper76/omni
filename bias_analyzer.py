import pandas as pd
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from empath import Empath
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

LOG_PATH = "memory_logs"
lexicon = Empath()
sentiment_analyzer = SentimentIntensityAnalyzer()

def collect_user_texts(user_id, room="room_1"):
    base_id = user_id.split("_")[0]
    path = os.path.join(LOG_PATH, f"user_{base_id}", f"{room}_log.jsonl")
    if not os.path.exists(path):
        return []

    messages = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                msg = json.loads(line.strip())
                if msg.get("user_id") == user_id:
                    messages.append(msg.get("content", ""))
            except json.JSONDecodeError:
                continue
    return messages

def analyze_user_bias(user_id, room="room_1"):
    texts = collect_user_texts(user_id, room)
    if not texts:
        return pd.DataFrame()

    results = [lexicon.analyze(text, normalize=True) for text in texts]
    df = pd.DataFrame(results)
    return df.mean().to_frame(name=user_id).T

def detect_bias_direction(user_id, category, room="room_1"):
    texts = collect_user_texts(user_id, room)
    if not texts:
        return None

    relevant_texts = [text for text in texts if category in lexicon.analyze(text, normalize=False)]
    if not relevant_texts:
        return None

    sentiment_scores = []
    for text in relevant_texts:
        score = sentiment_analyzer.polarity_scores(text)["compound"]
        sentiment_scores.append(score)

    if not sentiment_scores:
        return None

    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    return round(avg_sentiment, 4)

def sentiment_to_color(sentiment):
    sentiment = max(min(sentiment, 1), -1)
    red = (1 - sentiment) / 2
    green = (1 + sentiment) / 2
    return (red, green, 0.2)

def plot_radar_chart(user_id, room="room_1"):
    df = analyze_user_bias(user_id, room)
    if df.empty:
        print("No data to visualize.")
        return

    top_categories = df.loc[user_id].sort_values(ascending=False).head(10)
    categories = top_categories.index.tolist()
    values = top_categories.tolist()

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    sentiments = [detect_bias_direction(user_id, cat, room) or 0.0 for cat in categories]
    colors = [sentiment_to_color(s) for s in sentiments]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    for i in range(len(categories)):
        ax.plot([angles[i], angles[i + 1]], [values[i], values[i + 1]], color=colors[i], linewidth=3)
        ax.fill_between([angles[i], angles[i + 1]], 0, [values[i], values[i + 1]], color=colors[i], alpha=0.3)

    ax.plot([angles[-2], angles[0]], [values[-2], values[0]], color=colors[-1], linewidth=3)
    ax.fill_between([angles[-2], angles[0]], 0, [values[-2], values[0]], color=colors[-1], alpha=0.3)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_title(f"Top 10 Bias Traits (Color = Sentiment): {user_id}")
    plt.tight_layout()
    plt.show()

def plot_average_bias_chart(room="room_1"):
    all_user_ids = set()
    for root, dirs, files in os.walk(LOG_PATH):
        for file in files:
            if file == f"{room}_log.jsonl":
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            msg = json.loads(line.strip())
                            all_user_ids.add(msg.get("user_id"))
                        except:
                            continue

    all_profiles = []
    for uid in all_user_ids:
        df = analyze_user_bias(uid, room)
        if not df.empty:
            all_profiles.append(df)

    if not all_profiles:
        print("No user data found.")
        return

    avg_df = pd.concat(all_profiles).mean().to_frame(name="Average").T
    top_categories = avg_df.loc["Average"].sort_values(ascending=False).head(10)
    categories = top_categories.index.tolist()
    values = top_categories.tolist()

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    sentiments = [detect_bias_direction(uid, cat, room) or 0.0 for cat in categories for uid in all_user_ids]
    avg_sentiments = [np.mean([detect_bias_direction(uid, cat, room) or 0.0 for uid in all_user_ids]) for cat in categories]
    colors = [sentiment_to_color(s) for s in avg_sentiments]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    for i in range(len(categories)):
        ax.plot([angles[i], angles[i + 1]], [values[i], values[i + 1]], color=colors[i], linewidth=3)
        ax.fill_between([angles[i], angles[i + 1]], 0, [values[i], values[i + 1]], color=colors[i], alpha=0.3)

    ax.plot([angles[-2], angles[0]], [values[-2], values[0]], color=colors[-1], linewidth=3)
    ax.fill_between([angles[-2], angles[0]], 0, [values[-2], values[0]], color=colors[-1], alpha=0.3)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_title(f"Average Bias Traits (Color = Sentiment)")
    plt.tight_layout()
    plt.show()
