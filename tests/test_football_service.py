import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app import create_app
from config import Config
from models.game import Game
from models.user import Pool, User
from services.football_service import FootballService


class TestConfig(Config):
    TESTING = True
    FOOTBALL_API_KEY = "test-token"


@pytest.fixture
def app(tmp_path):
    TestConfig.DATABASE_URL = str(tmp_path / "test.db")
    app = create_app(TestConfig)
    yield app


def test_normalize_match_maps_api_fields(app):
    with app.app_context():
        match = FootballService._normalize_match(
            {
                "id": 123,
                "utcDate": "2026-06-21T19:00:00Z",
                "status": "TIMED",
                "matchday": 10,
                "competition": {"code": "BSA", "name": "Brasileirão Série A"},
                "homeTeam": {"shortName": "Avaí FC", "crest": "https://example.com/avai.svg"},
                "awayTeam": {"shortName": "Cuiabá EC", "crest": "https://example.com/cuiaba.svg"},
                "score": {"fullTime": {"home": None, "away": None}},
            }
        )

    assert match["external_match_id"] == 123
    assert match["competition_code"] == "BSA"
    assert match["home_team"] == "Avaí FC"
    assert match["status"] == "scheduled"


def test_sync_matches_to_db_uses_local_database(app, monkeypatch):
    payload = {
        "matches": [
            {
                "id": 456,
                "utcDate": "2026-06-21T19:00:00Z",
                "status": "SCHEDULED",
                "matchday": 12,
                "competition": {"code": "BSA", "name": "Brasileirão Série A"},
                "homeTeam": {"shortName": "CR Brasil", "crest": "https://example.com/crb.svg"},
                "awayTeam": {"shortName": "Fortaleza EC", "crest": "https://example.com/fortaleza.svg"},
                "score": {"fullTime": {"home": None, "away": None}},
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
