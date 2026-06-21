from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.notification import Notification

notification_bp = Blueprint("notification", __name__)

@notification_bp.route("/notificacoes", methods=["GET"])
@login_required
def inbox():
    notifications = Notification.list_for_user(current_user.id)
    return render_template("notifications/inbox.html", notifications=notifications)

@notification_bp.route("/notificacoes/unread-count", methods=["GET"])
@login_required
def unread_count():
    count = Notification.count_unread(current_user.id)
    return jsonify({"count": count})

@notification_bp.route("/notificacoes/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id):
    Notification.mark_read(notification_id, current_user.id)
    return jsonify({"success": True})

@notification_bp.route("/notificacoes/read-all", methods=["POST"])
@login_required
def mark_all_read():
    Notification.mark_all_read(current_user.id)
    return jsonify({"success": True})
