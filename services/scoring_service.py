from flask import current_app
import logging

from models.bet import Bet
from models.score import Score
from services.football_service import FootballService

logger = logging.getLogger(__name__)


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
            logger.debug(f"calculate_score: Jogo {game['id']} sem placar definido, retornando 0 pts.")
            return 0

        try:
            actual_home = int(game["home_score"])
            actual_away = int(game["away_score"])
            predicted_home = int(bet["predicted_home_score"])
            predicted_away = int(bet["predicted_away_score"])
        except (ValueError, TypeError):
            logger.error(f"calculate_score: Erro de conversão de placares (Jogo: {game['home_score']}x{game['away_score']} | Palpite {bet['id']}: {bet['predicted_home_score']}x{bet['predicted_away_score']})")
            return 0
            
        logger.debug(f"calculate_score: Calculando pontos. Placar Real: {actual_home}x{actual_away} | Palpite {bet['id']}: {predicted_home}x{predicted_away}")

        if predicted_home == actual_home and predicted_away == actual_away:
            points = current_app.config["EXACT_SCORE_POINTS"]
            logger.debug(f"calculate_score: Acerto de placar exato. Pontos: {points}")
            return points

        actual_winner = _winner(actual_home, actual_away)
        predicted_winner = _winner(predicted_home, predicted_away)

        if actual_winner == "draw" and predicted_winner == "draw":
            points = current_app.config["DRAW_POINTS"]
            logger.debug(f"calculate_score: Acerto de empate (placar diferente). Pontos: {points}")
            return points

        if actual_winner == predicted_winner:
            if predicted_home == actual_home or predicted_away == actual_away:
                points = current_app.config["WINNER_AND_GOALS_POINTS"]
                logger.debug(f"calculate_score: Acerto de vencedor e gols de 1 time. Pontos: {points}")
                return points
            points = current_app.config["WINNER_ONLY_POINTS"]
            logger.debug(f"calculate_score: Acerto apenas de vencedor. Pontos: {points}")
            return points

        logger.debug("calculate_score: Nenhum acerto. Pontos: 0")
        return 0

    @staticmethod
    def recalculate_game(game_id):
        logger.info(f"recalculate_game: Iniciando recálculo para o jogo {game_id}")
        game = _db().execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if game is None:
            logger.warning(f"recalculate_game: Jogo {game_id} não encontrado")
            return []
            
        if game["external_match_id"] and game["status"] != "finished":
            game = FootballService.sync_result_to_db(game)
            
        if game["status"] != "finished" and (game["home_score"] is None or game["away_score"] is None):
            logger.info(f"recalculate_game: Jogo {game_id} ainda não finalizado e sem placar. Abortando.")
            return []

        updated = []
        for bet in Bet.list(game_id=game_id):
            points = ScoringService.calculate_score(game, bet)
            Bet.update_points(bet["id"], points)
            updated.append((bet["id"], points))
            
        logger.info(f"recalculate_game: Recalculando ranking do bolão {game['pool_id']}")
        ScoringService.recalculate_ranking(game["pool_id"])
        
        logger.info(f"recalculate_game: Concluído para o jogo {game_id}. Palpites atualizados: {len(updated)}")
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
