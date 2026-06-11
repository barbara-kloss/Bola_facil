"""
Modelo de Aposta
"""

from datetime import datetime
from enum import Enum

class BetStatus(Enum):
    """Status possíveis de uma aposta"""
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    DRAW = "draw"

class Bet:
    """Modelo para representar uma aposta"""
    
    def __init__(self, user_id, game_id, prediction, amount=0):
        self.id = None
        self.user_id = user_id
        self.game_id = game_id
        self.prediction = prediction  # ex: "1", "X", "2" ou placar exato
        self.amount = amount
        self.status = BetStatus.PENDING
        self.points_awarded = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def __repr__(self):
        return f'<Bet user_id={self.user_id} game_id={self.game_id}>'
    
    def to_dict(self):
        """Converte a aposta para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_id': self.game_id,
            'prediction': self.prediction,
            'amount': self.amount,
            'status': self.status.value,
            'points_awarded': self.points_awarded,
            'created_at': self.created_at.isoformat()
        }
