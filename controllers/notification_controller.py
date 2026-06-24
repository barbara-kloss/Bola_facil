from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.notification import Notification

notification_bp = Blueprint("notification", __name__)

import json

@notification_bp.route("/notificacoes", methods=["GET"])
@login_required
def inbox():
    raw_notifications = Notification.list_for_user(current_user.id)
    notifications = []
    for n in raw_notifications:
        n_dict = dict(n)
        if n_dict.get("extra_data"):
            try:
                n_dict["parsed_extra"] = json.loads(n_dict["extra_data"])
            except Exception:
                n_dict["parsed_extra"] = {}
        else:
            n_dict["parsed_extra"] = {}
        notifications.append(n_dict)
    
    # Marcar automaticamente como lidas ao abrir a página
    Notification.mark_all_read(current_user.id)
    return render_template("notifications/inbox.html", notifications=notifications)

@notification_bp.route("/notificacoes/unread-count", methods=["GET"])
@login_required
def unread_count():
    count = Notification.count_unread(current_user.id)
    return jsonify({"count": count})

@notification_bp.route("/notificacoes/recentes", methods=["GET"])
@login_required
def recent():
    """Retorna as últimas 5 notificações para o dropdown."""
    all_notifs = Notification.list_for_user(current_user.id)
    recent_notifs = all_notifs[:5]
    
    out = []
    for n in recent_notifs:
        n_dict = {
            "id": n["id"],
            "title": n["title"],
            "body": n["body"] or "",
            "read": bool(n["read"]),
            "type": n["type"],
            "created_at": n["created_at"],
            "group_id": None
        }
        if n["type"] == "group_invite" and n["extra_data"]:
            try:
                extra = json.loads(n["extra_data"])
                n_dict["group_id"] = extra.get("group_id")
            except Exception:
                pass
        out.append(n_dict)
        
    Notification.mark_all_read(current_user.id)
    return jsonify({"notifications": out})

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
