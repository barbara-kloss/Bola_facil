import json

def _db():
    from app import get_db
    return get_db()

# Mapeamento de tipos de notificação para as chaves de preferência do usuário
_TYPE_TO_PREF_KEY = {
    "new_game": "new_game",
    "result": "results",
    "reminder": "reminders",
    "chat_message": "chat",
    "group_invite": "chat",
}

class Notification:
    @staticmethod
    def _is_allowed_for_user(user_id, notification_type):
        """Verifica se o usuário aceita esse tipo de notificação com base em suas preferências."""
        row = _db().execute(
            "SELECT notifications_enabled, notification_prefs FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        if not row:
            return False

        # Se notificações gerais estiverem desativadas, bloquear tudo
        if not row["notifications_enabled"]:
            return False

        # Verificar preferências granulares
        prefs_raw = row["notification_prefs"] or "{}"
        try:
            prefs = json.loads(prefs_raw)
        except (ValueError, TypeError):
            prefs = {}

        pref_key = _TYPE_TO_PREF_KEY.get(notification_type)
        if pref_key is None:
            # Tipo desconhecido — permite por padrão
            return True

        # Preferência ausente → True por padrão (opt-out)
        return prefs.get(pref_key, True)

    @staticmethod
    def create(user_id, type, title, body=None, extra_data=None):
        # Verificar preferências do destinatário antes de gravar
        if not Notification._is_allowed_for_user(user_id, type):
            return None

        data_str = json.dumps(extra_data) if extra_data else None
        cursor = _db().execute(
            "INSERT INTO notifications (user_id, type, title, body, extra_data) VALUES (?, ?, ?, ?, ?)",
            (user_id, type, title, body, data_str)
        )
        _db().commit()
        return cursor.lastrowid

    @staticmethod
    def list_for_user(user_id, unread_only=False):
        query = "SELECT * FROM notifications WHERE user_id = ?"
        params = [user_id]
        if unread_only:
            query += " AND read = 0"
        query += " ORDER BY created_at DESC"
        
        return _db().execute(query, params).fetchall()

    @staticmethod
    def list_all(limit=100):
        return _db().execute(
            """
            SELECT n.*, u.name as user_name 
            FROM notifications n 
            LEFT JOIN users u ON u.id = n.user_id 
            ORDER BY n.created_at DESC 
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    @staticmethod
    def mark_read(notification_id, user_id):
        _db().execute(
            "UPDATE notifications SET read = 1 WHERE id = ? AND user_id = ?",
            (notification_id, user_id)
        )
        _db().commit()

    @staticmethod
    def mark_all_read(user_id):
        _db().execute(
            "UPDATE notifications SET read = 1 WHERE user_id = ? AND read = 0",
            (user_id,)
        )
        _db().commit()

    @staticmethod
    def count_unread(user_id):
        row = _db().execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = 0",
            (user_id,)
        ).fetchone()
        return row[0] if row else 0
