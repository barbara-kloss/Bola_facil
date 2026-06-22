from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


def _db():
    from app import get_db

    return get_db()


class User(UserMixin):
    def __init__(self, id, name, email, whatsapp_phone=None, password_hash=None, created_at=None, role="user", notifications_enabled=1, notification_prefs=None, reset_token=None, reset_token_expires_at=None):
        self.id = str(id)
        self.name = name
        self.email = email
        self.whatsapp_phone = whatsapp_phone
        self.password_hash = password_hash
        self.created_at = created_at
        self.role = role
        self.notifications_enabled = notifications_enabled
        self.reset_token = reset_token
        self.reset_token_expires_at = reset_token_expires_at
        import json
        if isinstance(notification_prefs, str):
            try:
                self.notification_prefs = json.loads(notification_prefs)
            except:
                self.notification_prefs = {}
        else:
            self.notification_prefs = notification_prefs or {}

    @property
    def is_admin(self):
        return self.role == "admin"

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        
        # Use get() for role and notifications_enabled in case they are missing from older rows before migration
        return cls(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            whatsapp_phone=row["whatsapp_phone"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            role=row["role"] if "role" in row.keys() else "user",
            notifications_enabled=row["notifications_enabled"] if "notifications_enabled" in row.keys() else 1,
            notification_prefs=row["notification_prefs"] if "notification_prefs" in row.keys() else "{}",
            reset_token=row["reset_token"] if "reset_token" in row.keys() else None,
            reset_token_expires_at=row["reset_token_expires_at"] if "reset_token_expires_at" in row.keys() else None,
        )

    @staticmethod
    def create(name, email, password, whatsapp_phone=None):
        count = _db().execute("SELECT COUNT(*) FROM users").fetchone()[0]
        role = "admin" if count == 0 else "user"
        
        password_hash = generate_password_hash(password)
        cursor = _db().execute(
            """
            INSERT INTO users (name, email, whatsapp_phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email.lower(), whatsapp_phone, password_hash, role),
        )
        _db().commit()
        return User.get_by_id(cursor.lastrowid)

    @staticmethod
    def set_notification_preference(user_id, enabled):
        _db().execute(
            "UPDATE users SET notifications_enabled = ? WHERE id = ?",
            (1 if enabled else 0, user_id),
        )
        _db().commit()

    @staticmethod
    def get_by_id(user_id):
        row = _db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return User.from_row(row)

    @staticmethod
    def get_by_email(email):
        row = _db().execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
        return User.from_row(row)

    @staticmethod
    def list():
        rows = _db().execute("SELECT * FROM users ORDER BY name").fetchall()
        return [User.from_row(row) for row in rows]

    @staticmethod
    def update(user_id, name, email, whatsapp_phone=None):
        _db().execute(
            """
            UPDATE users
               SET name = ?, email = ?, whatsapp_phone = ?
             WHERE id = ?
            """,
            (name, email.lower(), whatsapp_phone, user_id),
        )
        _db().commit()
    @staticmethod
    def update_role(user_id, role):
        _db().execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (role, user_id),
        )
        _db().commit()
        return User.get_by_id(user_id)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def generate_reset_token(user_id):
        import secrets
        from datetime import datetime, timedelta, timezone
        
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        _db().execute(
            "UPDATE users SET reset_token = ?, reset_token_expires_at = ? WHERE id = ?",
            (token, expires_at, user_id)
        )
        _db().commit()
        return token

    @staticmethod
    def get_by_reset_token(token):
        row = _db().execute(
            "SELECT * FROM users WHERE reset_token = ? AND reset_token_expires_at > CURRENT_TIMESTAMP", 
            (token,)
        ).fetchone()
        return User.from_row(row)

    @staticmethod
    def reset_password(user_id, new_password):
        password_hash = generate_password_hash(new_password)
        _db().execute(
            "UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires_at = NULL WHERE id = ?",
            (password_hash, user_id)
        )
        _db().commit()


class Pool:
    @staticmethod
    def create(name, created_by, description=None):
        cursor = _db().execute(
            "INSERT INTO pools (name, description, created_by) VALUES (?, ?, ?)",
            (name, description, created_by),
        )
        pool_id = cursor.lastrowid
        _db().execute(
            "INSERT INTO pool_members (pool_id, user_id, role) VALUES (?, ?, 'admin')",
            (pool_id, created_by),
        )
        _db().commit()
        return Pool.get_by_id(pool_id)

    @staticmethod
    def get_by_id(pool_id):
        return _db().execute("SELECT * FROM pools WHERE id = ?", (pool_id,)).fetchone()

    @staticmethod
    def get_default():
        return _db().execute("SELECT * FROM pools ORDER BY id LIMIT 1").fetchone()

    @staticmethod
    def list_for_user(user_id):
        return _db().execute(
            """
            SELECT pools.*
              FROM pools
              JOIN pool_members ON pool_members.pool_id = pools.id
             WHERE pool_members.user_id = ?
             ORDER BY pools.created_at DESC
            """,
            (user_id,),
        ).fetchall()

    @staticmethod
    def is_admin(pool_id, user_id):
        row = _db().execute(
            "SELECT 1 FROM pools WHERE id = ? AND created_by = ?",
            (pool_id, user_id),
        ).fetchone()
        return row is not None


class PoolMember:
    @staticmethod
    def add(pool_id, user_id, role="member"):
        _db().execute(
            """
            INSERT OR IGNORE INTO pool_members (pool_id, user_id, role)
            VALUES (?, ?, ?)
            """,
            (pool_id, user_id, role),
        )
        _db().commit()

    @staticmethod
    def exists(pool_id, user_id):
        row = _db().execute(
            "SELECT 1 FROM pool_members WHERE pool_id = ? AND user_id = ?",
            (pool_id, user_id),
        ).fetchone()
        return row is not None
