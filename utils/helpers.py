"""
Funções auxiliares
"""

from datetime import datetime, timedelta

def format_date(date):
    """Formata data para string"""
    if date:
        return date.strftime('%d/%m/%Y %H:%M')
    return ''

def get_remaining_time(scheduled_at):
    """Retorna tempo restante até o início de um jogo"""
    now = datetime.now()
    diff = scheduled_at - now
    
    if diff.total_seconds() <= 0:
        return "Jogo iniciado"
    
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    
    return f"{hours}h {minutes}m"

def validate_email(email):
    """Valida formato de email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def hash_password(password):
    """Criptografa senha"""
    # TODO: Implementar hashing seguro com bcrypt ou similar
    return password

def verify_password(password, password_hash):
    """Verifica se senha corresponde ao hash"""
    # TODO: Implementar verificação de hash
    return password == password_hash
