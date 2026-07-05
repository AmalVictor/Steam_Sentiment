"""
src/pipeline.py — Main Orchestration Script
─────────────────────────────────────────────────────────────────────────────
PURPOSE:
    This is the ENTRY POINT for the entire pipeline. It ties all modules
    together and runs the full ETL process for all 6 games.

    Think of it as the "conductor" of an orchestra — it doesn't play any
    instrument itself, but it coordinates all the players (ingest, sentiment,
    db) in the right order.

HOW TO RUN:
    python -m src.pipeline

    The "-m" flag tells Python to run a module (from a package).
    This ensures imports like "from src.config import ..." work correctly.

WHAT THIS SCRIPT DOES (in order):
    1. Set up logging (console + file)
    2. Initialize the database (create tables if they don't exist)
    3. Insert/confirm the 6 game records
    4. For each game:
       a. Fetch reviews from Steam API       (ingest.py)
       b. Score reviews with VADER           (sentiment.py)
       c. Insert new reviews into PostgreSQL (db.py)
       d. Log counts (fetched, inserted, skipped)
    5. Print a final summary of total reviews processed

FAULT TOLERANCE:
    Each game's processing is wrapped in try/except. If Dota 2's API call
    fails, we log the error and continue to the next game. One bad game
    does not crash the whole run.
─────────────────────────────────────────────────────────────────────────────
"""

import logging
import sys
import time
from pathlib import Path

# ── Configure Logging ─────────────────────────────────────────────────────────
# We set up logging BEFORE importing other src modules so that any errors
# during import are also captured by the log file.
#
# WHY CONFIGURE LOGGING HERE and not in each module?
#   Each module creates its OWN logger with logging.getLogger(__name__),
#   but the ROOT logger's configuration (level, format, handlers) is set here.
#   All module loggers inherit this configuration automatically.

# Ensure the logs/ directory exists (create it if not)
# Path(__file__).parent.parent = project root directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)  # exist_ok=True: don't error if dir already exists

logging.basicConfig(
    level=logging.INFO,     # Show INFO and above (DEBUG messages are hidden)
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    # %(asctime)s   = timestamp  e.g., 2024-06-30 09:00:01,123
    # %(levelname)s = INFO, WARNING, ERROR, etc.
    # %(name)s      = module name e.g., src.ingest, src.db
    handlers=[
        # Handler 1: Write log to a file (persists between runs)
        logging.FileHandler(LOGS_DIR / "pipeline.log", encoding="utf-8"),
        # Handler 2: Also print to the console (so you can watch in real-time)
        logging.StreamHandler(sys.stdout),
    ]
)

# Get a logger specifically for this module (shows as "src.pipeline" in logs)
logger = logging.getLogger(__name__)

# ── Import project modules (after logging is configured) ──────────────────────
from src.config import GAMES, REVIEWS_PER_GAME, REVIEW_LANGUAGE
from src.db import init_db, insert_games, upsert_reviews
from src.ingest import fetch_reviews
from src.sentiment import score_reviews


