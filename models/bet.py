def _db():
    from app import get_db

    return get_db()


class Bet:
    @staticmethod
    def create(user_id, game_id, predicted_home_score, predicted_away_score):
        cursor = _db().execute(
            """
            INSERT INTO bets (user_id, game_id, predicted_home_score, predicted_away_score)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, game_id) DO UPDATE SET
                predicted_home_score = excluded.predicted_home_score,
                predicted_away_score = excluded.predicted_away_score,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, game_id, predicted_home_score, predicted_away_score),
        )
        _db().commit()
        if cursor.lastrowid:
            return Bet.get_by_id(cursor.lastrowid)
        return Bet.get_by_user_and_game(user_id, game_id)

    @staticmethod
    def get_by_id(bet_id):
        return _db().execute("SELECT * FROM bets WHERE id = ?", (bet_id,)).fetchone()

    @staticmethod
    def get_by_user_and_game(user_id, game_id):
        return _db().execute(
            "SELECT * FROM bets WHERE user_id = ? AND game_id = ?",
            (user_id, game_id),
        ).fetchone()

    @staticmethod
    def list(game_id=None, user_id=None):
        query = "SELECT * FROM bets"
        values = []
        clauses = []
        if game_id:
            clauses.append("game_id = ?")
            values.append(game_id)
        if user_id:
            clauses.append("user_id = ?")
            values.append(user_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC"
        return _db().execute(query, values).fetchall()

    @staticmethod
    def update_points(bet_id, points_earned):
        _db().execute(
            "UPDATE bets SET points_earned = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (points_earned, bet_id),
        )
        _db().commit()

    @staticmethod
    def delete(bet_id):
        _db().execute("DELETE FROM bets WHERE id = ?", (bet_id,))
        _db().commit()
