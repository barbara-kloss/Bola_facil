from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models.bet import Bet
from models.game import Game
from models.user import PoolMember


bet_bp = Blueprint("bets", __name__, url_prefix="/bets")


@bet_bp.route("/game/<int:game_id>", methods=["GET", "POST"])
@login_required
def bet_game(game_id):
    game = Game.get_by_id(game_id)
    if game is None:
        return jsonify({"error": "Jogo não encontrado."}), 404
    if not PoolMember.exists(game["pool_id"], current_user.id):
        PoolMember.add(game["pool_id"], current_user.id)

    existing_bet = Bet.get_by_user_and_game(current_user.id, game_id)

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        if game["status"] == "finished":
            message = "Palpites encerrados para este jogo."
            if request.is_json:
                return jsonify({"error": message}), 400
            flash(message, "error")
            return render_template("bets/form.html", game=game, bet=existing_bet), 400

        try:
            home_score = int(data.get("predicted_home_score"))
            away_score = int(data.get("predicted_away_score"))
        except (TypeError, ValueError):
            home_score = away_score = -1

        if home_score < 0 or away_score < 0:
            message = "O placar não pode ser negativo."
            if request.is_json:
                return jsonify({"error": message}), 400
            flash(message, "error")
            return render_template("bets/form.html", game=game, bet=existing_bet), 400

        bet = Bet.create(current_user.id, game_id, home_score, away_score)
        if request.is_json:
            return jsonify({"message": "Palpite salvo com sucesso.", "bet_id": bet["id"]})
        flash("Palpite salvo com sucesso.", "success")
        return redirect(url_for("games.game_detail", game_id=game_id))

    return render_template("bets/form.html", game=game, bet=existing_bet)
