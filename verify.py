import psycopg2
from src.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
cur = conn.cursor()

print("=== GAMES TABLE ===")
cur.execute("SELECT appid, game_name, genre FROM games ORDER BY appid;")
for row in cur.fetchall():
    print(f"  {row[0]:>7} | {row[1]:<25} | {row[2]}")

print()
print("=== REVIEWS PER GAME (sorted by avg sentiment) ===")
cur.execute("""
    SELECT g.game_name,
           COUNT(*) as total,
           ROUND(AVG(r.sentiment_compound)::numeric, 3) as avg_sentiment,
           SUM(CASE WHEN r.sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive,
           SUM(CASE WHEN r.sentiment_label = 'neutral'  THEN 1 ELSE 0 END) as neutral,
           SUM(CASE WHEN r.sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative
    FROM reviews r
    JOIN games g ON r.appid = g.appid
    GROUP BY g.game_name
    ORDER BY avg_sentiment DESC;
""")
header = f"  {'Game':<25} | {'Total':>5} | {'Avg Score':>9} | {'Pos':>4} | {'Neu':>4} | {'Neg':>4}"
print(header)
print("  " + "-" * 62)
for row in cur.fetchall():
    print(f"  {row[0]:<25} | {row[1]:>5} | {float(row[2]):>9.3f} | {row[3]:>4} | {row[4]:>4} | {row[5]:>4}")

print()
print("=== SAMPLE REVIEWS (5 random) ===")
cur.execute("""
    SELECT g.game_name, LEFT(r.review_text, 70), r.sentiment_compound, r.sentiment_label
    FROM reviews r
    JOIN games g ON r.appid = g.appid
    ORDER BY RANDOM()
    LIMIT 5;
""")
for row in cur.fetchall():
    print(f"  [{row[3]:>8}] {float(row[2]):>6.3f} | {row[0]:<22} | {row[1]}...")

print()
print("=== voted_up vs VADER agreement ===")
cur.execute("""
    SELECT
        voted_up,
        sentiment_label,
        COUNT(*) as count
    FROM reviews
    GROUP BY voted_up, sentiment_label
    ORDER BY voted_up DESC, count DESC;
""")
print(f"  {'voted_up':<10} | {'VADER label':<12} | {'Count':>6}")
print("  " + "-" * 35)
for row in cur.fetchall():
    print(f"  {str(row[0]):<10} | {row[1]:<12} | {row[2]:>6}")

conn.close()
print("\nDatabase verification complete!")
