import os
import psycopg2
import psycopg2.extras
from pathlib import Path

from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required
from flask_socketio import SocketIO

from config import DevelopmentConfig
from controllers.auth_controller import auth_bp
from controllers.bet_controller import bet_bp
from controllers.game_controller import game_bp
from controllers.ranking_controller import ranking_bp
from controllers.whatsapp_controller import whatsapp_bp
from controllers.admin_controller import admin_bp
from controllers.chat_controller import chat_bp
from controllers.notification_controller import notification_bp
from controllers.pool_controller import pool_bp
from models.user import User
from services.football_service import FootballService
from utils.decorators import admin_required
from utils.csrf import generate_csrf_token, validate_csrf_token


# SocketIO global instance (configured in create_app)
socketio = SocketIO()


login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para continuar."


class _PgWrapper:
    """Wrapper sobre psycopg2 que imita a interface do sqlite3 (execute/fetchone/fetchall/commit)."""
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Converte placeholders ? do SQLite para %s do PostgreSQL
        sql = sql.replace("?", "%s")
        cur.execute(sql, params)
        return _PgCursor(cur)

    def executescript(self, sql):
        cur = self._conn.cursor()
        cur.execute(sql)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


class _PgCursor:
    """Cursor wrapper que imita sqlite3.Cursor e retorna RealDictRow compatível com row['col']."""
    def __init__(self, cur):
        self._cur = cur

    def fetchone(self):
        row = self._cur.fetchone()
        return _PgRow(row) if row else None

    def fetchall(self):
        return [_PgRow(r) for r in self._cur.fetchall()]

    @property
    def lastrowid(self):
        # psycopg2 não tem lastrowid — usamos RETURNING id nas queries
        try:
            row = self._cur.fetchone()
            if row:
                return row.get("id") or row.get(list(row.keys())[0])
        except Exception:
            pass
        return None

    def __iter__(self):
        return iter(self.fetchall())


class _PgRow:
    """Imita sqlite3.Row: acesso por nome (row['col']) e por índice (row[0])."""
    def __init__(self, data):
        self._data = dict(data) if data else {}
        self._keys = list(self._data.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[self._keys[key]]
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._keys

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data.values())

    def __repr__(self):
        return repr(self._data)


def get_db():
    if "db" not in g:
        database_url = current_app_config()["DATABASE_URL"]
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        g.db = _PgWrapper(conn)
    return g.db


def current_app_config():
    from flask import current_app

    return current_app.config


def init_database(app):
    """Cria as tabelas no Supabase/PostgreSQL se ainda não existirem."""
    database_url = app.config["DATABASE_URL"]
    schema_path = Path(app.root_path) / "database" / "schema_pg.sql"

    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.users')")
        has_users = cur.fetchone()[0]
        if not has_users:
            cur.execute(schema_path.read_text(encoding="utf-8"))
        cur.close()
        conn.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Erro ao inicializar banco de dados: {e}")
        raise


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
    app.register_blueprint(pool_bp)

    # Initialize SocketIO with the app
    socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")

    # Register SocketIO event handlers
    from controllers.socket_controller import register_socket_handlers
    register_socket_handlers(socketio)

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
            "csrf_token": generate_csrf_token,
        }

    # CSRF: verifica token em todos os POSTs que NÃO sejam JSON puro de API
    # (rotas de webhook ou API interna ficam de fora via flag no blueprint)
    CSRF_EXEMPT_PATHS = {"/whatsapp/webhook"}

    @app.before_request
    def csrf_check():
        if app.config.get("TESTING"):
            return
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if request.path in CSRF_EXEMPT_PATHS:
                return
            if not validate_csrf_token():
                if request.is_json:
                    return jsonify({"error": "Token CSRF inválido ou ausente."}), 403
                flash("Sessão expirada. Por favor, tente novamente.", "error")
                return redirect(request.referrer or url_for("auth.login"))

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
        flash(f"{len(synced_games)} jogos sincronizados com a API-Sports.", "success")
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


app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=os.environ.get("FLASK_DEBUG", "1") == "1", allow_unsafe_werkzeug=True)
    # trigger reload 2
