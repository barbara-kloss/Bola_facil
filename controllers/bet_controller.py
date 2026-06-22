from flask import Blueprint, render_template, request, url_for
from flask_login import current_user, login_required

from models.bet import Bet
from models.game import Game
from models.user import PoolMember
from utils.messages import ApiMessages
from utils.responses import respond
from datetime import datetime, timedelta
from flask import current_app


bet_bp = Blueprint("bets", __name__, url_prefix="/bets")


@bet_bp.route("/game/<int:game_id>", methods=["GET", "POST"])
@login_required
def bet_game(game_id):
    game = Game.get_by_id(game_id)
    if game is None:
        return respond(ApiMessages.GAME_NOT_FOUND, ok=False, status=404,
                       redirect_to="games.list_games")

    if not PoolMember.exists(game["pool_id"], current_user.id):
        PoolMember.add(game["pool_id"], current_user.id)

    existing_bet = Bet.get_by_user_and_game(current_user.id, game_id)

    lockout_minutes = current_app.config.get("BET_LOCKOUT_MINUTES", 30)
    try:
        match_time = datetime.fromisoformat(game["match_datetime"].replace('Z', '+00:00'))
        if match_time.tzinfo:
            now = datetime.now(match_time.tzinfo)
        else:
            now = datetime.now()
        
        is_locked = (match_time - now) < timedelta(minutes=lockout_minutes)
    except ValueError:
        is_locked = False

    is_closed = game["status"] != "scheduled" or is_locked

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form

        if is_closed:
            return respond(
                f"Apostas encerradas para este jogo. O prazo limite é de {lockout_minutes} minutos antes da partida.",
                ok=False, status=400,
                template_fn=render_template,
                template_kwargs={"template_name_or_list": "bets/form.html",
                                 "game": game, "bet": existing_bet},
            )

        try:
            home_score = int(data.get("predicted_home_score"))
            away_score = int(data.get("predicted_away_score"))
        except (TypeError, ValueError):
            home_score = away_score = -1

        if home_score < 0 or away_score < 0:
            return respond(
                ApiMessages.BET_INVALID,
                ok=False, status=400,
                template_fn=render_template,
                template_kwargs={"template_name_or_list": "bets/form.html",
                                 "game": game, "bet": existing_bet},
            )

        bet = Bet.create(current_user.id, game_id, home_score, away_score)
        return respond(
            ApiMessages.BET_CREATE_SUCCESS,
            ok=True, redirect_to=url_for("games.game_detail", game_id=game_id),
            data={"bet_id": bet["id"]},
        )

    return render_template("bets/form.html", game=game, bet=existing_bet, is_closed=is_closed, lockout_minutes=lockout_minutes)
