from flask import Blueprint, jsonify, render_template, abort
from flask_login import current_user, login_required

from models.user import Pool, PoolMember
from utils.decorators import pool_admin_required

pool_bp = Blueprint("pools", __name__, url_prefix="/pools")


@pool_bp.route("/<int:pool_id>/members", methods=["GET"])
@login_required
@pool_admin_required
def manage_members(pool_id):
    pool = Pool.get_by_id(pool_id)
    if not pool:
        abort(404)
    members = PoolMember.list_by_pool(pool_id)
    return render_template("pools/members.html", pool=pool, members=members)


@pool_bp.route("/<int:pool_id>/members/<int:user_id>/role", methods=["POST"])
@login_required
@pool_admin_required
def toggle_member_role(pool_id, user_id):
    if str(user_id) == str(current_user.id):
        return jsonify({"error": "Você não pode alterar seu próprio privilégio."}), 400

    members = PoolMember.list_by_pool(pool_id)
    target_member = next((m for m in members if m["user_id"] == user_id), None)

    if not target_member:
        return jsonify({"error": "Membro não encontrado."}), 404

    new_role = "member" if target_member["role"] == "admin" else "admin"
    PoolMember.update_role(pool_id, user_id, new_role)

    return jsonify({"success": True, "new_role": new_role})
