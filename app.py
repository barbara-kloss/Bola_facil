"""
BolãoFácil - Aplicação Principal
Sistema de gerenciamento de apostas e rankings
"""

from flask import Flask, render_template, request, jsonify
from config import Config
from controllers import auth_controller, game_controller, bet_controller, ranking_controller

app = Flask(__name__)
app.config.from_object(Config)

# Registrar blueprints
app.register_blueprint(auth_controller.auth_bp)
app.register_blueprint(game_controller.game_bp)
app.register_blueprint(bet_controller.bet_bp)
app.register_blueprint(ranking_controller.ranking_bp)

@app.route('/')
def index():
    """Página inicial da aplicação"""
    return render_template('base.html')

@app.errorhandler(404)
def not_found(error):
    """Tratamento de página não encontrada"""
    return jsonify({'error': 'Página não encontrada'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Tratamento de erro interno do servidor"""
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    app.run(debug=True)
