"""
Modelo de Usuário
"""

from datetime import datetime

class User:
    """Modelo para representar um usuário"""
    
    def __init__(self, username, email, password_hash, phone=None):
        self.id = None
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.phone = phone
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.is_active = True
        self.total_points = 0
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Converte o usuário para dicionário"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'total_points': self.total_points,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
