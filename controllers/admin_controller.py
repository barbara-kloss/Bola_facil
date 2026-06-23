from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from utils.decorators import admin_required
from models.user import User

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/dashboard")
@admin_required
def dashboard():
    from app import get_db
    db = get_db()

    # Contadores de jogos por status
    def count_games(status):
        row = db.execute("SELECT COUNT(*) FROM games WHERE status = ?", (status,)).fetchone()
        return row[0] if row else 0

    stats = {
        "live": count_games("live"),
        "scheduled": count_games("scheduled"),
        "finished": count_games("finished"),
        "total_bets": db.execute("SELECT COUNT(*) FROM bets").fetchone()[0],
        "total_users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
    }

    # Jogos por mês (últimos 6 meses)
    monthly = db.execute(
        """
        SELECT TO_CHAR(match_datetime, 'Mon/YY') AS month,
               COUNT(*) AS total
          FROM games
         WHERE match_datetime >= NOW() - INTERVAL '6 months'
         GROUP BY TO_CHAR(match_datetime, 'Mon/YY'), DATE_TRUNC('month', match_datetime)
         ORDER BY DATE_TRUNC('month', match_datetime)
        """
    ).fetchall()
    monthly_labels = [r["month"] for r in monthly]
    monthly_data = [r["total"] for r in monthly]

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        monthly_labels=monthly_labels,
        monthly_data=monthly_data,
    )

@admin_bp.route("/admin/users")
@admin_required
def users():
    all_users = User.list()
    return render_template("admin/users.html", users=all_users)

@admin_bp.route("/admin/alerts")
@admin_required
def alerts():
    from models.notification import Notification
    all_alerts = Notification.list_all(100)
    return render_template("admin/alerts.html", alerts=all_alerts)


@admin_bp.route("/admin/users/<int:user_id>/role", methods=["POST"])
@admin_required
def toggle_role(user_id):
    if str(user_id) == str(current_user.id):
        return jsonify({"error": "Você não pode alterar seu próprio privilégio."}), 400
        
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404
        
    new_role = "user" if user.is_admin else "admin"
    User.update_role(user_id, new_role)
    
    return jsonify({"success": True, "new_role": new_role})


@admin_bp.route("/admin/users/<int:user_id>/notify", methods=["POST"])
@admin_required
def notify_user(user_id):
    """Envia uma notificação manual a um usuário."""
    from models.notification import Notification
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()

    if not title:
        return jsonify({"error": "Título é obrigatório."}), 400

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404

    from app import get_db
    db = get_db()
    db.execute(
        "INSERT INTO notifications (user_id, type, title, body) VALUES (?, ?, ?, ?)",
        (user_id, "admin_message", title, body or None),
    )
    db.commit()
    return jsonify({"success": True})


@admin_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    """Exclui permanentemente um usuário e todos os seus dados."""
    if str(user_id) == str(current_user.id):
        return jsonify({"error": "Você não pode excluir sua própria conta."}), 400

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404

    from app import get_db
    db = get_db()
    # Excluir dados relacionados antes de excluir o usuário
    db.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM bets WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM scores WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM pool_members WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM chat_group_members WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return jsonify({"success": True})
