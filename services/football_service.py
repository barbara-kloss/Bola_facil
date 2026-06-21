import logging
import time

import requests
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
            f"/competitions/{current_app.config['FOOTBALL_COMPETITION_CODE']}/matches",
            params={"status": "SCHEDULED"},
        )

    @staticmethod
    def get_match_result(match_id):
        return FootballService._get(f"/matches/{match_id}")

    @staticmethod
    def get_standings():
        return FootballService._get(
            f"/competitions/{current_app.config['FOOTBALL_COMPETITION_CODE']}/standings"
        )

    @staticmethod
    def sync_matches_to_db(pool_id=None):
        pool = Pool.get_by_id(pool_id) if pool_id else Pool.get_default()
        if pool is None:
            raise RuntimeError("Crie um bolão antes de sincronizar jogos.")

        payload = FootballService.get_next_matches()
        matches = payload.get("matches", [])
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
        match = payload.get("match", payload)
        normalized = FootballService._normalize_match(match)
        return Game.upsert_external(game["pool_id"], normalized)

    @staticmethod
    def _get(path, params=None):
        FootballService._throttle()
        api_url = current_app.config["FOOTBALL_API_URL"].rstrip("/")
        api_key = current_app.config["FOOTBALL_API_KEY"]
        if not api_key:
            raise RuntimeError("FOOTBALL_API_KEY não configurada.")

        response = requests.get(
            f"{api_url}{path}",
            params=params,
            headers={"X-Auth-Token": api_key},
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
        score = match.get("score", {})
        full_time = score.get("fullTime") or {}
        competition = match.get("competition") or {}
        home_team = match.get("homeTeam") or {}
        away_team = match.get("awayTeam") or {}
        api_status = match.get("status", "SCHEDULED")

        return {
            "external_match_id": match["id"],
            "competition_code": competition.get("code") or current_app.config["FOOTBALL_COMPETITION_CODE"],
            "competition_name": competition.get("name"),
            "matchday": match.get("matchday"),
            "home_team": home_team.get("shortName") or home_team.get("name"),
            "away_team": away_team.get("shortName") or away_team.get("name"),
            "home_crest": home_team.get("crest"),
            "away_crest": away_team.get("crest"),
            "match_datetime": match.get("utcDate"),
            "home_score": full_time.get("home"),
            "away_score": full_time.get("away"),
            "api_status": api_status,
            "status": FootballService._map_status(api_status),
        }

    @staticmethod
    def _map_status(api_status):
        status = (api_status or "").upper()
        if status in {"FINISHED", "AWARDED"}:
            return "finished"
        if status in {"IN_PLAY", "LIVE", "PAUSED"}:
            return "live"
        if status in {"POSTPONED", "SUSPENDED", "CANCELLED"}:
            return "cancelled"
        return "scheduled"
