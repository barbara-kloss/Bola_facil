def _db():
    from app import get_db

    return get_db()


class Game:
    @staticmethod
    def create(pool_id, home_team, away_team, match_datetime, status="scheduled", **api_fields):
        if not home_team or not str(home_team).strip():
            raise ValueError("O nome do time mandante não pode estar vazio")
        if not away_team or not str(away_team).strip():
            raise ValueError("O nome do time visitante não pode estar vazio")
            
        from datetime import datetime
        try:
            if isinstance(match_datetime, str):
                match_time = datetime.fromisoformat(match_datetime.replace('Z', '+00:00'))
            else:
                match_time = match_datetime
            now = datetime.now(match_time.tzinfo) if match_time.tzinfo else datetime.now()
            if match_time <= now:
                raise ValueError("A data e hora do jogo devem ser no futuro")
        except ValueError as e:
            if "futuro" in str(e):
                raise
            raise ValueError("Data e hora inválidas")

        existing = _db().execute(
            "SELECT id FROM games WHERE pool_id = ? AND home_team = ? AND away_team = ? AND match_datetime = ?",
            (pool_id, home_team, away_team, match_datetime)
        ).fetchone()
        if existing:
            raise ValueError("Este jogo já está cadastrado para este bolão nesta mesma data e horário")

        row = _db().execute(
            """
            INSERT INTO games (
                pool_id, external_match_id, competition_code, competition_name, matchday,
                home_team, away_team, home_crest, away_crest, match_datetime,
                home_score, away_score, api_status, status, last_synced_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
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
        ).fetchone()
        _db().commit()
        return Game.get_by_id(row["id"])

    @staticmethod
    def get_by_id(game_id):
        return _db().execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()

    @staticmethod
    def list(pool_id=None):
        order_clause = """
            ORDER BY 
                CASE 
                    WHEN status = 'live' THEN 0 
                    WHEN status = 'scheduled' THEN 1 
                    ELSE 2 
                END, 
                match_datetime ASC
        """
        if pool_id:
            return _db().execute(
                f"SELECT * FROM games WHERE pool_id = ? {order_clause}",
                (pool_id,),
            ).fetchall()
        return _db().execute(f"SELECT * FROM games {order_clause}").fetchall()

    @staticmethod
    def update(game_id, home_team, away_team, match_datetime, status):
        _db().execute(
            """
            UPDATE games
               SET home_team = ?, away_team = ?, match_datetime = ?, status = ?, updated_at = NOW()
             WHERE id = ?
            """,
            (home_team, away_team, match_datetime, status, game_id),
        )
        _db().commit()
        return Game.get_by_id(game_id)

    @staticmethod
    def record_result(game_id, home_score, away_score, status="finished"):
        if int(home_score) < 0 or int(away_score) < 0:
            raise ValueError("O placar não pode conter valores negativos")
            
        _db().execute(
            """
            UPDATE games
               SET home_score = ?, away_score = ?, status = ?, updated_at = NOW()
             WHERE id = ?
            """,
            (int(home_score), int(away_score), status, game_id),
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
        row = _db().execute(
            """
            INSERT INTO games (
                pool_id, external_match_id, competition_code, competition_name, matchday,
                home_team, away_team, home_crest, away_crest, match_datetime,
                home_score, away_score, api_status, status, last_synced_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
            ON CONFLICT(external_match_id) DO UPDATE SET
                competition_code = EXCLUDED.competition_code,
                competition_name = EXCLUDED.competition_name,
                matchday = EXCLUDED.matchday,
                home_team = EXCLUDED.home_team,
                away_team = EXCLUDED.away_team,
                home_crest = EXCLUDED.home_crest,
                away_crest = EXCLUDED.away_crest,
                match_datetime = EXCLUDED.match_datetime,
                home_score = EXCLUDED.home_score,
                away_score = EXCLUDED.away_score,
                api_status = EXCLUDED.api_status,
                status = EXCLUDED.status,
                last_synced_at = NOW(),
                updated_at = NOW()
            RETURNING id
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
        ).fetchone()
        _db().commit()
        if row:
            return Game.get_by_id(row["id"])
        return Game.get_by_external_match_id(match_data["external_match_id"])
