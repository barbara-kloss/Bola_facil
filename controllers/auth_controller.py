import sqlite3

from flask import Blueprint, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models.user import Pool, User
from utils.helpers import is_valid_email, is_valid_password
from utils.messages import ApiMessages
from utils.responses import respond
from utils import rate_limit


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and request.method == "GET":
        from flask import redirect
        return redirect(url_for("games.list_games"))

    if request.method == "POST":
        if rate_limit.is_blocked():
            remaining = rate_limit.remaining_lockout()
            return respond(
                f"Muitas tentativas falhas. Tente novamente em {remaining} segundos.",
                ok=False, status=429,
                template_fn=render_template,
                template_kwargs={"template_name_or_list": "auth/login.html"},
            )

        data = request.get_json(silent=True) or request.form
        email = data.get("email", "")
        password = data.get("password", "")
        user = User.get_by_email(email)

        if not user or not user.check_password(password):
            rate_limit.record_failure()
            return respond(
                ApiMessages.AUTH_LOGIN_ERROR,
                ok=False, status=401,
                template_fn=render_template,
                template_kwargs={"template_name_or_list": "auth/login.html"},
            )

        rate_limit.record_success()
        login_user(user)
        if user.is_admin:
            return respond(
                ApiMessages.AUTH_LOGIN_SUCCESS,
                ok=True, redirect_to="admin.dashboard",
            )
        return respond(
            ApiMessages.AUTH_LOGIN_SUCCESS,
            ok=True, redirect_to="games.list_games",
        )

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@auth_bp.route("/cadastro", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        from flask import redirect
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("games.list_games"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        whatsapp_phone = data.get("whatsapp_phone", "").strip() or None

        if not name or not is_valid_email(email) or not is_valid_password(password):
            return respond(
                ApiMessages.VALIDATION_REQUIRED_FIELD,
                ok=False, status=400,
                template_fn=render_template,
                template_kwargs={"template_name_or_list": "auth/register.html"},
            )

        existing_user = User.get_by_email(email)
        if existing_user:
            return respond(
                "E-mail já cadastrado. Faça login ou use outro endereço.",
                ok=False, status=409,
                template_fn=render_template,
                template_kwargs={"template_name_or_list": "auth/register.html"},
            )

        try:
            user = User.create(name, email, password, whatsapp_phone)
            if Pool.get_default() is None:
                Pool.create("Bolão Principal", user.id, "Grupo principal do BolãoFácil")

            from models.chat import ChatGroupInvite
            ChatGroupInvite.accept_all_for_user(user.id, email)

            login_user(user)
        except sqlite3.IntegrityError:
            return respond(
                ApiMessages.AUTH_REGISTER_ERROR,
                ok=False, status=409,
                template_fn=render_template,
                template_kwargs={"template_name_or_list": "auth/register.html"},
            )

        if user.is_admin:
            return respond(
                ApiMessages.AUTH_REGISTER_SUCCESS,
                ok=True, status=201, redirect_to="admin.dashboard",
                data={"user_id": user.id},
            )
        return respond(
            ApiMessages.AUTH_REGISTER_SUCCESS,
            ok=True, status=201, redirect_to="games.list_games",
            data={"user_id": user.id},
        )

    return render_template("auth/register.html")


@auth_bp.route("/perfil", methods=["GET"])
@login_required
def profile():
    return render_template("auth/profile.html")


@auth_bp.route("/perfil/atualizar", methods=["POST"])
@login_required
def update_profile():
    data = request.get_json(silent=True) or request.form

    name = data.get("name", current_user.name).strip()
    email = data.get("email", current_user.email).strip()

    if email != current_user.email:
        existing_user = User.get_by_email(email)
        if existing_user:
            return respond(
                "E-mail já cadastrado por outro usuário. Escolha outro endereço.",
                ok=False, status=409,
                redirect_to="auth.profile",
            )

    whatsapp_phone = data.get("whatsapp_phone", "").strip() or None
    if whatsapp_phone:
        whatsapp_phone = "".join(filter(str.isdigit, whatsapp_phone))

    User.update(current_user.id, name, email, whatsapp_phone)
    current_user.name = name
    current_user.email = email
    current_user.whatsapp_phone = whatsapp_phone

    enabled = str(data.get("enabled", "0")).lower() in ["1", "true", "on", "yes"]
    User.set_notification_preference(current_user.id, enabled)
    current_user.notifications_enabled = 1 if enabled else 0

    return respond(
        "Perfil salvo com sucesso!",
        ok=True, redirect_to="auth.profile",
    )


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return respond(
        ApiMessages.AUTH_LOGOUT_SUCCESS,
        ok=True, redirect_to="auth.login",
    )
