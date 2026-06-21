def _db():
    from app import get_db

    return get_db()


class Score:
    @staticmethod
    def update(pool_id, user_id, total_points):
        _db().execute(
            """
            INSERT INTO scores (pool_id, user_id, total_points, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(pool_id, user_id) DO UPDATE SET
                total_points = excluded.total_points,
                updated_at = CURRENT_TIMESTAMP
            """,
            (pool_id, user_id, total_points),
        )
        _db().commit()

    @staticmethod
    def get_ranking(pool_id):
        return _db().execute(
            """
            SELECT users.id AS user_id,
                   users.name,
                   users.email,
                   COALESCE(scores.total_points, 0) AS total_points,
                   COUNT(bets.id) AS bets_count
              FROM pool_members
              JOIN users ON users.id = pool_members.user_id
              LEFT JOIN scores ON scores.user_id = users.id AND scores.pool_id = pool_members.pool_id
              LEFT JOIN bets ON bets.user_id = users.id
              LEFT JOIN games ON games.id = bets.game_id AND games.pool_id = pool_members.pool_id
             WHERE pool_members.pool_id = ?
             GROUP BY users.id, users.name, users.email, scores.total_points
             ORDER BY total_points DESC, users.name ASC
            """,
            (pool_id,),
        ).fetchall()
