import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app import create_app
from config import Config
from models.game import Game
from models.user import Pool


class TestConfig(Config):
    TESTING = True


@pytest.fixture
def app(tmp_path):
    TestConfig.DATABASE_URL = str(tmp_path / "test.db")
    app = create_app(TestConfig)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def login_user(client):
    client.post(
        "/register",
        json={"name": "Apostador", "email": "apostador@example.com", "password": "senha123"},
    )


def create_game(app):
    with app.app_context():
        pool = Pool.get_default()
        game = Game.create(pool["id"], "Brasil", "Argentina", "2026-07-01T18:00")
        return game["id"]


from utils.messages import ApiMessages


def test_create_bet(client, app):
    login_user(client)
    game_id = create_game(app)
    response = client.post(
        f"/bets/game/{game_id}",
        json={"predicted_home_score": 2, "predicted_away_score": 1},
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == ApiMessages.BET_CREATE_SUCCESS


def test_reject_negative_bet(client, app):
    login_user(client)
    game_id = create_game(app)
    response = client.post(
        f"/bets/game/{game_id}",
        json={"predicted_home_score": -1, "predicted_away_score": 1},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == ApiMessages.BET_INVALID


def test_block_bet_after_finished_game(client, app):
    login_user(client)
    game_id = create_game(app)
    with app.app_context():
        Game.record_result(game_id, 1, 0)

    response = client.post(
        f"/bets/game/{game_id}",
        json={"predicted_home_score": 1, "predicted_away_score": 0},
    )

    assert response.status_code == 400
    assert "Apostas encerradas" in response.get_json()["error"]

