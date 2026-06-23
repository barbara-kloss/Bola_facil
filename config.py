import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL", "database/bolao_facil.db")
    WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "")
    WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")
    API_SPORTS_KEY = os.environ.get("API_SPORTS_KEY", "")
    API_SPORTS_URL = os.environ.get("API_SPORTS_URL", "https://v3.football.api-sports.io")
    FOOTBALL_COMPETITION_CODE = os.environ.get("FOOTBALL_COMPETITION_CODE", "1") # League ID para World Cup na API-Sports é 1
    API_SPORTS_SEASON = os.environ.get("API_SPORTS_SEASON", "2022")
    FOOTBALL_RATE_LIMIT_PER_MINUTE = 10

    SMTP_SERVER = os.environ.get("SMTP_SERVER", "")
    SMTP_PORT = os.environ.get("SMTP_PORT", 587)
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_SENDER = os.environ.get("SMTP_SENDER", "noreply@bolaofacil.com")

    EXACT_SCORE_POINTS = 10
    WINNER_AND_GOALS_POINTS = 5
    WINNER_ONLY_POINTS = 3
    DRAW_POINTS = 2
# teste
    BET_LOCKOUT_MINUTES = int(os.environ.get("BET_LOCKOUT_MINUTES", 10))

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
    
    def __init__(self):
        if os.environ.get("SECRET_KEY") is None:
            raise ValueError("SECRET_KEY não definida no ambiente de produção!")
