from flask import current_app

from models.bet import Bet
from models.score import Score
from services.football_service import FootballService


def _db():
    from app import get_db

    return get_db()


def _winner(home_score, away_score):
    if home_score > away_score:
        return "home"
    if away_score > home_score:
        return "away"
    return "draw"


class ScoringService:
    @staticmethod
    def calculate_score(game, bet):
        if game["home_score"] is None or game["away_score"] is None:
            return 0

        actual_home = int(game["home_score"])
        actual_away = int(game["away_score"])
        predicted_home = int(bet["predicted_home_score"])
        predicted_away = int(bet["predicted_away_score"])

        if predicted_home == actual_home and predicted_away == actual_away:
            return current_app.config["EXACT_SCORE_POINTS"]

        actual_winner = _winner(actual_home, actual_away)
        predicted_winner = _winner(predicted_home, predicted_away)

        if actual_winner == "draw" and predicted_winner == "draw":
            return current_app.config["DRAW_POINTS"]

        if actual_winner == predicted_winner:
            if predicted_home == actual_home or predicted_away == actual_away:
                return current_app.config["WINNER_AND_GOALS_POINTS"]
            return current_app.config["WINNER_ONLY_POINTS"]

        return 0

    @staticmethod
    def recalculate_game(game_id):
        game = _db().execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if game is None:
            return []
        if game["external_match_id"] and game["status"] != "finished":
            game = FootballService.sync_result_to_db(game)

        updated = []
        for bet in Bet.list(game_id=game_id):
            points = ScoringService.calculate_score(game, bet)
            Bet.update_points(bet["id"], points)
            updated.append((bet["id"], points))
        ScoringService.recalculate_ranking(game["pool_id"])
        return updated

    @staticmethod
    def recalculate_ranking(pool_id):
        rows = _db().execute(
            """
            SELECT pool_members.user_id, COALESCE(SUM(bets.points_earned), 0) AS total_points
              FROM pool_members
              LEFT JOIN games ON games.pool_id = pool_members.pool_id
              LEFT JOIN bets ON bets.game_id = games.id AND bets.user_id = pool_members.user_id
             WHERE pool_members.pool_id = ?
             GROUP BY pool_members.user_id
            """,
            (pool_id,),
        ).fetchall()

        for row in rows:
            Score.update(pool_id, row["user_id"], row["total_points"])
        return Score.get_ranking(pool_id)
