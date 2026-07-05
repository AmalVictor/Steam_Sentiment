-- ─────────────────────────────────────────────────────────────────────────────
-- src/schema.sql — Database Schema Definition
-- ─────────────────────────────────────────────────────────────────────────────
-- PURPOSE:
--   This file creates the two PostgreSQL tables our pipeline uses.
--   It is run once (on first pipeline run) via init_db() in db.py.
--   Re-running it is safe because of "IF NOT EXISTS".
--
-- HOW TO RUN MANUALLY (if you want to inspect or reset):
--   Open pgAdmin → Query Tool → paste and run this file
--   OR from command line:
--   psql -U postgres -d steam_reviews -f src/schema.sql
--
-- DESIGN DECISIONS (explained in the learning path, Module 6):
--   - Two tables instead of one to avoid repeating game_name/genre per review
--   - review_id is Steam's own recommendationid — globally unique
--   - ON CONFLICT DO NOTHING relies on review_id being the PRIMARY KEY
-- ─────────────────────────────────────────────────────────────────────────────


-- ── TABLE: games ──────────────────────────────────────────────────────────────
-- Stores the 6 games we track. This is a "dimension table" in BI terminology
-- — it describes WHO the reviews are about.
--
-- Only 6 rows total. Small, but critical — it gives us game_name and genre
-- for every review without storing those strings millions of times.

CREATE TABLE IF NOT EXISTS games (
    -- appid: Steam's unique identifier for each game (e.g., 1245620 = Elden Ring)
    -- PRIMARY KEY means: must be unique, can never be NULL
    appid       INTEGER     PRIMARY KEY,

    -- game_name: Human-readable game title shown in dashboards
    -- VARCHAR(100): text up to 100 characters (enough for any game name)
    -- NOT NULL: every game MUST have a name
    game_name   VARCHAR(100) NOT NULL,

    -- genre: Broad category for cross-genre comparisons in Power BI
    -- Nullable — genre is optional (though we always supply it)
    genre       VARCHAR(50)
);


-- ── TABLE: reviews ────────────────────────────────────────────────────────────
-- Stores individual Steam reviews with their sentiment scores.
-- This is the "fact table" — it stores the measurable events.
--
-- Grows with every pipeline run (hundreds of new rows per day).
-- All four Power BI charts query this table.

CREATE TABLE IF NOT EXISTS reviews (
    -- review_id: Steam's "recommendationid" — a globally unique integer per review
    -- BIGINT because Steam has issued hundreds of millions of IDs
    -- (regular INTEGER maxes out at ~2 billion — BIGINT at ~9.2 quintillion)
    review_id               BIGINT      PRIMARY KEY,

    -- appid: Which game this review is for
    -- REFERENCES games(appid): a FOREIGN KEY constraint — PostgreSQL enforces
    -- that you can't insert a review for a game not in the games table
    appid                   INTEGER     REFERENCES games(appid),

    -- review_text: The raw text the player wrote
    -- TEXT: unlimited length (reviews can be very long)
    review_text             TEXT,

    -- language: The language the review was written in (we filter to "english")
    language                VARCHAR(20),

    -- voted_up: Steam's own thumbs-up (TRUE) or thumbs-down (FALSE) signal
    -- We compare this against VADER's label in Power BI
    voted_up                BOOLEAN,

    -- playtime_at_review_minutes: Minutes the reviewer had played at time of writing
    -- We scatter-plot this against sentiment to find correlations
    playtime_at_review_minutes  INTEGER,

    -- votes_up: How many other Steam users found this review helpful
    votes_up                INTEGER,

    -- timestamp_created: When the review was posted on Steam
    -- Stored as PostgreSQL TIMESTAMP so we can query by date ranges
    timestamp_created       TIMESTAMP,

    -- sentiment_compound: VADER's compound score, range -1.0 to +1.0
    -- FLOAT: decimal number (e.g., 0.7234, -0.4521)
    sentiment_compound      FLOAT,

    -- sentiment_label: Human-readable sentiment category derived from compound
    -- Values: "positive", "neutral", "negative"
    sentiment_label         VARCHAR(10),

    -- ingested_at: When OUR pipeline inserted this row (not when review was written)
    -- DEFAULT NOW(): automatically set to current timestamp on insert
    -- Useful for debugging ("when did we process this?")
    ingested_at             TIMESTAMP   DEFAULT NOW()
);


-- ── INDEXES ───────────────────────────────────────────────────────────────────
-- Indexes speed up queries by letting PostgreSQL jump directly to matching rows
-- instead of scanning every row from top to bottom.
--
-- We create indexes on the columns Power BI and our pipeline filter by most often.

-- Index on appid: Power BI filters reviews by game constantly
-- Without this: 1M reviews → full table scan every time you switch games in BI
CREATE INDEX IF NOT EXISTS idx_reviews_appid
    ON reviews(appid);

-- Index on timestamp_created: Power BI trends charts filter by date
-- Also useful for incremental loads if we add watermark-based filtering later
CREATE INDEX IF NOT EXISTS idx_reviews_timestamp
    ON reviews(timestamp_created);

-- Index on sentiment_label: useful for counts by label (Power BI chart 2)
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment_label
    ON reviews(sentiment_label);
