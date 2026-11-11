"""Sentient NLP Main Application."""
from app.core import classify_intent, compute_sentiment


class SentientAnalyzer:
    @staticmethod
    def process(text: str) -> dict:
        score, label = compute_sentiment(text)
        intent = classify_intent(text)
        return {
            "text": text,
            "sentiment_score": score,
            "sentiment_label": label,
            "predicted_intent": intent,
        }
