"""
Controlador de Jogos
"""

from flask import Blueprint, render_template, request, jsonify

game_bp = Blueprint('game', __name__, url_prefix='/games')

@game_bp.route('/', methods=['GET'])
def list_games():
    """Listar todos os jogos"""
    # TODO: Buscar jogos do banco de dados
    games = []
    return render_template('games/list.html', games=games)

@game_bp.route('/<int:game_id>')
def game_detail(game_id):
    """Detalhes de um jogo específico"""
    # TODO: Buscar jogo do banco de dados
    game = None
    return render_template('games/detail.html', game=game)

@game_bp.route('/create', methods=['POST'])
def create_game():
    """Criar novo jogo"""
    data = request.get_json()
    team_a = data.get('team_a')
    team_b = data.get('team_b')
    scheduled_at = data.get('scheduled_at')
    
    # TODO: Validar e criar jogo
    
    return jsonify({'message': 'Jogo criado com sucesso'})

@game_bp.route('/<int:game_id>/finish', methods=['POST'])
def finish_game(game_id):
    """Finalizar um jogo com resultado"""
    data = request.get_json()
    goals_a = data.get('goals_a')
    goals_b = data.get('goals_b')
    
    # TODO: Atualizar jogo e calcular pontuações
    
    return jsonify({'message': 'Jogo finalizado'})
