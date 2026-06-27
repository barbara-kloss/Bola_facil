import psycopg2
import os
from dotenv import load_dotenv
import requests

load_dotenv()
db = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(db)
cur = conn.cursor()
cur.execute('SELECT id, external_match_id, match_datetime, status FROM games WHERE external_match_id IS NOT NULL LIMIT 5')
rows = cur.fetchall()
print("Games in DB:")
for r in rows:
    print(r)

if rows:
    game = rows[0]
    api_key = os.environ.get('API_SPORTS_KEY')
    headers = {'x-apisports-key': api_key}
    print(f"\nFetching lineups for fixture_id={game[1]} from API...")
    res = requests.get('https://v3.football.api-sports.io/fixtures/lineups', params={'fixture': game[1]}, headers=headers)
    print("Status:", res.status_code)
    data = res.json()
    print("Errors:", data.get('errors'))
    print("Response length:", len(data.get('response', [])))
    if data.get('response'):
        print("Home team formation:", data['response'][0].get('formation'))
        print("Away team formation:", data['response'][1].get('formation'))
