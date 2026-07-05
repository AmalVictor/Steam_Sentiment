"""
src/ingest.py — Steam API Ingestion Module
─────────────────────────────────────────────────────────────────────────────
PURPOSE:
    Responsible for ONE thing: fetching raw reviews from the Steam API.

    This module knows nothing about databases or sentiment analysis.
    It simply calls the API, handles errors and pagination, and returns
    a clean list of Python dictionaries.

THE STEAM REVIEWS API:
    Endpoint: https://store.steampowered.com/appreviews/{appid}?json=1
    No API key required. Public endpoint.
    Returns up to 100 reviews per page. Uses cursor-based pagination.

PAGINATION EXPLAINED:
    "Cursor" is a special token Steam gives you after each page.
    You pass it back on the next request to get the next page.

    Page 1: cursor="*"        → returns reviews 1-100 + new cursor "abc123"
    Page 2: cursor="abc123"   → returns reviews 101-200 + new cursor "def456"
    ...and so on until Steam returns fewer than 100 results (end of data)
─────────────────────────────────────────────────────────────────────────────
"""

import time
import logging
from datetime import datetime

import requests

from src.config import REQUEST_DELAY_SECONDS, MAX_RETRIES

logger = logging.getLogger(__name__)

# Steam API base URL — {appid} is replaced with the actual game ID
STEAM_REVIEWS_URL = "https://store.steampowered.com/appreviews/{appid}"


