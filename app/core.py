"""Sentient NLP Core Engine."""
import re
from typing import Dict, List, Tuple

POSITIVE_LEXICON = {"great", "excellent", "fast", "love", "awesome", "good", "reliable", "easy", "clean"}
NEGATIVE_LEXICON = {"bad", "slow", "error", "fail", "broken", "hate", "issue", "crash", "terrible", "bug"}


def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"\b[a-zA-Z]{2,}\b", text)]


def compute_sentiment(text: str) -> Tuple[float, str]:
    tokens = tokenize(text)
    if not tokens:
        return 0.0, "neutral"

    pos_count = sum(1 for t in tokens if t in POSITIVE_LEXICON)
    neg_count = sum(1 for t in tokens if t in NEGATIVE_LEXICON)
    total = pos_count + neg_count

    if total == 0:
        return 0.0, "neutral"

    score = round((pos_count - neg_count) / total, 3)
    if score > 0.15:
        label = "positive"
    elif score < -0.15:
        label = "negative"
    else:
        label = "neutral"

    return score, label


def classify_intent(text: str) -> str:
    tokens = set(tokenize(text))
    if {"bug", "crash", "error", "fail", "broken"} & tokens:
        return "bug_report"
    if {"how", "why", "help", "question", "docs"} & tokens:
        return "inquiry"
    if {"love", "great", "thanks", "awesome"} & tokens:
        return "praise"
    return "general_feedback"
