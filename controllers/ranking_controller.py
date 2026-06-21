from flask import Blueprint, render_template
from flask_login import login_required

from models.score import Score
from models.user import Pool


ranking_bp = Blueprint("ranking", __name__, url_prefix="/ranking")


@ranking_bp.route("/")
@login_required
def index():
    pool = Pool.get_default()
    ranking = Score.get_ranking(pool["id"]) if pool else []
    return render_template("ranking/index.html", pool=pool, ranking=ranking)


@ranking_bp.route("/pool/<int:pool_id>")
@login_required
def pool_ranking(pool_id):
    pool = Pool.get_by_id(pool_id)
    ranking = Score.get_ranking(pool_id)
    return render_template("ranking/index.html", pool=pool, ranking=ranking)
