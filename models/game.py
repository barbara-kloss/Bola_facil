"""
Modelo de Jogo
"""

from datetime import datetime
from enum import Enum

class GameStatus(Enum):
    """Status possíveis de um jogo"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"

class Game:
    """Modelo para representar um jogo/partida"""
    
    def __init__(self, team_a, team_b, scheduled_at, league=None):
        self.id = None
        self.team_a = team_a
        self.team_b = team_b
        self.scheduled_at = scheduled_at
        self.league = league
        self.status = GameStatus.SCHEDULED
        self.goals_a = None
        self.goals_b = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def __repr__(self):
        return f'<Game {self.team_a} x {self.team_b}>'
    
    def to_dict(self):
        """Converte o jogo para dicionário"""
        return {
            'id': self.id,
            'team_a': self.team_a,
            'team_b': self.team_b,
            'scheduled_at': self.scheduled_at.isoformat(),
            'league': self.league,
            'status': self.status.value,
            'goals_a': self.goals_a,
            'goals_b': self.goals_b
        }
