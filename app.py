import os
import sqlite3
from pathlib import Path

from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required

from config import DevelopmentConfig
from controllers.auth_controller import auth_bp
from controllers.bet_controller import bet_bp
from controllers.game_controller import game_bp
from controllers.ranking_controller import ranking_bp
from controllers.whatsapp_controller import whatsapp_bp
from controllers.admin_controller import admin_bp
from controllers.chat_controller import chat_bp
from controllers.notification_controller import notification_bp
from models.user import User
from services.football_service import FootballService
from utils.decorators import admin_required


login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para continuar."


def get_db():
    if "db" not in g:
        database_url = current_app_config()["DATABASE_URL"]
        database_path = Path(database_url)
        database_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def current_app_config():
    from flask import current_app

    return current_app.config


def init_database(app):
    database_path = Path(app.config["DATABASE_URL"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path = Path(app.root_path) / "database" / "schema.sql"

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        has_users = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'"
        ).fetchone()
        if not has_users:
            connection.executescript(schema_path.read_text(encoding="utf-8"))
            connection.commit()
        ensure_schema_updates(connection)


def ensure_schema_updates(connection):
    # --- users table columns ---
    user_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(users)").fetchall()
    }
    user_additions = {
        "role": "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'",
        "notifications_enabled": "ALTER TABLE users ADD COLUMN notifications_enabled INTEGER NOT NULL DEFAULT 1",
    }
    for column, statement in user_additions.items():
        if column not in user_columns:
            connection.execute(statement)

    # --- games table columns ---
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(games)").fetchall()
    }
    additions = {
        "external_match_id": "ALTER TABLE games ADD COLUMN external_match_id INTEGER",
        "competition_code": "ALTER TABLE games ADD COLUMN competition_code TEXT",
        "competition_name": "ALTER TABLE games ADD COLUMN competition_name TEXT",
        "matchday": "ALTER TABLE games ADD COLUMN matchday INTEGER",
        "home_crest": "ALTER TABLE games ADD COLUMN home_crest TEXT",
        "away_crest": "ALTER TABLE games ADD COLUMN away_crest TEXT",
        "api_status": "ALTER TABLE games ADD COLUMN api_status TEXT",
        "last_synced_at": "ALTER TABLE games ADD COLUMN last_synced_at TEXT",
    }
    for column, statement in additions.items():
        if column not in columns:
            connection.execute(statement)

    # --- indexes ---
    indexes = [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_games_external_match_id ON games(external_match_id)",
        "CREATE INDEX IF NOT EXISTS idx_games_competition_code ON games(competition_code)",
    ]
    for statement in indexes:
        connection.execute(statement)

    # --- new tables (chat + notifications) ---
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS chat_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS chat_group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES chat_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE (group_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            sender_id INTEGER NOT NULL DEFAULT 0,
            recipient_id INTEGER,
            text TEXT NOT NULL,
            is_bot INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES chat_groups(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            read INTEGER NOT NULL DEFAULT 0,
            extra_data TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_group ON chat_messages(group_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_recipient ON chat_messages(recipient_id);
    """)

    connection.commit()


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or DevelopmentConfig)

    init_database(app)

    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(bet_bp)
    app.register_blueprint(ranking_bp)
    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(notification_bp)

    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.context_processor
    def inject_brand():
        return {
            "brand_name": "BolãoFácil",
            "brand_slogan": "Jogue Junto. Torça. Ganhe.",
            "current_user": current_user,
        }

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("games.list_games"))
        return redirect(url_for("auth.login"))

    @app.route("/stats")
    def stats_dashboard():
        db = get_db()
        stats = {
            "total_pools": db.execute("SELECT COUNT(*) FROM pools").fetchone()[0],
            "total_bets": db.execute("SELECT COUNT(*) FROM bets").fetchone()[0],
            "total_points": db.execute("SELECT COALESCE(SUM(points_earned), 0) FROM bets").fetchone()[0],
        }
        return render_template("stats/dashboard.html", stats=stats)

    @app.route("/admin/sync-games", methods=["GET", "POST"])
    @admin_required
    def sync_games():
        try:
            synced_games = FootballService.sync_matches_to_db()
        except Exception as exc:
            if request.accept_mimetypes.best == "application/json":
                return jsonify({"error": str(exc)}), 502
            flash(f"Não foi possível sincronizar jogos: {exc}", "error")
            return redirect(url_for("games.list_games"))

        if request.accept_mimetypes.best == "application/json":
            return jsonify({"message": "Jogos sincronizados.", "count": len(synced_games)})
        flash(f"{len(synced_games)} jogos sincronizados com a football-data.org.", "success")
        return redirect(url_for("games.list_games"))

    @app.errorhandler(403)
    def forbidden(error):
        if request.accept_mimetypes.best == "application/json":
            return jsonify({"error": "Acesso negado."}), 403
        return render_template("base.html", error_message="Acesso negado."), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.accept_mimetypes.best == "application/json":
            return jsonify({"error": "Página não encontrada."}), 404
        return render_template("base.html", error_message="Página não encontrada."), 404

    @app.errorhandler(500)
    def internal_error(error):
        if request.accept_mimetypes.best == "application/json":
            return jsonify({"error": "Erro interno do servidor."}), 500
        return render_template("base.html", error_message="Erro interno do servidor."), 500

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


if __name__ == "__main__":
    create_app().run(debug=os.environ.get("FLASK_DEBUG", "1") == "1")
