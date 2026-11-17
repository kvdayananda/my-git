"""Tests for Sentient NLP Engine."""
from app.core import compute_sentiment, classify_intent
from app.main import SentientAnalyzer


def test_positive_sentiment():
    score, label = compute_sentiment("This tool is great, fast, and awesome!")
    assert score > 0.0
    assert label == "positive"


def test_negative_sentiment():
    score, label = compute_sentiment("Encountered a bad bug and a terrible crash.")
    assert score < 0.0
    assert label == "negative"


def test_neutral_sentiment():
    score, label = compute_sentiment("The application received a data package.")
    assert score == 0.0
    assert label == "neutral"


def test_intent_classification():
    assert classify_intent("How do I configure the server?") == "inquiry"
    assert classify_intent("Critical error on startup!") == "bug_report"
    assert classify_intent("Thanks for the great release!") == "praise"


def test_analyzer_facade():
    res = SentientAnalyzer.process("Great work on delivering the awesome release!")
    assert res["sentiment_label"] == "positive"
    assert "sentiment_score" in res
