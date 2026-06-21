import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app import create_app
from config import Config
from models.bet import Bet
from models.game import Game
from models.score import Score
from models.user import Pool, User
from services.scoring_service import ScoringService


class TestConfig(Config):
    TESTING = True


@pytest.fixture
def app(tmp_path):
    TestConfig.DATABASE_URL = str(tmp_path / "test.db")
    app = create_app(TestConfig)
    yield app


def make_game_and_bet(app, prediction, result):
    with app.app_context():
        user = User.create("Jogador", f"jogador{prediction[0]}{prediction[1]}@example.com", "senha123")
        pool = Pool.get_default() or Pool.create("Bolão Teste", user.id)
        game = Game.create(pool["id"], "Casa", "Fora", "2026-07-01T18:00")
        bet = Bet.create(user.id, game["id"], prediction[0], prediction[1])
        Game.record_result(game["id"], result[0], result[1])
        game = Game.get_by_id(game["id"])
        bet = Bet.get_by_id(bet["id"])
        return game, bet


@pytest.mark.parametrize(
    "prediction,result,expected",
    [
        ((2, 1), (2, 1), 10),
        ((2, 0), (2, 1), 5),
        ((3, 0), (2, 1), 3),
        ((1, 1), (2, 2), 2),
        ((0, 2), (2, 1), 0),
    ],
)
def test_calculate_score(app, prediction, result, expected):
    game, bet = make_game_and_bet(app, prediction, result)
    with app.app_context():
        assert ScoringService.calculate_score(game, bet) == expected


def test_recalculate_ranking(app):
    with app.app_context():
        user = User.create("Ranking User", "ranking@example.com", "senha123")
        pool = Pool.get_default() or Pool.create("Bolão Ranking", user.id)
        game = Game.create(pool["id"], "Casa", "Fora", "2026-07-01T18:00")
        Bet.create(user.id, game["id"], 2, 1)
        Game.record_result(game["id"], 2, 1)

        ScoringService.recalculate_game(game["id"])
        ranking = Score.get_ranking(pool["id"])

        assert ranking[0]["name"] == "Ranking User"
        assert ranking[0]["total_points"] == 10
