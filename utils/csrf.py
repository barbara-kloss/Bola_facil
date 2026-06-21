"""
Proteção CSRF simples usando tokens de sessão do Flask.
Não depende de Flask-WTF — funciona com qualquer formulário HTML.
"""
import secrets
from functools import wraps
from flask import abort, request, session


_CSRF_KEY = "_csrf_token"


def generate_csrf_token() -> str:
    """Gera e armazena um token CSRF na sessão se não existir."""
    if _CSRF_KEY not in session:
        session[_CSRF_KEY] = secrets.token_hex(32)
    return session[_CSRF_KEY]


def validate_csrf_token() -> bool:
    """
    Valida o token CSRF enviado pelo cliente.
    Aceita tanto o header X-CSRFToken (fetch/AJAX) quanto o campo _csrf_token do form.
    """
    expected = session.get(_CSRF_KEY)
    if not expected:
        return False
    received = (
        request.headers.get("X-CSRFToken")
        or request.form.get("_csrf_token")
        or (request.get_json(silent=True) or {}).get("_csrf_token")
    )
    return secrets.compare_digest(expected, received or "")


def csrf_protect(view):
    """
    Decorador que valida o token CSRF em requisições POST/PUT/PATCH/DELETE.
    Requisições GET/HEAD/OPTIONS são sempre permitidas.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if not validate_csrf_token():
                abort(403)
        return view(*args, **kwargs)
    return wrapped
