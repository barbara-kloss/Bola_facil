import logging
import time
import requests
import re
from flask import current_app

from models.game import Game
from models.user import Pool


logger = logging.getLogger(__name__)
_request_timestamps = []


def _db():
    from app import get_db

    return get_db()


class FootballService:
    @staticmethod
    def get_next_matches():
        return FootballService._get(
            "/fixtures",
            params={
                "league": current_app.config["FOOTBALL_COMPETITION_CODE"],
                "season": current_app.config["API_SPORTS_SEASON"]
            },
        )

    @staticmethod
    def get_match_result(match_id):
        return FootballService._get(
            "/fixtures",
            params={"id": match_id}
        )

    @staticmethod
    def get_standings():
        return FootballService._get(
            "/standings",
            params={
                "league": current_app.config["FOOTBALL_COMPETITION_CODE"],
                "season": current_app.config["API_SPORTS_SEASON"]
            }
        )

    @staticmethod
    def get_match_lineups(fixture_id):
        return FootballService._get(
            "/fixtures/lineups",
            params={"fixture": fixture_id}
        )

    @staticmethod
    def sync_matches_to_db(pool_id=None):
        pool = Pool.get_by_id(pool_id) if pool_id else Pool.get_default()
        if pool is None:
            raise RuntimeError("Crie um bolão antes de sincronizar jogos.")

        payload = FootballService.get_next_matches()
        matches = payload.get("response", [])
        synced = []
        for match in matches:
            synced.append(Game.upsert_external(pool["id"], FootballService._normalize_match(match)))
        return synced

    @staticmethod
    def sync_result_to_db(game):
        external_match_id = game["external_match_id"] if "external_match_id" in game.keys() else None
        if not external_match_id:
            return game

        payload = FootballService.get_match_result(external_match_id)
        response_list = payload.get("response", [])
        if not response_list:
            return game
        match = response_list[0]
        normalized = FootballService._normalize_match(match)
        return Game.upsert_external(game["pool_id"], normalized)

    @staticmethod
    def _get(path, params=None):
        FootballService._throttle()
        api_url = current_app.config["API_SPORTS_URL"].rstrip("/")
        api_key = current_app.config["API_SPORTS_KEY"]
        if not api_key:
            raise RuntimeError("API_SPORTS_KEY não configurada.")

        response = requests.get(
            f"{api_url}{path}",
            params=params,
            headers={"x-apisports-key": api_key},
            timeout=12,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _throttle():
        limit = current_app.config.get("FOOTBALL_RATE_LIMIT_PER_MINUTE", 10)
        now = time.monotonic()
        while _request_timestamps and now - _request_timestamps[0] >= 60:
            _request_timestamps.pop(0)
        if len(_request_timestamps) >= limit:
            sleep_for = 60 - (now - _request_timestamps[0])
            logger.info("Football API rate limit atingido. Aguardando %.1fs.", sleep_for)
            time.sleep(max(sleep_for, 0))
        _request_timestamps.append(time.monotonic())

    @staticmethod
    def _normalize_match(match):
        fixture = match.get("fixture", {})
        league = match.get("league", {})
        teams = match.get("teams", {})
        goals = match.get("goals", {})

        home_team = teams.get("home", {})
        away_team = teams.get("away", {})

        round_str = league.get("round", "")
        matchday = None
        digits = re.findall(r'\d+', round_str)
        if digits:
            matchday = int(digits[0])

        api_status = fixture.get("status", {}).get("short", "NS")

        return {
            "external_match_id": fixture.get("id"),
            "competition_code": str(league.get("id")) or current_app.config["FOOTBALL_COMPETITION_CODE"],
            "competition_name": league.get("name"),
            "matchday": matchday,
            "home_team": home_team.get("name") or "A definir",
            "away_team": away_team.get("name") or "A definir",
            "home_crest": home_team.get("logo"),
            "away_crest": away_team.get("logo"),
            "match_datetime": fixture.get("date"),
            "home_score": goals.get("home"),
            "away_score": goals.get("away"),
            "api_status": api_status,
            "status": FootballService._map_status(api_status),
        }

    @staticmethod
    def _map_status(api_status):
        status = (api_status or "").upper()
        if status in {"FT", "AET", "PEN"}:
            return "finished"
        if status in {"1H", "2H", "HT", "ET", "BT", "P", "LIVE"}:
            return "live"
        if status in {"PST", "CANC", "ABD", "SUSP", "INT"}:
            return "cancelled"
        return "scheduled"
