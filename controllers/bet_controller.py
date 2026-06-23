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
        match_dt = game["match_datetime"]
        if isinstance(match_dt, str):
            match_time = datetime.fromisoformat(match_dt.replace('Z', '+00:00'))
        else:
            match_time = match_dt
            
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


@bet_bp.route("/historico", methods=["GET"])
@login_required
def bet_history():
    """Histórico de todos os palpites do usuário logado."""
    from app import get_db
    db = get_db()
    rows = db.execute(
        """
        SELECT
            b.id AS bet_id,
            b.predicted_home_score,
            b.predicted_away_score,
            b.points_earned,
            b.created_at AS bet_created_at,
            g.id AS game_id,
            g.home_team,
            g.away_team,
            g.home_crest,
            g.away_crest,
            g.home_score,
            g.away_score,
            g.status AS game_status,
            g.match_datetime,
            g.competition_name,
            g.matchday
        FROM bets b
        JOIN games g ON g.id = b.game_id
        WHERE b.user_id = ?
        ORDER BY g.match_datetime DESC
        """,
        (current_user.id,),
    ).fetchall()

    def _result_status(row):
        if row["game_status"] != "finished":
            return "pending"
        if row["home_score"] is None or row["away_score"] is None:
            return "pending"
        ph = int(row["predicted_home_score"])
        pa = int(row["predicted_away_score"])
        ah = int(row["home_score"])
        aa = int(row["away_score"])
        if ph == ah and pa == aa:
            return "exact"
        def winner(h, a): return "home" if h > a else ("away" if a > h else "draw")
        if winner(ph, pa) == winner(ah, aa):
            return "winner"
        return "miss"

    bets = []
    for row in rows:
        bets.append({
            "row": row,
            "result": _result_status(row),
        })

    return render_template("bets/history.html", bets=bets, format_match_time=format_match_time)
