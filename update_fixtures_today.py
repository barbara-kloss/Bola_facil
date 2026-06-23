import psycopg2
import requests

DATABASE_URL = "postgresql://postgres:b8RDz%23w%3FdHc_f%3Ff@db.veooiziqewuoolrkrfdf.supabase.co:5432/postgres"

api_key = '6de3a3775b9ee3aca616e24dbcd42893'
headers = {'x-apisports-key': api_key}
res = requests.get('https://v3.football.api-sports.io/fixtures', params={'date': '2026-06-23'}, headers=headers)
fixtures = res.json().get('response', [])

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("SELECT id, home_team, away_team, external_match_id FROM games")
db_games = cur.fetchall()

updated_count = 0
for f in fixtures:
    if f['league']['id'] == 1:
        api_id = f['fixture']['id']
        api_home = f['teams']['home']['name'].lower().strip()
        api_away = f['teams']['away']['name'].lower().strip()
        home_logo = f['teams']['home']['logo']
        away_logo = f['teams']['away']['logo']
        api_status = f['fixture']['status']['short']
        
        for db_id, db_home, db_away, db_ext in db_games:
            # Compare names (flexible matching)
            if (db_home.lower().strip() == api_home or api_home in db_home.lower() or db_home.lower() in api_home) and \
               (db_away.lower().strip() == api_away or api_away in db_away.lower() or db_away.lower() in api_away):
                print(f"Matching DB Game {db_id}: {db_home} vs {db_away} (old ID: {db_ext}) -> API ID: {api_id}")
                
                # Update external_match_id, logos, and api_status in postgres database
                cur.execute(
                    """
                    UPDATE games 
                    SET external_match_id = %s, home_crest = %s, away_crest = %s, api_status = %s
                    WHERE id = %s
                    """,
                    (api_id, home_logo, away_logo, api_status, db_id)
                )
                updated_count += 1
                break

conn.commit()
cur.close()
conn.close()
print(f"Successfully matched and updated {updated_count} matches in the database!")
