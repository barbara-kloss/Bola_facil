"""
Socket Controller — Gerencia eventos WebSocket de chat em tempo real.
Usa Flask-SocketIO com 'rooms' mapeadas para grupos de chat.
"""

from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

from models.chat import ChatGroupMember, ChatMessage


def register_socket_handlers(socketio):
    """Registra todos os event handlers do SocketIO no app."""

    def _require_auth():
        """Verifica se o usuário está autenticado; emite erro e retorna False se não."""
        if not current_user.is_authenticated:
            emit("error", {"message": "Não autenticado."})
            return False
        return True

    @socketio.on("connect")
    def on_connect():
        if not current_user.is_authenticated:
            return False  # rejeita conexão
        emit("connected", {"user_id": int(current_user.id), "name": current_user.name})

    @socketio.on("disconnect")
    def on_disconnect():
        pass  # cleanup é automático pelo Flask-SocketIO

    @socketio.on("join_group")
    def on_join_group(data):
        if not _require_auth():
            return

        group_id = data.get("group_id")
        if not group_id:
            return emit("error", {"message": "group_id obrigatório."})

        # Validar que o usuário é membro do grupo
        if not ChatGroupMember.exists(group_id, current_user.id):
            return emit("error", {"message": "Acesso negado ao grupo."})

        room = f"group_{group_id}"
        join_room(room)
        emit("joined", {"group_id": group_id, "room": room})

    @socketio.on("leave_group")
    def on_leave_group(data):
        if not _require_auth():
            return

        group_id = data.get("group_id")
        if group_id:
            leave_room(f"group_{group_id}")

    @socketio.on("send_message")
    def on_send_message(data):
        if not _require_auth():
            return

        group_id = data.get("group_id")
        text = (data.get("text") or "").strip()

        if not group_id or not text:
            return emit("error", {"message": "group_id e text são obrigatórios."})

        if len(text) > 2000:
            return emit("error", {"message": "Mensagem muito longa (máximo 2000 caracteres)."})

        # Segurança: confirmar que o sender é membro
        if not ChatGroupMember.exists(group_id, current_user.id):
            return emit("error", {"message": "Acesso negado ao grupo."})

        # Persistir no banco
        msg_id = ChatMessage.send_to_group(group_id, int(current_user.id), text)

        # Broadcast para todos na sala (inclusive o remetente)
        room = f"group_{group_id}"
        emit(
            "new_message",
            {
                "id": msg_id,
                "group_id": group_id,
                "sender_id": int(current_user.id),
                "sender_name": current_user.name,
                "text": text,
            },
            to=room,
        )
