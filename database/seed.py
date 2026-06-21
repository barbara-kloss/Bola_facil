import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash


ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "database" / "bolao_facil.db"
SCHEMA_PATH = ROOT / "database" / "schema.sql"


def seed():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

        users = [
            ("Ana Souza", "ana@bolao.test", "11999990001"),
            ("Bruno Lima", "bruno@bolao.test", "11999990002"),
            ("Carla Nunes", "carla@bolao.test", "11999990003"),
            ("Diego Rocha", "diego@bolao.test", "11999990004"),
            ("Elisa Martins", "elisa@bolao.test", "11999990005"),
        ]
        user_ids = []
        for name, email, phone in users:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO users (name, email, whatsapp_phone, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, phone, generate_password_hash("senha123")),
            )
            row = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            user_ids.append(row["id"] if row else cursor.lastrowid)

        connection.execute(
            "INSERT OR IGNORE INTO pools (id, name, description, created_by) VALUES (1, ?, ?, ?)",
            ("Bolão Principal", "Dados de exemplo para testes manuais", user_ids[0]),
        )
        for index, user_id in enumerate(user_ids):
            role = "admin" if index == 0 else "member"
            connection.execute(
                "INSERT OR IGNORE INTO pool_members (pool_id, user_id, role) VALUES (1, ?, ?)",
                (user_id, role),
            )

        games = [
            ("Brasil", "Argentina", "2026-07-01T18:00", 2, 1, "finished", 1),
            ("Flamengo", "Palmeiras", "2026-07-02T16:00", None, None, "scheduled", 2),
            ("São Paulo", "Santos", "2026-07-03T20:00", None, None, "scheduled", 2),
            ("Grêmio", "Internacional", "2026-07-04T19:00", None, None, "scheduled", 2),
            ("Cruzeiro", "Atlético Mineiro", "2026-07-05T17:00", None, None, "scheduled", 2),
        ]
        for home, away, when, home_score, away_score, status, matchday in games:
            connection.execute(
                """
                INSERT OR IGNORE INTO games (
                    id, pool_id, competition_code, competition_name, matchday,
                    home_team, away_team, match_datetime, home_score, away_score, status
                )
                VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM games), 1, 'BSA', 'Brasileirão Série A', ?, ?, ?, ?, ?, ?, ?)
                """,
                (matchday, home, away, when, home_score, away_score, status),
            )

        first_game = connection.execute("SELECT id FROM games ORDER BY id LIMIT 1").fetchone()["id"]
        predictions = [(2, 1), (1, 0), (3, 1), (0, 0), (2, 0)]
        for user_id, prediction in zip(user_ids, predictions):
            connection.execute(
                """
                INSERT OR IGNORE INTO bets (user_id, game_id, predicted_home_score, predicted_away_score)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, first_game, prediction[0], prediction[1]),
            )

        connection.commit()


if __name__ == "__main__":
    seed()
    print(f"Banco populado em {DATABASE_PATH}")
