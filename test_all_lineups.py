import requests
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db = os.environ.get('DATABASE_URL')
api_key = os.environ.get('API_SPORTS_KEY')
conn = psycopg2.connect(db)
cur = conn.cursor()

# Get recent PAST games
cur.execute('SELECT id, home_team, away_team, external_match_id, match_datetime, status FROM games WHERE external_match_id IS NOT NULL AND match_datetime < CURRENT_TIMESTAMP ORDER BY match_datetime DESC LIMIT 15')
rows = cur.fetchall()

headers = {'x-apisports-key': api_key}
print(f"{'Data':<12} | {'Status':<10} | {'Jogo':<40} | {'Tem Escalação?'}")
print("-" * 85)

for r in rows:
    game_id, home, away, ext_id, dt, status = r
    dt_str = dt.strftime("%d/%m %H:%M")
    
    # Query API
    res = requests.get('https://v3.football.api-sports.io/fixtures/lineups', params={'fixture': ext_id}, headers=headers)
    data = res.json()
    
    resp = data.get('response', [])
    has_lineups = "Sim" if len(resp) > 0 else "Não"
    
    game_name = f"{home} x {away}"
    print(f"{dt_str:<12} | {status:<10} | {game_name:<40} | {has_lineups}")
