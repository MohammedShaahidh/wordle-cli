
from history import GameHistory

class GameStats:

    def __init__(self, history: GameHistory ):
        self.history = history
        
    
    @property
    def total_games(self) -> int:
        """Return the total number of completed games."""
        return len(self.history.records)

    @property
    def total_wins(self) -> int:
        """Return the total number of won games."""
        return sum(1 for record in self.history.records if record["won"])

    @property
    def win_percentage(self) -> float:
        """Return the percentage of games won (0.0 to 100.0)."""
        if not self.history.records:
            return 0.0
        return (self.total_wins / self.total_games) * 100.0

    @property
    def current_streak(self) -> int:
        """Return the number of consecutive wins ending with the most recent game."""
        streak = 0
        for record in reversed(self.history.records):
            if record["won"]:
                streak += 1
            else:
                break
        return streak

    @property
    def best_streak(self) -> int:
        """Return the longest consecutive winning streak in the history."""
        best = 0
        current = 0
        for record in self.history.records:
            if record["won"]:
                current += 1
                if current > best:
                    best = current
            else:
                current = 0
        return best
