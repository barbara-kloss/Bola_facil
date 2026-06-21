from flask import Blueprint, jsonify, request
from flask_login import login_required

from services.whatsapp_service import WhatsAppService


whatsapp_bp = Blueprint("whatsapp", __name__, url_prefix="/whatsapp")


def _db():
    from app import get_db

    return get_db()


@whatsapp_bp.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    return jsonify({"received": True, "payload": payload})


@whatsapp_bp.route("/notify", methods=["POST"])
@login_required
def notify():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "Mensagem do BolãoFácil.")
    users = _db().execute("SELECT whatsapp_phone FROM users WHERE whatsapp_phone IS NOT NULL").fetchall()
    results = [WhatsAppService.send_message(user["whatsapp_phone"], message) for user in users]
    return jsonify({"sent": len(results), "results": results})