# ─────────────────────────────────────────────────────────────────────────────
# run_pipeline()
# ─────────────────────────────────────────────────────────────────────────────
def run_pipeline():
    """
    Execute the full Steam Sentiment ETL pipeline.

    Steps:
        1. Initialize database (create tables if needed)
        2. Insert game metadata records
        3. For each game: fetch → score → upsert
        4. Log and return final summary statistics

    Returns:
        dict: Summary with keys "total_fetched", "total_inserted", "games_processed",
              "games_failed". Useful for testing or future monitoring.
    """
    pipeline_start_time = time.time()

    logger.info("=" * 70)
    logger.info("STEAM SENTIMENT PIPELINE — RUN STARTED")
    logger.info("=" * 70)

    # ── Step 1: Initialize Database ───────────────────────────────────────────
    # Runs schema.sql to create tables if they don't exist yet.
    # Safe to call on every run — uses CREATE TABLE IF NOT EXISTS.
    logger.info("Step 1/3: Initializing database schema...")
    try:
        init_db()
    except Exception as e:
        # If we can't even create the tables, there's no point continuing.
        # This is a CRITICAL failure — exit with a non-zero code.
        logger.critical(f"Database initialization failed: {e}")
        logger.critical("Cannot proceed without database. Exiting.")
        sys.exit(1)

    # ── Step 2: Insert Game Records ───────────────────────────────────────────
    # Convert the GAMES list of tuples into a list of dicts for insert_games()
    logger.info("Step 2/3: Inserting game metadata...")
    game_records = [
        {"appid": appid, "game_name": game_name, "genre": genre}
        for appid, game_name, genre in GAMES
    ]
    try:
        insert_games(game_records)
    except Exception as e:
        logger.critical(f"Failed to insert game records: {e}")
        sys.exit(1)

    # ── Step 3: Process Each Game ─────────────────────────────────────────────
    logger.info("Step 3/3: Processing games...")
    logger.info(f"Games to process: {len(GAMES)}")
    logger.info(f"Reviews per game: {REVIEWS_PER_GAME}")
    logger.info("-" * 70)

    # Accumulators for the final summary
    total_fetched = 0
    total_inserted = 0
    games_processed = 0
    games_failed = 0

    for appid, game_name, genre in GAMES:
        game_start_time = time.time()
        logger.info(f"▶  Processing: {game_name} (appid={appid}, genre={genre})")

        try:
            # ── EXTRACT: Fetch reviews from Steam API ─────────────────────────
            reviews = fetch_reviews(
                appid=appid,
                num_reviews=REVIEWS_PER_GAME,
                language=REVIEW_LANGUAGE
            )
            fetched_count = len(reviews)
            total_fetched += fetched_count
            logger.info(f"   ✓ Fetched {fetched_count} reviews")

            if fetched_count == 0:
                logger.warning(f"   ⚠ No reviews returned for {game_name}. Skipping.")
                games_processed += 1
                continue

            # ── TRANSFORM: Score sentiment with VADER ─────────────────────────
            reviews = score_reviews(reviews)
            logger.info(f"   ✓ Sentiment scored for {fetched_count} reviews")

            # ── LOAD: Insert into PostgreSQL ──────────────────────────────────
            inserted_count = upsert_reviews(reviews)
            skipped_count = fetched_count - inserted_count
            total_inserted += inserted_count

            game_elapsed = time.time() - game_start_time
            logger.info(
                f"   ✓ Inserted: {inserted_count} new | "
                f"Skipped (duplicates): {skipped_count} | "
                f"Time: {game_elapsed:.1f}s"
            )
            games_processed += 1

        except Exception as e:
            # ── PER-GAME ERROR HANDLING ───────────────────────────────────────
            # If processing THIS game fails for any reason, log it and continue
            # to the next game. One failure does not abort the whole pipeline.
            logger.error(f"   ✗ FAILED to process {game_name}: {e}", exc_info=True)
            # exc_info=True includes the full Python traceback in the log file
            games_failed += 1

        logger.info("")  # blank line between games for readability

    # ── Final Summary ─────────────────────────────────────────────────────────
    total_elapsed = time.time() - pipeline_start_time

    logger.info("=" * 70)
    logger.info("PIPELINE COMPLETE — SUMMARY")
    logger.info("=" * 70)
    logger.info(f"  Games processed successfully : {games_processed}")
    logger.info(f"  Games failed                 : {games_failed}")
    logger.info(f"  Total reviews fetched        : {total_fetched}")
    logger.info(f"  Total NEW reviews inserted   : {total_inserted}")
    logger.info(f"  Total pipeline run time      : {total_elapsed:.1f} seconds")
    logger.info("=" * 70)

    # Also print to console in a clean format (in addition to the logger output)
    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETE")
    print(f"   Games OK: {games_processed}  |  Games failed: {games_failed}")
    print(f"   Reviews fetched: {total_fetched}  |  New rows inserted: {total_inserted}")
    print(f"   Duration: {total_elapsed:.1f}s")
    print("=" * 70)

    return {
        "total_fetched": total_fetched,
        "total_inserted": total_inserted,
        "games_processed": games_processed,
        "games_failed": games_failed,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
# This block only runs when the script is executed directly:
#   python -m src.pipeline
#
# It does NOT run if this module is imported by another script.
# That's the standard Python pattern for scripts that can also be imported.
if __name__ == "__main__":
    run_pipeline()
