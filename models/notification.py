import json

def _db():
    from app import get_db
    return get_db()

class Notification:
    @staticmethod
    def create(user_id, type, title, body=None, extra_data=None):
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
