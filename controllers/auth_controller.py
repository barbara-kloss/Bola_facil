import sqlite3

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models.user import Pool, User
from utils.helpers import is_valid_email, is_valid_password
from utils.messages import ApiMessages


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
            if request.is_json:
                return jsonify({"error": ApiMessages.AUTH_LOGIN_ERROR}), 401
            flash(ApiMessages.AUTH_LOGIN_ERROR, "error")
            return render_template("auth/login.html"), 401

        login_user(user)
        if request.is_json:
            return jsonify({"message": ApiMessages.AUTH_LOGIN_SUCCESS})
        flash(ApiMessages.AUTH_LOGIN_SUCCESS, "success")
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
            if request.is_json:
                return jsonify({"error": ApiMessages.VALIDATION_REQUIRED_FIELD}), 400
            flash(ApiMessages.VALIDATION_REQUIRED_FIELD, "error")
            return render_template("auth/register.html"), 400

        try:
            user = User.create(name, email, password, whatsapp_phone)
            if Pool.get_default() is None:
                Pool.create("Bolão Principal", user.id, "Grupo principal do BolãoFácil")
            login_user(user)
        except sqlite3.IntegrityError:
            if request.is_json:
                return jsonify({"error": ApiMessages.AUTH_REGISTER_ERROR}), 409
            flash(ApiMessages.AUTH_REGISTER_ERROR, "error")
            return render_template("auth/register.html"), 409

        if request.is_json:
            return jsonify({"message": ApiMessages.AUTH_REGISTER_SUCCESS, "user_id": user.id}), 201
        flash(ApiMessages.AUTH_REGISTER_SUCCESS, "success")
        return redirect(url_for("games.list_games"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash(ApiMessages.AUTH_LOGOUT_SUCCESS, "success")
    return redirect(url_for("auth.login"))
