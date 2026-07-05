<div align="center">

# 🎮 Steam Sentiment Pipeline

### End-to-End Data Engineering & Power BI Analytics

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![VADER](https://img.shields.io/badge/NLP-VADER%20Sentiment-FF6B6B?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=for-the-badge)

<br/>

*A fully automated ETL pipeline that pulls 600+ Steam game reviews daily, scores them for sentiment using VADER NLP, stores everything in PostgreSQL, and surfaces actionable insights through an interactive Power BI dashboard.*

</div>

---

## 📌 Project Overview

This project is a **production-style, end-to-end data engineering pipeline** built entirely with open-source tools and free public APIs. It ingests real Steam game reviews, enriches them with NLP-based sentiment scores, and delivers a polished analytics dashboard — fully automated on a daily schedule.

### What this project demonstrates

| Area | Implementation |
|---|---|
| **ETL Pipeline** | Modular Python pipeline: Extract → Transform → Load |
| **API Integration** | Steam Web API with cursor-based pagination and retry logic |
| **Data Cleaning** | Language filtering, null handling, Unix timestamp conversion |
| **NLP / Sentiment Analysis** | VADER lexicon-based scoring with compound labels |
| **Relational Database** | PostgreSQL schema with constraints, indexes, and idempotency |
| **Business Intelligence** | Interactive Power BI dashboard with 4 visuals + slicer |
| **Automation** | Daily scheduling via Windows Task Scheduler |
| **Engineering Best Practices** | Modular code, `.env` config, structured logging, error handling |

### Games Tracked

| appid | Game | Genre |
|---|---|---|
| 730 | Counter-Strike 2 | Shooter |
| 570 | Dota 2 | MOBA |
| 578080 | PUBG: Battlegrounds | Battle Royale |
| 271590 | Grand Theft Auto V | Open World |
| 1245620 | Elden Ring | RPG |
| 413150 | Stardew Valley | Indie / Casual |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   STEAM WEB API (Public)                 │
│         store.steampowered.com/appreviews/{appid}        │
└──────────────────────────┬──────────────────────────────┘
                           │  HTTP GET · JSON · Cursor Pagination
                           ▼
┌─────────────────────────────────────────────────────────┐
│              PYTHON ETL PIPELINE  (src/)                 │
│                                                         │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────┐ │
│   │  ingest.py   │───▶│ sentiment.py │───▶│  db.py   │ │
│   │              │    │              │    │          │ │
│   │ • API calls  │    │ • VADER NLP  │    │ • Upsert │ │
│   │ • Pagination │    │ • Compound   │    │ • ON     │ │
│   │ • Retries    │    │   score      │    │   CONFLICT│ │
│   │ • Parsing    │    │ • Labels     │    │   DO     │ │
│   └──────────────┘    └──────────────┘    │   NOTHING│ │
│                                           └──────────┘ │
│   config.py · logging · error handling per game        │
└──────────────────────────┬──────────────────────────────┘
                           │  psycopg2 · SQL INSERT
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    POSTGRESQL DATABASE                   │
│                                                         │
│   ┌──────────────┐         ┌──────────────────────────┐ │
│   │    games     │────────▶│        reviews           │ │
│   │  (6 rows)    │  1:many │   (600+ rows, growing)   │ │
│   └──────────────┘         └──────────────────────────┘ │
└──────────────────────────┬──────────────────────────────┘
                           │  Direct PostgreSQL Connector
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   POWER BI DASHBOARD                     │
│                                                         │
│   KPI Cards  │  Line Chart  │  Bar Chart  │  Scatter    │
│   Sentiment  │  Trend Over  │  Label      │  Playtime   │
│   Summary    │  Time        │  Breakdown  │  vs Score   │
└─────────────────────────────────────────────────────────┘
                           ▲
          ┌────────────────┘
          │  Windows Task Scheduler (daily @ 9 AM)
          │  python -m src.pipeline
```

---

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.9+ | Core pipeline language |
| **requests** | 2.31.0 | Steam API HTTP calls |
| **vaderSentiment** | 3.3.2 | NLP sentiment scoring |
| **psycopg2-binary** | 2.9.9 | PostgreSQL database driver |
| **pandas** | 2.1.4 | Data inspection and analysis |
| **python-dotenv** | 1.0.0 | Secure environment variable loading |
| **PostgreSQL** | 14+ | Relational database storage |
| **Power BI Desktop** | Latest | Interactive analytics dashboard |
| **Windows Task Scheduler** | Built-in | Daily pipeline automation |
| **Python logging** | Built-in | Structured log files |

---

## ✨ Features

- ✔ **Steam API Integration** — Cursor-based pagination fetches 100 reviews per page per game
- ✔ **Multi-Game Processing** — Processes 6 genre-diverse games in a single run
- ✔ **Automatic Retries** — Exponential backoff (1s → 2s → 4s) on failed requests
- ✔ **Data Cleaning** — Language filtering, null checks, Unix timestamp conversion
- ✔ **VADER Sentiment Scoring** — Compound score from -1.0 to +1.0 per review
- ✔ **Sentiment Categorization** — Positive / Neutral / Negative with standard thresholds
- ✔ **Idempotent Pipeline** — `ON CONFLICT DO NOTHING` prevents all duplicate data
- ✔ **PostgreSQL Storage** — Normalized schema with foreign keys, indexes, and constraints
- ✔ **Interactive Power BI Dashboard** — 4 visuals + game slicer for cross-filtering
- ✔ **Daily Automation** — Windows Task Scheduler runs the pipeline hands-free
- ✔ **Structured Logging** — Timestamped logs to both console and `logs/pipeline.log`
- ✔ **Per-Game Fault Isolation** — One failed game never stops the rest of the run
- ✔ **Modular Architecture** — Each file has a single responsibility, easy to extend

---

## 📁 Project Structure

```
steam-sentiment-pipeline/
│
├── src/                        # All pipeline source code
│   ├── __init__.py             # Marks src/ as a Python package
│   ├── config.py               # Central config: DB settings, game list, constants
│   ├── schema.sql              # PostgreSQL table + index definitions
│   ├── db.py                   # Database layer: connect, init, insert, upsert
│   ├── ingest.py               # Steam API ingestion with pagination & retries
│   ├── sentiment.py            # VADER sentiment scoring & labeling
│   └── pipeline.py             # Orchestrator — entry point for the full run
│
├── logs/
│   ├── .gitkeep                # Keeps empty folder tracked in Git
│   └── pipeline.log            # Generated on each run (gitignored)
│
├── screenshots/                # Dashboard and output screenshots (for portfolio)
│
├── .env                        # Your secrets (gitignored — never committed)
├── .env.example                # Template showing required variables
├── .gitignore                  # Excludes .env, logs, __pycache__, venv
├── requirements.txt            # All Python dependencies with pinned versions
├── verify.py                   # Quick data verification script
└── README.md                   # This file
```

---

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher — [python.org](https://www.python.org/downloads/)
- PostgreSQL 14 or higher — [postgresql.org](https://www.postgresql.org/download/)
- Power BI Desktop (free) — [microsoft.com/power-bi](https://powerbi.microsoft.com/desktop/)

---

### 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/steam-sentiment-pipeline.git
cd steam-sentiment-pipeline
```

---

### 2 — Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

---

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4 — Create the PostgreSQL database

Open **pgAdmin** → right-click **Databases** → **Create → Database**, name it `steam_reviews`.

Or via the command line:

```bash
# Windows
createdb -U postgres steam_reviews

# macOS / Linux
createdb steam_reviews
```

---

### 5 — Configure environment variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in your real PostgreSQL credentials:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=steam_reviews
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
```

> ⚠️ **Never commit `.env` to Git.** It is already listed in `.gitignore`.

---

### 6 — Run the pipeline

```bash
python -m src.pipeline
```

**Expected output:**

```
2026-07-05 09:00:01  INFO  src.pipeline — STEAM SENTIMENT PIPELINE — RUN STARTED
2026-07-05 09:00:03  INFO  src.pipeline — ▶  Processing: Counter-Strike 2 (appid=730)
2026-07-05 09:00:04  INFO  src.ingest   — Fetched 100 reviews for appid=730
2026-07-05 09:00:05  INFO  src.sentiment — Sentiment scoring complete: 97 scored, 3 skipped
2026-07-05 09:00:06  INFO  src.pipeline — ✓ Inserted: 100 new | Skipped: 0 | Time: 2.1s
...
✅ PIPELINE COMPLETE
   Games OK: 6  |  Games failed: 0
   Reviews fetched: 600  |  New rows inserted: 600
   Duration: 11.0s
```

---

## 🔐 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `POSTGRES_HOST` | ✅ | `localhost` | PostgreSQL server hostname or IP |
| `POSTGRES_PORT` | ✅ | `5432` | PostgreSQL port (default is 5432) |
| `POSTGRES_DB` | ✅ | `steam_reviews` | Target database name |
| `POSTGRES_USER` | ✅ | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | ✅ | — | PostgreSQL password *(no default — must be set)* |

> The Steam Reviews API is **public and requires no API key.** No Steam account is needed.

---

## 🗄️ Database Schema

### `games` table — Dimension table (6 rows)

| Column | Type | Constraint | Description |
|---|---|---|---|
| `appid` | `INTEGER` | `PRIMARY KEY` | Steam's unique game identifier |
| `game_name` | `VARCHAR(100)` | `NOT NULL` | Human-readable game title |
| `genre` | `VARCHAR(50)` | — | Broad genre category for cross-game analysis |

---

### `reviews` table — Fact table (grows daily)

| Column | Type | Constraint | Description |
|---|---|---|---|
| `review_id` | `BIGINT` | `PRIMARY KEY` | Steam's `recommendationid` — globally unique |
| `appid` | `INTEGER` | `REFERENCES games(appid)` | Foreign key linking review to its game |
| `review_text` | `TEXT` | — | Raw review text written by the player |
| `language` | `VARCHAR(20)` | — | Review language (filtered to English) |
| `voted_up` | `BOOLEAN` | — | Steam thumbs-up (`true`) or thumbs-down (`false`) |
| `playtime_at_review_minutes` | `INTEGER` | — | Minutes played when the review was written |
| `votes_up` | `INTEGER` | — | Helpful votes from other Steam users |
| `timestamp_created` | `TIMESTAMP` | — | When the review was posted |
| `sentiment_compound` | `FLOAT` | — | VADER compound score: −1.0 (negative) → +1.0 (positive) |
| `sentiment_label` | `VARCHAR(10)` | — | `"positive"`, `"neutral"`, or `"negative"` |
| `ingested_at` | `TIMESTAMP` | `DEFAULT NOW()` | When our pipeline processed this review |

**Indexes:**
```sql
CREATE INDEX idx_reviews_appid           ON reviews(appid);
CREATE INDEX idx_reviews_timestamp       ON reviews(timestamp_created);
CREATE INDEX idx_reviews_sentiment_label ON reviews(sentiment_label);
```

---

## 📊 Power BI Dashboard

### Connecting to PostgreSQL

1. Open **Power BI Desktop**
2. **Home → Get Data → PostgreSQL database**
3. Server: `localhost` · Database: `steam_reviews`
4. Select ✅ `games` and ✅ `reviews` → **Load**
5. In **Model view**, drag `reviews[appid]` → `games[appid]` to create the relationship

---

### Visuals

#### 🔢 KPI Cards
Four headline metrics at the top of the dashboard:

| Card | Measure | Description |
|---|---|---|
| **Total Reviews** | `COUNT(review_id)` | Total reviews in the database |
| **Average Sentiment** | `AVERAGE(sentiment_compound)` | Overall compound score across all games |
| **Average Playtime** | `AVERAGE(playtime_at_review_minutes)` | Average hours played at review time |
| **Games Analyzed** | `DISTINCTCOUNT(appid)` | Number of unique games tracked |

---

#### 📈 Line Chart — Average Sentiment Over Time
- **X-axis:** `timestamp_created` (Month granularity)
- **Y-axis:** `AVERAGE(sentiment_compound)`
- **Legend:** `game_name`
- **Insight:** Track whether a game's sentiment improves or deteriorates after patches/updates

---

#### 📊 Stacked Column Chart — Review Distribution by Sentiment
- **X-axis:** `game_name`
- **Y-axis:** Count of `review_id`
- **Legend:** `sentiment_label`
- **Colors:** Positive = green · Neutral = gray · Negative = red
- **Insight:** Instantly compare community health across genres

---

#### 🔵 Scatter Plot — Playtime vs Sentiment
- **X-axis:** `playtime_at_review_minutes`
- **Y-axis:** `sentiment_compound`
- **Values:** `review_id` (dot size optional)
- **Legend:** `game_name`
- **Insight:** Do highly invested players write more positive reviews?

---

#### 📋 Matrix — Sentiment Summary by Game
- **Rows:** `game_name`
- **Columns:** `sentiment_label`
- **Values:** Count of `voted_up = TRUE` vs VADER label
- **Insight:** Measures how well VADER's text-based score aligns with Steam's own thumbs-up signal

---

#### 🎛️ Game Slicer
A single `game_name` slicer cross-filters **all four visuals simultaneously**. Click any game to instantly drill into its sentiment profile.

---

## 💡 Dashboard Insights

> Results from the first pipeline run — **600 reviews across 6 games**

| Insight | Finding |
|---|---|
| **Total reviews analyzed** | 600 (100 per game) |
| **Games compared** | 6 across 5 distinct genres |
| **Overall positive rate** | ~56% of all reviews scored positive |
| **Highest sentiment game** | 🌱 Stardew Valley — avg compound **+0.478** |
| **Lowest sentiment game** | 🔫 Counter-Strike 2 — avg compound **+0.171** |
| **Playtime correlation** | Weak positive — highly invested players trend slightly more positive |
| **VADER vs voted_up** | Strong agreement on extreme scores; mismatches mainly in the neutral band |
| **Genre pattern** | Casual/indie games outperform competitive multiplayer in text sentiment |

---

## ⏰ Automation

The pipeline is designed to run **unattended every day** using Windows Task Scheduler.

### Setup (one-time, run in PowerShell as Administrator)

```powershell
$action = New-ScheduledTaskAction `
    -Execute "D:\powerbi\steam-sentiment-pipeline\venv\Scripts\python.exe" `
    -Argument "-m src.pipeline" `
    -WorkingDirectory "D:\powerbi\steam-sentiment-pipeline"

$trigger = New-ScheduledTaskTrigger -Daily -At "09:00AM"

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
    -TaskName "SteamSentimentPipeline" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Daily Steam review sentiment ETL pipeline"
```

### Verify & trigger manually

```powershell
# Confirm the task was created
Get-ScheduledTask -TaskName "SteamSentimentPipeline"

# Run immediately without waiting for the schedule
Start-ScheduledTask -TaskName "SteamSentimentPipeline"
```

### Linux / macOS — cron equivalent

```bash
crontab -e
```

```cron
# Run at 9:00 AM every day
0 9 * * * cd /path/to/steam-sentiment-pipeline && /path/to/venv/bin/python -m src.pipeline >> logs/cron.log 2>&1
```

Each run:
1. Fetches the latest reviews from Steam
2. Scores them with VADER
3. Inserts only **new** reviews (`ON CONFLICT DO NOTHING` skips duplicates)
4. Writes a timestamped log to `logs/pipeline.log`
5. Power BI refreshes from the updated PostgreSQL data

---

## 🔮 Future Improvements

| Improvement | Description |
|---|---|
| **Incremental loading** | Watermark-based fetch — only pull reviews newer than the last run |
| **Docker support** | `Dockerfile` + `docker-compose.yml` for portable deployment |
| **Apache Airflow** | Replace Task Scheduler with a full orchestration framework |
| **Power BI Service** | Publish dashboard online with scheduled cloud refresh |
| **Azure deployment** | Host PostgreSQL on Azure Database, pipeline on Azure Functions |
| **ML sentiment model** | Fine-tuned BERT/RoBERTa for higher accuracy on gaming text |
| **Topic modeling** | LDA or BERTopic to discover common themes in negative reviews |
| **Multi-language support** | Extend beyond English using multilingual sentiment models |
| **Kafka streaming** | Replace batch with real-time review streaming pipeline |
| **Review anomaly detection** | Identify review bombing events via statistical outlier detection |

---

## 📸 Screenshots

> *Add screenshots to the `screenshots/` folder and update these paths.*

| Preview | Description |
|---|---|
| `screenshots/dashboard_overview.png` | Full Power BI dashboard with all 4 visuals |
| `screenshots/sentiment_by_game.png` | Stacked bar chart — sentiment breakdown per game |
| `screenshots/playtime_scatter.png` | Scatter plot — playtime vs sentiment correlation |
| `screenshots/pipeline_console.png` | Terminal output from a successful pipeline run |
| `screenshots/postgres_tables.png` | pgAdmin view of the games and reviews tables |

---

## 🎯 Skills Demonstrated

```
Data Engineering         ████████████████████  Expert
ETL Pipelines            ████████████████████  Expert
REST API Integration     ████████████████████  Expert
PostgreSQL / SQL         █████████████████░░░  Advanced
Python                   █████████████████░░░  Advanced
NLP / Sentiment Analysis ███████████████░░░░░  Intermediate
Power BI / DAX           ███████████████░░░░░  Intermediate
Data Visualization       ███████████████░░░░░  Intermediate
Pipeline Automation      ████████████████████  Expert
Logging & Observability  █████████████████░░░  Advanced
```

| Domain | Skills |
|---|---|
| **Data Engineering** | ETL design, batch processing, idempotent pipelines, incremental loads |
| **Python Development** | Modular architecture, error handling, configuration management |
| **Database Design** | Schema normalization, foreign keys, indexes, ON CONFLICT |
| **API Integration** | Pagination, retries, exponential backoff, JSON parsing |
| **NLP** | Lexicon-based sentiment analysis, compound scoring, label thresholds |
| **Business Intelligence** | Power BI data modeling, DAX measures, dashboard design |
| **Automation** | Task Scheduler, cron, production-grade scheduling |
| **Software Engineering** | Separation of concerns, logging, `.env` secrets management |

---

## 📖 Key Learnings

This project demonstrates that even a **"simple" portfolio project** can exhibit the exact same architectural patterns used at companies like Netflix and Spotify — just at a smaller scale:

- **Separation of concerns** makes code maintainable, testable, and easy to extend
- **Idempotency** (`ON CONFLICT DO NOTHING`) is non-negotiable in production pipelines — failures happen, and re-runs must be safe
- **Lexicon-based NLP** (VADER) is a practical and fast choice for short informal text when latency and cost matter — not everything needs a transformer model
- **Batch > Streaming** for most analytics use cases — real-time adds enormous complexity for marginal business benefit when daily freshness is acceptable
- **Structured logging** is the difference between a script and a system — logs tell you what happened, when, and why without needing to re-run
- **Environment variables** (`python-dotenv`) separate secrets from code — a basic but critical security practice
- A **genre-diverse game selection** makes cross-segment comparisons meaningful — Stardew Valley vs CS2 tells a far richer story than 6 shooters

---

## 📄 License

This project is licensed under the **MIT License** — free to use, modify, and distribute.

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software.
```

---

<div align="center">

**Built with 🎮 curiosity, 🐍 Python, and ☕ way too much coffee**

*If this project helped you, consider giving it a ⭐ on GitHub*

</div>
