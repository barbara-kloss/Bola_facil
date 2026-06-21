from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.game import Game
from models.score import Score
from models.user import Pool, PoolMember
from services.scoring_service import ScoringService
from utils.helpers import format_match_time, match_status_label


game_bp = Blueprint("games", __name__)


def _db():
    from app import get_db

    return get_db()


def _default_pool():
    pool = Pool.get_default()
    if pool is None and current_user.is_authenticated:
        pool = Pool.create("Bolão Principal", current_user.id, "Grupo principal do BolãoFácil")
    if pool and current_user.is_authenticated and not PoolMember.exists(pool["id"], current_user.id):
        PoolMember.add(pool["id"], current_user.id)
    return pool


@game_bp.route("/games")
@login_required
def list_games():
    pool = _default_pool()
    games = Game.list(pool["id"]) if pool else []
    return render_template(
        "games/list.html",
        pool=pool,
        games=games,
        is_admin=True,
        format_match_time=format_match_time,
        match_status_label=match_status_label,
    )


@game_bp.route("/games/create", methods=["POST"])
@login_required
def create_game():
    pool = _default_pool()
    data = request.get_json(silent=True) or request.form
    game = Game.create(
        pool["id"],
        data.get("home_team", "").strip(),
        data.get("away_team", "").strip(),
        data.get("match_datetime", "").strip(),
        data.get("status", "scheduled"),
    )
    if request.is_json:
        return jsonify({"message": "Jogo criado com sucesso.", "game_id": game["id"]}), 201
    flash("Jogo criado com sucesso.", "success")
    return redirect(url_for("games.list_games"))


@game_bp.route("/games/<int:game_id>")
@login_required
def game_detail(game_id):
    game = Game.get_by_id(game_id)
    if game is None:
        return jsonify({"error": "Jogo não encontrado."}), 404
    ranking = Score.get_ranking(game["pool_id"])
    bets = _db().execute(
        """
        SELECT bets.*, users.name
          FROM bets
          JOIN users ON users.id = bets.user_id
         WHERE bets.game_id = ?
         ORDER BY bets.points_earned DESC, users.name
        """,
        (game_id,),
    ).fetchall()
    return render_template(
        "games/detail.html",
        game=game,
        ranking=ranking,
        bets=bets,
        format_match_time=format_match_time,
        match_status_label=match_status_label,
    )


@game_bp.route("/games/<int:game_id>/result", methods=["POST"])
@login_required
def record_result(game_id):
    data = request.get_json(silent=True) or request.form
    home_score = int(data.get("home_score", 0))
    away_score = int(data.get("away_score", 0))
    game = Game.record_result(game_id, home_score, away_score)
    ScoringService.recalculate_game(game_id)
    if request.is_json:
        return jsonify({"message": "Resultado lançado com sucesso.", "game_id": game["id"]})
    flash("Resultado lançado com sucesso.", "success")
    return redirect(url_for("games.game_detail", game_id=game_id))


@game_bp.route("/chat")
@login_required
def chat():
    return render_template("chat/index.html")


@game_bp.route("/chat/messages", methods=["GET", "POST"])
@login_required
def chat_messages():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()
        return jsonify({"name": current_user.name, "text": text})
    return jsonify(
        [
            {"name": "BolãoFácil", "text": "Bem-vindo ao chat do bolão."},
            {"name": current_user.name, "text": "Pronto para palpitar!"},
        ]
    )
