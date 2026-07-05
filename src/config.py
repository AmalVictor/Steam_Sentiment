"""
src/config.py — Central Configuration Module
─────────────────────────────────────────────────────────────────────────────
PURPOSE:
    This is the single source of truth for ALL configuration in the project.
    Every other module imports from here. If you need to change a setting,
    you change it here (or in your .env file) — nowhere else.

WHY A SEPARATE CONFIG FILE?
    Imagine your database password is hardcoded in db.py, ingest.py, AND
    pipeline.py. When the password changes, you'd need to find and update
    all three files. With config.py, you update .env once — done.

HOW ENVIRONMENT VARIABLES WORK:
    1. You fill in your real values in the `.env` file
    2. `load_dotenv()` reads that file and loads values into os.environ
    3. `os.getenv("KEY")` retrieves the value by name
    4. The `.env` file is NEVER committed to Git (see .gitignore)
─────────────────────────────────────────────────────────────────────────────
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env file ────────────────────────────────────────────────────────────
# Path(__file__).parent = the folder containing THIS file (src/)
# .parent again = the project root (steam-sentiment-pipeline/)
# This makes the script work regardless of which directory you run it from.
PROJECT_ROOT = Path(__file__).parent.parent

# load_dotenv() searches for a .env file and loads its key=value pairs
# into environment variables. If .env doesn't exist, it silently continues
# (variables may then be missing, which will cause an error later — good).
load_dotenv(PROJECT_ROOT / ".env")


# ── Database Configuration ────────────────────────────────────────────────────
# os.getenv(KEY, DEFAULT) — reads the environment variable KEY.
# The second argument is a fallback default value (used if .env is missing it).

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))    # convert string → int
DB_NAME = os.getenv("POSTGRES_DB", "steam_reviews")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")          # no default — MUST be set


# ── File Paths ────────────────────────────────────────────────────────────────
# Path to schema.sql (used by init_db() in db.py to create the tables)
SCHEMA_PATH = PROJECT_ROOT / "src" / "schema.sql"

# Path to the logs directory
LOGS_DIR = PROJECT_ROOT / "logs"


# ── Games to Track ────────────────────────────────────────────────────────────
# A list of tuples: (steam_appid, display_name, genre)
# These are the 6 games our pipeline collects reviews for.
#
# WHY HARDCODED HERE and not in .env?
#   The game list is a business decision (which games to analyze), not a secret.
#   It belongs in code, not in a secrets file. Analysts can see and change it.
#
# ADD A NEW GAME: just add a new tuple. The pipeline handles the rest.

GAMES = [
    (730,     "Counter-Strike 2",     "shooter"),
    (570,     "Dota 2",               "MOBA"),
    (578080,  "PUBG: Battlegrounds",  "battle royale"),
    (271590,  "Grand Theft Auto V",   "open world"),
    (1245620, "Elden Ring",           "RPG"),
    (413150,  "Stardew Valley",       "indie/casual"),
]


# ── Ingestion Settings ────────────────────────────────────────────────────────
# How many reviews to fetch per game per pipeline run.
# 100 is a safe default — the Steam API's max per page.
# Increase to 500 or 1000 for a richer dataset (more API calls, more time).
REVIEWS_PER_GAME = 100

# Only fetch English reviews (VADER is trained on English text only)
REVIEW_LANGUAGE = "english"

# How long to wait between API page requests (seconds)
# Steam doesn't publish a rate limit, but 1 second is respectful and safe.
REQUEST_DELAY_SECONDS = 1

# How many times to retry a failed API request before giving up
MAX_RETRIES = 3
