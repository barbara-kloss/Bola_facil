"""
Controlador de Ranking
"""

from flask import Blueprint, render_template, jsonify

ranking_bp = Blueprint('ranking', __name__, url_prefix='/ranking')

@ranking_bp.route('/')
def ranking():
    """Exibir ranking geral"""
    # TODO: Buscar ranking do banco de dados
    rankings = []
    return render_template('ranking/index.html', rankings=rankings)

@ranking_bp.route('/api', methods=['GET'])
def ranking_api():
    """API para obter ranking"""
    # TODO: Buscar ranking ordenado por pontos
    rankings = []
    return jsonify({'rankings': rankings})

@ranking_bp.route('/user/<int:user_id>')
def user_ranking(user_id):
    """Posição de um usuário no ranking"""
    # TODO: Buscar posição do usuário
    position = None
    return jsonify({'position': position})
