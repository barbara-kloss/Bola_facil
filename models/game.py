def _db():
    from app import get_db

    return get_db()


class Game:
    @staticmethod
    def create(pool_id, home_team, away_team, match_datetime, status="scheduled", **api_fields):
        cursor = _db().execute(
            """
            INSERT INTO games (
                pool_id, external_match_id, competition_code, competition_name, matchday,
                home_team, away_team, home_crest, away_crest, match_datetime,
                home_score, away_score, api_status, status, last_synced_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pool_id,
                api_fields.get("external_match_id"),
                api_fields.get("competition_code"),
                api_fields.get("competition_name"),
                api_fields.get("matchday"),
                home_team,
                away_team,
                api_fields.get("home_crest"),
                api_fields.get("away_crest"),
                match_datetime,
                api_fields.get("home_score"),
                api_fields.get("away_score"),
                api_fields.get("api_status"),
                status,
                api_fields.get("last_synced_at"),
            ),
        )
        _db().commit()
        return Game.get_by_id(cursor.lastrowid)

    @staticmethod
    def get_by_id(game_id):
        return _db().execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()

    @staticmethod
    def list(pool_id=None):
        if pool_id:
            return _db().execute(
                "SELECT * FROM games WHERE pool_id = ? ORDER BY match_datetime",
                (pool_id,),
            ).fetchall()
        return _db().execute("SELECT * FROM games ORDER BY match_datetime").fetchall()

    @staticmethod
    def update(game_id, home_team, away_team, match_datetime, status):
        _db().execute(
            """
            UPDATE games
               SET home_team = ?, away_team = ?, match_datetime = ?, status = ?, updated_at = CURRENT_TIMESTAMP
             WHERE id = ?
            """,
            (home_team, away_team, match_datetime, status, game_id),
        )
        _db().commit()
        return Game.get_by_id(game_id)

    @staticmethod
    def record_result(game_id, home_score, away_score, status="finished"):
        _db().execute(
            """
            UPDATE games
               SET home_score = ?, away_score = ?, status = ?, updated_at = CURRENT_TIMESTAMP
             WHERE id = ?
            """,
            (home_score, away_score, status, game_id),
        )
        _db().commit()
        return Game.get_by_id(game_id)

    @staticmethod
    def get_by_external_match_id(external_match_id):
        return _db().execute(
            "SELECT * FROM games WHERE external_match_id = ?",
            (external_match_id,),
        ).fetchone()

    @staticmethod
    def upsert_external(pool_id, match_data):
        cursor = _db().execute(
            """
            INSERT INTO games (
                pool_id, external_match_id, competition_code, competition_name, matchday,
                home_team, away_team, home_crest, away_crest, match_datetime,
                home_score, away_score, api_status, status, last_synced_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(external_match_id) DO UPDATE SET
                pool_id = excluded.pool_id,
                competition_code = excluded.competition_code,
                competition_name = excluded.competition_name,
                matchday = excluded.matchday,
                home_team = excluded.home_team,
                away_team = excluded.away_team,
                home_crest = excluded.home_crest,
                away_crest = excluded.away_crest,
                match_datetime = excluded.match_datetime,
                home_score = excluded.home_score,
                away_score = excluded.away_score,
                api_status = excluded.api_status,
                status = excluded.status,
                last_synced_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                pool_id,
                match_data["external_match_id"],
                match_data.get("competition_code"),
                match_data.get("competition_name"),
                match_data.get("matchday"),
                match_data["home_team"],
                match_data["away_team"],
                match_data.get("home_crest"),
                match_data.get("away_crest"),
                match_data["match_datetime"],
                match_data.get("home_score"),
                match_data.get("away_score"),
                match_data.get("api_status"),
                match_data["status"],
            ),
        )
        _db().commit()
        if cursor.lastrowid:
            return Game.get_by_id(cursor.lastrowid)
        return Game.get_by_external_match_id(match_data["external_match_id"])