# ─────────────────────────────────────────────────────────────────────────────
# _make_request()   (private helper — the underscore means "internal use only")
# ─────────────────────────────────────────────────────────────────────────────
def _make_request(url: str, params: dict) -> dict:
    """
    Make a single GET request with automatic retry on failure.

    Implements EXPONENTIAL BACKOFF: if a request fails, we wait longer
    and longer before each retry (1s → 2s → 4s). This gives the server
    time to recover instead of hammering it with rapid retries.

    Args:
        url (str): The full URL to request.
        params (dict): Query parameters to append to the URL.

    Returns:
        dict: The parsed JSON response body.

    Raises:
        Exception: If all retry attempts fail.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(f"GET {url} | params={params} | attempt {attempt}/{MAX_RETRIES}")

            # timeout=15: abandon the request if no response in 15 seconds
            # Without a timeout, a hung request could freeze the entire pipeline
            response = requests.get(url, params=params, timeout=15)

            # raise_for_status() turns HTTP 4xx/5xx into Python exceptions
            # e.g., 404 → requests.exceptions.HTTPError: 404 Client Error
            response.raise_for_status()

            # Parse the JSON body into a Python dict and return it
            return response.json()

        except Exception as e:
            last_error = e
            logger.warning(f"Request attempt {attempt} failed: {e}")

            if attempt < MAX_RETRIES:
                # Exponential backoff: 2^0=1s, 2^1=2s, 2^2=4s
                wait_time = 2 ** (attempt - 1)
                logger.info(f"Retrying in {wait_time} second(s)...")
                time.sleep(wait_time)

    # All retries exhausted
    logger.error(f"All {MAX_RETRIES} request attempts failed for {url}")
    raise Exception(f"Request failed after {MAX_RETRIES} attempts: {last_error}")


# ─────────────────────────────────────────────────────────────────────────────
# _parse_review()   (private helper)
# ─────────────────────────────────────────────────────────────────────────────
def _parse_review(raw_review: dict, appid: int) -> dict:
    """
    Extract the fields we care about from a single raw Steam API review dict.

    Steam returns many fields we don't need (steam_purchase, votes_funny, etc.).
    This function extracts only what our database schema expects.

    Args:
        raw_review (dict): One review object from Steam's API response.
        appid (int): The game's appid (not in the review object itself).

    Returns:
        dict: A clean dictionary with exactly the fields we store.
    """
    # Steam returns Unix timestamps (seconds since Jan 1, 1970).
    # We convert to a Python datetime object, which psycopg2 then stores
    # as a proper PostgreSQL TIMESTAMP.
    ts = raw_review.get("timestamp_created")
    timestamp = datetime.fromtimestamp(ts) if ts else None

    return {
        # Steam calls this "recommendationid" — we rename it to review_id for clarity
        "review_id": int(raw_review["recommendationid"]),
        "appid": appid,

        # The actual review text written by the player
        "review_text": raw_review.get("review", ""),

        # Language the review was written in (we filter to "english" upstream)
        "language": raw_review.get("language", ""),

        # True = thumbs up, False = thumbs down (Steam's own signal)
        "voted_up": raw_review.get("voted_up", None),

        # Minutes played at the time the review was written
        # Nested inside the "author" sub-object in the API response
        "playtime_at_review_minutes": raw_review.get("author", {}).get(
            "playtime_at_review", None
        ),

        # How many users marked this review as helpful
        "votes_up": raw_review.get("votes_up", 0),

        # When the review was posted on Steam (converted from Unix timestamp)
        "timestamp_created": timestamp,

        # These two fields will be filled in by sentiment.py (not the API)
        "sentiment_compound": None,
        "sentiment_label": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# fetch_reviews()   (public function — called by pipeline.py)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_reviews(appid: int, num_reviews: int = 100, language: str = "english") -> list:
    """
    Fetch up to `num_reviews` recent reviews for a Steam game.

    Handles pagination automatically using Steam's cursor mechanism.
    Adds a 1-second delay between page requests to avoid rate limiting.
    Catches and logs per-request failures without crashing the whole run.

    Args:
        appid (int): Steam application ID (e.g., 1245620 for Elden Ring).
        num_reviews (int): Maximum number of reviews to fetch total.
                           Defaults to 100 (one page).
        language (str): Language filter. Defaults to "english".
                        VADER only works well on English text.

    Returns:
        list[dict]: A list of parsed review dictionaries.
                    Empty list if the API is unreachable after all retries.

    Example:
        reviews = fetch_reviews(appid=1245620, num_reviews=200)
        # Returns up to 200 reviews for Elden Ring, spread across 2 API pages
    """
    url = STEAM_REVIEWS_URL.format(appid=appid)
    all_reviews = []

    # Cursor starts as "*" which means "from the beginning"
    # After each page, Steam returns a new cursor for the next page
    cursor = "*"

    # Steam allows max 100 reviews per page
    per_page = min(100, num_reviews)

    logger.info(f"Fetching up to {num_reviews} reviews for appid={appid} (language={language})")

    while len(all_reviews) < num_reviews:
        # Build the query parameters for this page request
        params = {
            "json": 1,              # return JSON (not HTML)
            "filter": "recent",     # sort by most recent reviews
            "language": language,   # only fetch this language
            "num_per_page": per_page,
            "cursor": cursor,       # which page to fetch
            "purchase_type": "all", # include non-purchase reviews too
        }

        try:
            data = _make_request(url, params)
        except Exception as e:
            # If we can't fetch this page even after retries, log and stop
            # We return whatever we've collected so far rather than crashing
            logger.error(f"Stopping pagination for appid={appid} due to error: {e}")
            break

        # Extract the list of reviews from the response
        page_reviews = data.get("reviews", [])

        # If Steam returned 0 reviews, we've reached the end — stop paginating
        if not page_reviews:
            logger.debug(f"No more reviews available for appid={appid}. Stopping.")
            break

        # Parse each raw review dict into our clean format
        for raw_review in page_reviews:
            try:
                parsed = _parse_review(raw_review, appid)
                all_reviews.append(parsed)
            except Exception as e:
                # If one review is malformed, skip it and continue
                review_id = raw_review.get("recommendationid", "unknown")
                logger.warning(f"Failed to parse review {review_id}: {e}. Skipping.")

        logger.debug(
            f"Page fetched: {len(page_reviews)} reviews | "
            f"Total so far: {len(all_reviews)}"
        )

        # If this page returned fewer results than requested, we're at the end
        if len(page_reviews) < per_page:
            logger.debug(f"Last page reached for appid={appid}.")
            break

        # Get the cursor for the next page
        cursor = data.get("cursor", "")
        if not cursor:
            logger.debug("No cursor returned — end of results.")
            break

        # Wait between requests — be a good citizen of the API
        # Without this, rapid requests could get our IP temporarily blocked
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f"Fetched {len(all_reviews)} reviews for appid={appid}")
    return all_reviews
