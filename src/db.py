"""
src/db.py — Database Layer
─────────────────────────────────────────────────────────────────────────────
PURPOSE:
    All PostgreSQL operations live here. No other module directly touches
    the database — they all call functions from this file.

    This is called the "Repository Pattern" or "Data Access Layer" in
    software engineering — isolating database logic in one place.

FUNCTIONS:
    get_connection()     → Create and return a PostgreSQL connection
    init_db()            → Run schema.sql to create tables (safe to re-run)
    insert_games(games)  → Insert game records (skips existing ones)
    upsert_reviews(reviews) → Insert reviews (skips duplicates by review_id)

WHY ISOLATE DATABASE CODE HERE?
    If you ever switch from PostgreSQL to MySQL or SQLite, you only change
    this one file. The rest of the pipeline code stays untouched.
─────────────────────────────────────────────────────────────────────────────
"""

import logging
import psycopg2
import psycopg2.extras  # provides execute_values() for bulk inserts

# Import all config values from our central config file
from src.config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, SCHEMA_PATH
)

# Get a logger for this module
# __name__ resolves to "src.db" — helps identify which module logged a message
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# get_connection()
# ─────────────────────────────────────────────────────────────────────────────
def get_connection():
    """
    Create and return a new psycopg2 connection to PostgreSQL.

    A "connection" is like opening a phone call to the database server.
    You need one before you can send any SQL commands.

    Returns:
        psycopg2.connection: An open database connection object.

    Raises:
        psycopg2.OperationalError: If the database is unreachable or
        credentials are wrong. Let this propagate — the caller (pipeline.py)
        will catch and log it.

    Usage:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
    """
    logger.debug(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}")

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# init_db()
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    """
    Initialize the database by running schema.sql.

    This creates the `games` and `reviews` tables (and their indexes) if they
    don't already exist. The SQL uses "CREATE TABLE IF NOT EXISTS" so calling
    this multiple times is completely safe — it never drops or modifies
    existing data.

    Called once at the start of each pipeline run in pipeline.py.

    Raises:
        FileNotFoundError: If schema.sql cannot be found.
        psycopg2.Error: If the SQL fails to execute.
    """
    logger.info("Initializing database schema...")

    # Read the SQL from the .sql file — cleaner than writing SQL as Python strings
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    # Use a context manager (with statement) for the connection.
    # This ensures the connection is closed even if an error occurs.
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Execute the entire schema.sql as a single command
        cursor.execute(schema_sql)

        # IMPORTANT: Changes to the database are only saved when you COMMIT.
        # psycopg2 does NOT auto-commit by default.
        conn.commit()

        logger.info("Database schema initialized successfully.")
    except Exception as e:
        # If something went wrong, ROLLBACK cancels any partial changes
        conn.rollback()
        logger.error(f"Failed to initialize database schema: {e}")
        raise  # re-raise so pipeline.py knows something went wrong
    finally:
        # Always close the connection, whether success or failure
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# insert_games()
# ─────────────────────────────────────────────────────────────────────────────
def insert_games(games: list):
    """
    Insert game records into the `games` table.

    Uses ON CONFLICT (appid) DO NOTHING so re-running never creates
    duplicate game rows. The `games` table has only 6 rows and almost
    never changes, but we still insert idempotently for consistency.

    Args:
        games (list): A list of dicts, each with keys:
                      "appid" (int), "game_name" (str), "genre" (str)

    Example input:
        [
            {"appid": 730, "game_name": "Counter-Strike 2", "genre": "shooter"},
            {"appid": 1245620, "game_name": "Elden Ring", "genre": "RPG"},
        ]
    """
    if not games:
        logger.warning("insert_games() called with an empty list. Nothing to insert.")
        return

    # Build a list of tuples — psycopg2's execute_values() expects tuples
    # [(730, "Counter-Strike 2", "shooter"), (1245620, "Elden Ring", "RPG"), ...]
    records = [
        (g["appid"], g["game_name"], g["genre"])
        for g in games
    ]

    # SQL with ON CONFLICT DO NOTHING — if appid already exists, skip silently
    sql = """
        INSERT INTO games (appid, game_name, genre)
        VALUES %s
        ON CONFLICT (appid) DO NOTHING;
    """

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # execute_values() is the efficient way to insert many rows at once.
        # It builds a single SQL statement: INSERT ... VALUES (1,..), (2,..), ...
        # Much faster than calling cursor.execute() in a loop.
        psycopg2.extras.execute_values(cursor, sql, records)

        conn.commit()
        logger.info(f"Inserted/confirmed {len(records)} game(s) in the games table.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to insert games: {e}")
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# upsert_reviews()
# ─────────────────────────────────────────────────────────────────────────────
def upsert_reviews(reviews: list) -> int:
    """
    Insert reviews into the `reviews` table, skipping duplicates.

    The key mechanism: ON CONFLICT (review_id) DO NOTHING
    If a review with the same review_id already exists in the table, the
    INSERT is silently skipped. No error, no duplicate, no data change.

    This is what makes the pipeline IDEMPOTENT:
    - Run it twice → same data in the database
    - Restart after a crash → safe, no duplicates

    Args:
        reviews (list): A list of dicts. Each dict should have these keys:
            - review_id (int)
            - appid (int)
            - review_text (str)
            - language (str)
            - voted_up (bool)
            - playtime_at_review_minutes (int)
            - votes_up (int)
            - timestamp_created (datetime or str)
            - sentiment_compound (float)
            - sentiment_label (str)

    Returns:
        int: Approximate number of newly inserted rows
             (PostgreSQL doesn't directly report skipped ON CONFLICT rows,
             so we return the rowcount which reflects actual inserts)
    """
    if not reviews:
        logger.warning("upsert_reviews() called with an empty list. Nothing to insert.")
        return 0

    # Build tuples matching the column order in the SQL below
    records = [
        (
            r["review_id"],
            r["appid"],
            r.get("review_text"),                    # .get() returns None if key missing
            r.get("language"),
            r.get("voted_up"),
            r.get("playtime_at_review_minutes"),
            r.get("votes_up"),
            r.get("timestamp_created"),
            r.get("sentiment_compound"),
            r.get("sentiment_label"),
        )
        for r in reviews
    ]

    sql = """
        INSERT INTO reviews (
            review_id,
            appid,
            review_text,
            language,
            voted_up,
            playtime_at_review_minutes,
            votes_up,
            timestamp_created,
            sentiment_compound,
            sentiment_label
        )
        VALUES %s
        ON CONFLICT (review_id) DO NOTHING;
    """

    conn = get_connection()
    try:
        cursor = conn.cursor()
        psycopg2.extras.execute_values(cursor, sql, records)
        conn.commit()

        # cursor.rowcount = number of rows actually inserted (excludes skipped ones)
        inserted = cursor.rowcount
        skipped = len(records) - inserted
        logger.debug(
            f"Upsert complete: {inserted} inserted, {skipped} skipped (already existed)."
        )
        return inserted
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to upsert reviews: {e}")
        raise
    finally:
        conn.close()
