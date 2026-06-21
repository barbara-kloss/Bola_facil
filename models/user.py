from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


def _db():
    from app import get_db

    return get_db()


class User(UserMixin):
    def __init__(self, id, name, email, whatsapp_phone=None, password_hash=None, created_at=None):
        self.id = str(id)
        self.name = name
        self.email = email
        self.whatsapp_phone = whatsapp_phone
        self.password_hash = password_hash
        self.created_at = created_at

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            whatsapp_phone=row["whatsapp_phone"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
        )

    @staticmethod
    def create(name, email, password, whatsapp_phone=None):
        password_hash = generate_password_hash(password)
        cursor = _db().execute(
            """
            INSERT INTO users (name, email, whatsapp_phone, password_hash)
            VALUES (?, ?, ?, ?)
            """,
            (name, email.lower(), whatsapp_phone, password_hash),
        )
        _db().commit()
        return User.get_by_id(cursor.lastrowid)

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
        return User.get_by_id(user_id)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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
