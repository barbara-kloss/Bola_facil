from app import create_app
from services.football_service import FootballService

app = create_app()
with app.app_context():
    print("Starting sync of 2022 matches...")
    synced = FootballService.sync_matches_to_db()
    print("Successfully synced", len(synced), "matches!")
    if synced:
        print("First synced match ID in DB:", synced[0]['id'], "External Match ID:", synced[0]['external_match_id'])
