def _db():
    from app import get_db

    return get_db()


class Bet:
    @staticmethod
    def create(user_id, game_id, predicted_home_score, predicted_away_score):
        row = _db().execute(
            """
            INSERT INTO bets (user_id, game_id, predicted_home_score, predicted_away_score)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, game_id) DO UPDATE SET
                predicted_home_score = EXCLUDED.predicted_home_score,
                predicted_away_score = EXCLUDED.predicted_away_score,
                updated_at = NOW()
            RETURNING id
            """,
            (user_id, game_id, predicted_home_score, predicted_away_score),
        ).fetchone()
        _db().commit()
        if row:
            return Bet.get_by_id(row["id"])
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
        return _db().execute(query, tuple(values)).fetchall()

    @staticmethod
    def update_points(bet_id, points_earned):
        _db().execute(
            "UPDATE bets SET points_earned = ?, updated_at = NOW() WHERE id = ?",
            (points_earned, bet_id),
        )
        _db().commit()

    @staticmethod
    def delete(bet_id):
        _db().execute("DELETE FROM bets WHERE id = ?", (bet_id,))
        _db().commit()
