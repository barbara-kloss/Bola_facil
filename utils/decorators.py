from functools import wraps

from flask import abort
from flask_login import current_user, login_required

from models.user import Pool, PoolMember


def login_required_pool_member(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        pool_id = kwargs.get("pool_id")
        if pool_id and not PoolMember.exists(pool_id, current_user.id):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def pool_admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        pool_id = kwargs.get("pool_id")
        if pool_id and not Pool.is_admin(pool_id, current_user.id):
            abort(403)
        return view(*args, **kwargs)

    return wrapped
