"""
Modelo de Pontuação
"""

from datetime import datetime

class Score:
    """Modelo para representar a pontuação de um usuário"""
    
    def __init__(self, user_id, game_id, points=0):
        self.id = None
        self.user_id = user_id
        self.game_id = game_id
        self.points = points
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def __repr__(self):
        return f'<Score user_id={self.user_id} points={self.points}>'
    
    def to_dict(self):
        """Converte a pontuação para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_id': self.game_id,
            'points': self.points,
            'created_at': self.created_at.isoformat()
        }
