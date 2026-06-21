from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from utils.decorators import admin_required
from models.user import User

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/dashboard")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")

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
