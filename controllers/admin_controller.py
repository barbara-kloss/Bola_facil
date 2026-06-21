from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from utils.decorators import admin_required
from models.user import User

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/dashboard")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")

@admin_bp.route("/admin/users")
@admin_required
def users():
    all_users = User.list()
    return render_template("admin/users.html", users=all_users)

@admin_bp.route("/admin/alerts")
@admin_required
def alerts():
    from models.notification import Notification
    all_alerts = Notification.list_all(100)
    return render_template("admin/alerts.html", alerts=all_alerts)
