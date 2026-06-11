"""
Controlador de Autenticação
"""

from flask import Blueprint, render_template, request, jsonify, redirect, session

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Fazer login"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # TODO: Validar credenciais no banco de dados
        
        return jsonify({'message': 'Login realizado com sucesso'})
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registrar novo usuário"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # TODO: Validar e criar novo usuário
        
        return jsonify({'message': 'Usuário registrado com sucesso'})
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Fazer logout"""
    session.clear()
    return redirect('/')
