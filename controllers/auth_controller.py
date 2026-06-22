import sqlite3

from flask import Blueprint, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models.user import Pool, User
from utils.helpers import is_valid_email, is_valid_password, is_valid_phone
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
                template_kwargs={"template_name_or_list": "auth/login.html", "email": email},
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

        if not name:
            return respond("O nome é obrigatório.", ok=False, status=400, template_fn=render_template, template_kwargs={"template_name_or_list": "auth/register.html"})
        if not is_valid_email(email):
            return respond("E-mail inválido.", ok=False, status=400, template_fn=render_template, template_kwargs={"template_name_or_list": "auth/register.html"})
        if not is_valid_password(password):
            return respond("A senha deve ter no mínimo 8 caracteres, contendo pelo menos uma letra e um número.", ok=False, status=400, template_fn=render_template, template_kwargs={"template_name_or_list": "auth/register.html"})
        if whatsapp_phone and not is_valid_phone(whatsapp_phone):
            return respond("WhatsApp/Telefone inválido. Deve conter apenas números (DDD + 8 ou 9 dígitos).", ok=False, status=400, template_fn=render_template, template_kwargs={"template_name_or_list": "auth/register.html"})

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

    if not name:
        return respond("O nome é obrigatório.", ok=False, status=400, redirect_to="auth.profile")
    if not is_valid_email(email):
        return respond("E-mail inválido.", ok=False, status=400, redirect_to="auth.profile")

    whatsapp_phone = data.get("whatsapp_phone", "").strip() or None
    if whatsapp_phone and not is_valid_phone(whatsapp_phone):
        return respond("WhatsApp/Telefone inválido. Deve conter apenas números (DDD + 8 ou 9 dígitos).", ok=False, status=400, redirect_to="auth.profile")

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


@auth_bp.route("/esqueci-senha", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("games.list_games"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        email = data.get("email", "").strip()
        
        user = User.get_by_email(email)
        if user:
            token = User.generate_reset_token(user.id)
            reset_url = request.host_url.rstrip("/") + url_for("auth.reset_password", token=token)
            
            from services.email_service import EmailService
            EmailService.send_password_reset_email(user.email, user.name, reset_url)
            
        # Sempre retorna sucesso para não expor quais emails existem na base
        return respond(
            "Se o e-mail estiver cadastrado, você receberá um link para redefinir sua senha.",
            ok=True, redirect_to="auth.login"
        )

    return render_template("auth/forgot_password.html")


@auth_bp.route("/resetar-senha/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("games.list_games"))

    user = User.get_by_reset_token(token)
    if not user:
        flash("O link de redefinição é inválido ou expirou.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        password = data.get("password")
        password_confirm = data.get("password_confirm")

        if not password or len(password) < 6:
            return respond("A senha deve ter pelo menos 6 caracteres.", ok=False, status=400)
            
        if password != password_confirm:
            return respond("As senhas não coincidem.", ok=False, status=400)

        User.reset_password(user.id, password)
        return respond(
            "Sua senha foi redefinida com sucesso. Você já pode fazer login.",
            ok=True, redirect_to="auth.login"
        )

    return render_template("auth/reset_password.html", token=token)
