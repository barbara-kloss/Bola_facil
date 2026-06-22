from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.game import Game
from models.score import Score
from models.user import Pool, PoolMember
from services.scoring_service import ScoringService
from utils.helpers import format_match_time, match_status_label
from utils.messages import ApiMessages
from utils.responses import respond


game_bp = Blueprint("games", __name__)
ITEMS_PER_PAGE = 15


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
    if not pool:
        return render_template(
            "games/list.html",
            pool=None,
            games=[],
            current_page=1,
            total_pages=1,
            is_admin=current_user.is_admin,
        )

    # Obter página do query parameter
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    # Obter todos os jogos
    all_games = Game.list(pool["id"]) if pool else []

    # Calcular paginação
    total_items = len(all_games)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    # Validar página
    if page > total_pages and total_pages > 0:
        page = total_pages

    # Paginar os resultados
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    games = all_games[start_idx:end_idx]

    return render_template(
        "games/list.html",
        pool=pool,
        games=games,
        current_page=page,
        total_pages=total_pages,
        total_items=total_items,
        items_per_page=ITEMS_PER_PAGE,
        is_admin=current_user.is_admin,
        format_match_time=format_match_time,
        match_status_label=match_status_label,
    )


from utils.decorators import admin_required
from models.notification import Notification

@game_bp.route("/games/create", methods=["POST"])
@admin_required
def create_game():
    pool = _default_pool()
    data = request.get_json(silent=True) or request.form
    
    try:
        game = Game.create(
            pool["id"],
            data.get("home_team", "").strip(),
            data.get("away_team", "").strip(),
            data.get("match_datetime", "").strip(),
            data.get("status", "scheduled"),
        )

        # Notificar apenas membros do bolão ao qual o jogo pertence
        pool_users = _db().execute(
            "SELECT user_id FROM pool_members WHERE pool_id = ? AND user_id != ?",
            (pool["id"], current_user.id),
        ).fetchall()
        for u in pool_users:
            Notification.create(
                user_id=u["user_id"],
                type="new_game",
                title="Novo Jogo Adicionado!",
                body=f"{game['home_team']} vs {game['away_team']} — clique para palpitar!",
                extra_data={"game_id": game["id"]}
            )

        return respond(
            ApiMessages.GAME_CREATE_SUCCESS,
            ok=True, status=201, redirect_to="games.list_games",
            data={"game_id": game["id"]},
        )
    except ValueError as e:
        return respond(str(e), ok=False, status=400, redirect_to="games.list_games")
    except Exception:
        return respond(
            ApiMessages.GAME_CREATE_ERROR,
            ok=False, redirect_to="games.list_games",
        )


@game_bp.route("/games/<int:game_id>")
@login_required
def game_detail(game_id):
    game = Game.get_by_id(game_id)
    if game is None:
        return jsonify({"error": ApiMessages.GAME_NOT_FOUND}), 404
    
    if not current_user.is_admin and not PoolMember.exists(game["pool_id"], current_user.id):
        from flask import abort
        abort(403)
    
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
@admin_required
def record_result(game_id):
    data = request.get_json(silent=True) or request.form
    
    game = Game.get_by_id(game_id)
    if not game:
        return respond("Jogo não encontrado.", ok=False, status=404, redirect_to="games.list_games")
        
    if game["status"] in ["finished", "cancelled"]:
        return respond("Não é possível registrar resultado para jogos já finalizados ou cancelados.", ok=False, redirect_to=url_for("games.game_detail", game_id=game_id))
    
    try:
        home_score = int(data.get("home_score", 0))
        away_score = int(data.get("away_score", 0))
        
        if home_score < 0 or away_score < 0:
            raise ValueError("Placar não pode ser negativo")
            
        game = Game.record_result(game_id, home_score, away_score)
        ScoringService.recalculate_game(game_id)
        
        # Notificar membros do bolão sobre o resultado
        pool_members = _db().execute(
            "SELECT user_id FROM pool_members WHERE pool_id = ?",
            (game["pool_id"],),
        ).fetchall()
        for m in pool_members:
            Notification.create(
                user_id=m["user_id"],
                type="result",
                title="Resultado Registrado!",
                body=f"{game['home_team']} {home_score} x {away_score} {game['away_team']} — confira sua pontuação!",
                extra_data={"game_id": game["id"]},
            )

        return respond(
            ApiMessages.GAME_RESULT_RECORDED,
            ok=True, redirect_to=url_for("games.game_detail", game_id=game_id),
            data={"game_id": game["id"]},
        )
    except (ValueError, TypeError):
        return respond(
            ApiMessages.GAME_RESULT_ERROR,
            ok=False, redirect_to=url_for("games.game_detail", game_id=game_id),
        )


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
