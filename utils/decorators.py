"""
Decoradores úteis para a aplicação
"""

from functools import wraps
from flask import session, redirect, jsonify

def login_required(f):
    """
    Decorador para verificar se usuário está autenticado
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated_function

def api_login_required(f):
    """
    Decorador para verificar autenticação em endpoints da API
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorador para verificar se usuário é administrador
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('is_admin') != True:
            return jsonify({'error': 'Acesso negado'}), 403
        return f(*args, **kwargs)
    return decorated_function
