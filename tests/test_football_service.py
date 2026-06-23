import sys
from pathlib import Path
import sqlite3
import pytest
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as flask_app
from config import Config
from models.game import Game
from models.user import Pool, User
from services.football_service import FootballService


class TestConfig(Config):
    TESTING = True
    API_SPORTS_KEY = "test-token"
    DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def app(tmp_path, monkeypatch):
    # Mock init_database so it doesn't connect to Postgres
    monkeypatch.setattr(flask_app, "init_database", lambda app: None)

    # Create a local sqlite connection
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    # Register NOW() function for SQLite compatibility
    conn.create_function("NOW", 0, lambda: datetime.now().isoformat())

    # Load SQLite schema
    schema_path = Path(flask_app.__file__).parent / "database" / "schema.sql"
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.commit()

    # Mock get_db to return this sqlite connection wrapped in a simple wrapper
    class SqliteWrapper:
        def __init__(self, c):
            self.c = c
        def execute(self, sql, params=()):
            return self.c.execute(sql, params)
        def commit(self):
            self.c.commit()
        def close(self):
            pass

    wrapper = SqliteWrapper(conn)
    monkeypatch.setattr(flask_app, "get_db", lambda: wrapper)

    app_instance = flask_app.create_app(TestConfig)
    
    yield app_instance

    conn.close()


def test_normalize_match_maps_api_fields(app):
    with app.app_context():
        match = FootballService._normalize_match(
            {
                "fixture": {
                    "id": 123,
                    "date": "2026-06-21T19:00:00+00:00",
                    "status": {"short": "NS"}
                },
                "league": {
                    "id": 1,
                    "name": "World Cup",
                    "round": "Group Stage - 10"
                },
                "teams": {
                    "home": {"name": "Avaí FC", "logo": "https://example.com/avai.svg"},
                    "away": {"name": "Cuiabá EC", "logo": "https://example.com/cuiaba.svg"}
                },
                "goals": {"home": None, "away": None}
            }
        )

    assert match["external_match_id"] == 123
    assert match["competition_code"] == "1"
    assert match["home_team"] == "Avaí FC"
    assert match["status"] == "scheduled"


def test_sync_matches_to_db_uses_local_database(app, monkeypatch):
    payload = {
        "response": [
            {
                "fixture": {
                    "id": 456,
                    "date": "2026-06-21T19:00:00+00:00",
                    "status": {"short": "NS"}
                },
                "league": {
                    "id": 1,
                    "name": "World Cup",
                    "round": "Group Stage - 12"
                },
                "teams": {
                    "home": {"name": "CR Brasil", "logo": "https://example.com/crb.svg"},
                    "away": {"name": "Fortaleza EC", "logo": "https://example.com/fortaleza.svg"}
                },
                "goals": {"home": None, "away": None}
            }
        ]
    }

    monkeypatch.setattr(FootballService, "get_next_matches", staticmethod(lambda: payload))

    with app.app_context():
        user = User.create("Admin", "admin@example.com", "senha123")
        Pool.create("Bolão API", user.id)
        synced = FootballService.sync_matches_to_db()
        game = Game.get_by_external_match_id(456)

    assert len(synced) == 1
    assert game["home_team"] == "CR Brasil"
    assert game["matchday"] == 12
