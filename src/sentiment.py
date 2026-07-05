"""
src/sentiment.py — Sentiment Scoring Module
─────────────────────────────────────────────────────────────────────────────
PURPOSE:
    This is the TRANSFORM stage of our ETL pipeline.

    Takes raw review dictionaries (from ingest.py) and enriches them with
    two new fields:
        - sentiment_compound: a float from -1.0 to +1.0
        - sentiment_label:    "positive", "neutral", or "negative"

WHY VADER?
    VADER (Valence Aware Dictionary and sEntiment Reasoner) is:
    - Fast: scores thousands of texts per second (no GPU needed)
    - Tuned for informal text: slang, capitalization, punctuation, emoji
    - No training data needed: uses a hand-built lexicon
    - Free and offline: no API calls, no costs

    It's the right tool for Steam reviews — short, informal, slang-heavy text.

VADER COMPOUND SCORE THRESHOLDS (industry standard):
    compound >= 0.05  → "positive"
    compound <= -0.05 → "negative"
    otherwise         → "neutral"
─────────────────────────────────────────────────────────────────────────────
"""

import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

# ── Initialize VADER ──────────────────────────────────────────────────────────
# SentimentIntensityAnalyzer loads the VADER lexicon from disk into memory.
# We create ONE instance here at module level (not inside the function) because:
#   - Loading the lexicon takes a small amount of time
#   - Creating a new instance for every review would be wasteful
#   - Module-level initialization happens only once when the module is imported
analyzer = SentimentIntensityAnalyzer()


# ─────────────────────────────────────────────────────────────────────────────
# _get_label()   (private helper)
# ─────────────────────────────────────────────────────────────────────────────
def _get_label(compound: float) -> str:
    """
    Convert a VADER compound score to a human-readable sentiment label.

    These thresholds (0.05 and -0.05) are VADER's own recommended values.
    They create a small "neutral zone" around 0 to avoid mislabeling
    very mildly positive/negative text.

    Args:
        compound (float): VADER compound score in range [-1.0, 1.0].

    Returns:
        str: One of "positive", "neutral", or "negative".

    Examples:
        _get_label(0.72)  → "positive"
        _get_label(-0.91) → "negative"
        _get_label(0.02)  → "neutral"
        _get_label(0.05)  → "positive"   (boundary is inclusive)
        _get_label(-0.05) → "negative"   (boundary is inclusive)
    """
    if compound >= 0.05:
        return "positive"
    elif compound <= -0.05:
        return "negative"
    else:
        return "neutral"


# ─────────────────────────────────────────────────────────────────────────────
# score_reviews()   (public function — called by pipeline.py)
# ─────────────────────────────────────────────────────────────────────────────
def score_reviews(reviews: list) -> list:
    """
    Add VADER sentiment scores to a list of review dictionaries.

    This function MUTATES the input list in place (adds new keys to each dict)
    AND returns it, so both of these work:
        reviews = score_reviews(reviews)        # assign return value
        score_reviews(reviews)                  # or just call it (mutates in place)

    Skips reviews where review_text is empty or whitespace-only.
    For those, sentiment_compound stays None and sentiment_label stays None.

    Args:
        reviews (list[dict]): List of review dicts from ingest.py.
                              Must have a "review_text" key.

    Returns:
        list[dict]: Same list, with "sentiment_compound" and "sentiment_label"
                    added/filled in for each review that has text.

    Example:
        reviews = [
            {"review_id": 1, "review_text": "Amazing game!", ...},
            {"review_id": 2, "review_text": "Total garbage.", ...},
            {"review_id": 3, "review_text": "", ...},  # empty — will be skipped
        ]
        scored = score_reviews(reviews)
        # scored[0]["sentiment_compound"] = 0.60
        # scored[0]["sentiment_label"]    = "positive"
        # scored[1]["sentiment_compound"] = -0.68
        # scored[1]["sentiment_label"]    = "negative"
        # scored[2]["sentiment_compound"] = None   (skipped)
        # scored[2]["sentiment_label"]    = None   (skipped)
    """
    scored_count = 0
    skipped_count = 0

    for review in reviews:
        text = review.get("review_text", "")

        # Skip empty or whitespace-only review text
        # .strip() removes leading/trailing whitespace — "   " becomes ""
        if not text or not text.strip():
            skipped_count += 1
            # Leave sentiment_compound and sentiment_label as None (already set in ingest.py)
            logger.debug(f"Skipping empty review text for review_id={review.get('review_id')}")
            continue

        # polarity_scores() returns a dict: {"pos": float, "neu": float, "neg": float, "compound": float}
        # We only need the "compound" key for our analysis
        scores = analyzer.polarity_scores(text)
        compound = scores["compound"]

        # Add the two new fields to the review dict
        review["sentiment_compound"] = compound
        review["sentiment_label"] = _get_label(compound)

        scored_count += 1

    logger.info(
        f"Sentiment scoring complete: {scored_count} scored, {skipped_count} skipped (empty text)."
    )
    return reviews
