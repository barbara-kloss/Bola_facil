import sqlite3

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models.user import Pool, User
from utils.helpers import is_valid_email, is_valid_password


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and request.method == "GET":
        return redirect(url_for("games.list_games"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        email = data.get("email", "")
        password = data.get("password", "")
        user = User.get_by_email(email)

        if not user or not user.check_password(password):
            message = "E-mail ou senha inválidos."
            if request.is_json:
                return jsonify({"error": message}), 401
            flash(message, "error")
            return render_template("auth/login.html"), 401

        login_user(user)
        if request.is_json:
            return jsonify({"message": "Login realizado com sucesso."})
        flash("Login realizado com sucesso.", "success")
        return redirect(url_for("games.list_games"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("games.list_games"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        whatsapp_phone = data.get("whatsapp_phone", "").strip() or None

        if not name or not is_valid_email(email) or not is_valid_password(password):
            message = "Informe nome, e-mail válido e senha com pelo menos 6 caracteres."
            if request.is_json:
                return jsonify({"error": message}), 400
            flash(message, "error")
            return render_template("auth/register.html"), 400

        try:
            user = User.create(name, email, password, whatsapp_phone)
            if Pool.get_default() is None:
                Pool.create("Bolão Principal", user.id, "Grupo principal do BolãoFácil")
            login_user(user)
        except sqlite3.IntegrityError:
            message = "Este e-mail já está cadastrado."
            if request.is_json:
                return jsonify({"error": message}), 409
            flash(message, "error")
            return render_template("auth/register.html"), 409

        if request.is_json:
            return jsonify({"message": "Cadastro realizado com sucesso.", "user_id": user.id}), 201
        flash("Cadastro realizado com sucesso.", "success")
        return redirect(url_for("games.list_games"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "success")
    return redirect(url_for("auth.login"))
