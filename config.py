import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL", "database/bolao_facil.db")
    WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "")
    WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")
    FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
    FOOTBALL_API_URL = os.environ.get("FOOTBALL_API_URL", "https://api.football-data.org/v4")
    FOOTBALL_COMPETITION_CODE = "BSA"
    FOOTBALL_RATE_LIMIT_PER_MINUTE = 10

    EXACT_SCORE_POINTS = 10
    WINNER_AND_GOALS_POINTS = 5
    WINNER_ONLY_POINTS = 3
    DRAW_POINTS = 2

    JSON_AS_ASCII = False


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        str(Path("database") / "bolao_facil.db"),
    )
