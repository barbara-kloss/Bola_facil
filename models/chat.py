def _db():
    from app import get_db
    return get_db()

class ChatGroup:
    @staticmethod
    def create(name, created_by):
        cursor = _db().execute(
            "INSERT INTO chat_groups (name, created_by) VALUES (?, ?)",
            (name, created_by)
        )
        group_id = cursor.lastrowid
        ChatGroupMember.add(group_id, created_by)
        _db().commit()
        return ChatGroup.get_by_id(group_id)

    @staticmethod
    def get_by_id(group_id):
        return _db().execute("SELECT * FROM chat_groups WHERE id = ?", (group_id,)).fetchone()

    @staticmethod
    def list_for_user(user_id):
        return _db().execute(
            """
            SELECT cg.* FROM chat_groups cg
            JOIN chat_group_members cgm ON cgm.group_id = cg.id
            WHERE cgm.user_id = ?
            ORDER BY cg.created_at DESC
            """,
            (user_id,)
        ).fetchall()


class ChatGroupMember:
    @staticmethod
    def add(group_id, user_id):
        _db().execute(
            "INSERT OR IGNORE INTO chat_group_members (group_id, user_id) VALUES (?, ?)",
            (group_id, user_id)
        )
        _db().commit()

    @staticmethod
    def exists(group_id, user_id):
        row = _db().execute(
            "SELECT 1 FROM chat_group_members WHERE group_id = ? AND user_id = ?",
            (group_id, user_id)
        ).fetchone()
        return row is not None


class ChatMessage:
    @staticmethod
    def send_to_group(group_id, sender_id, text, is_bot=0):
        cursor = _db().execute(
            "INSERT INTO chat_messages (group_id, sender_id, text, is_bot) VALUES (?, ?, ?, ?)",
            (group_id, sender_id, text, is_bot)
        )
        _db().commit()
        return cursor.lastrowid

    @staticmethod
    def send_private(sender_id, recipient_id, text, is_bot=0):
        cursor = _db().execute(
            "INSERT INTO chat_messages (sender_id, recipient_id, text, is_bot) VALUES (?, ?, ?, ?)",
            (sender_id, recipient_id, text, is_bot)
        )
        _db().commit()
        return cursor.lastrowid

    @staticmethod
    def list_for_group(group_id):
        return _db().execute(
            """
            SELECT cm.*, u.name as sender_name 
            FROM chat_messages cm
            LEFT JOIN users u ON u.id = cm.sender_id
            WHERE cm.group_id = ?
            ORDER BY cm.created_at ASC
            """,
            (group_id,)
        ).fetchall()

    @staticmethod
    def list_private(user1_id, user2_id):
        return _db().execute(
            """
            SELECT cm.*, u.name as sender_name
            FROM chat_messages cm
            LEFT JOIN users u ON u.id = cm.sender_id
            WHERE cm.group_id IS NULL AND (
                (cm.sender_id = ? AND cm.recipient_id = ?) OR
                (cm.sender_id = ? AND cm.recipient_id = ?)
            )
            ORDER BY cm.created_at ASC
            """,
            (user1_id, user2_id, user2_id, user1_id)
        ).fetchall()


class ChatGroupInvite:
    @staticmethod
    def add(group_id, email, invited_by):
        _db().execute(
            "INSERT OR IGNORE INTO chat_group_invites (group_id, email, invited_by) VALUES (?, ?, ?)",
            (group_id, email.lower(), invited_by)
        )
        _db().commit()

    @staticmethod
    def get_by_email(email):
        return _db().execute(
            "SELECT * FROM chat_group_invites WHERE email = ?",
            (email.lower(),)
        ).fetchall()

    @staticmethod
    def accept_all_for_user(user_id, email):
        invites = ChatGroupInvite.get_by_email(email)
        for inv in invites:
            ChatGroupMember.add(inv["group_id"], user_id)
        if invites:
            _db().execute("DELETE FROM chat_group_invites WHERE email = ?", (email.lower(),))
            _db().commit()
