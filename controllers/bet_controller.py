"""
Controlador de Apostas
"""

from flask import Blueprint, render_template, request, jsonify

bet_bp = Blueprint('bet', __name__, url_prefix='/bets')

@bet_bp.route('/form/<int:game_id>', methods=['GET'])
def bet_form(game_id):
    """Formulário para fazer uma aposta"""
    # TODO: Buscar jogo e dados do usuário
    game = None
    return render_template('bets/form.html', game=game)

@bet_bp.route('/create', methods=['POST'])
def create_bet():
    """Criar nova aposta"""
    data = request.get_json()
    user_id = data.get('user_id')
    game_id = data.get('game_id')
    prediction = data.get('prediction')
    
    # TODO: Validar e criar aposta
    
    return jsonify({'message': 'Aposta realizada com sucesso'})

@bet_bp.route('/user/<int:user_id>', methods=['GET'])
def user_bets(user_id):
    """Listar apostas de um usuário"""
    # TODO: Buscar apostas do usuário
    bets = []
    return jsonify({'bets': bets})

@bet_bp.route('/game/<int:game_id>', methods=['GET'])
def game_bets(game_id):
    """Listar todas as apostas de um jogo"""
    # TODO: Buscar apostas do jogo
    bets = []
    return jsonify({'bets': bets})
