
import sys
import os
from pathlib import Path

# Add backend to path so we can import src
sys.path.append(str(Path("backend").resolve()))

from src.gui.models.simulation_model import PlayoffProbabilityModel
from PySide6.QtCore import Qt

class MockStats:
    def __init__(self, avg_wins, playoff_prob, div_prob, first_seed_prob):
        self.average_wins = avg_wins
        self.playoff_probability = playoff_prob
        self.division_win_probability = div_prob
        self.first_seed_probability = first_seed_prob

class MockResult:
    def __init__(self):
        self.team_stats = {
            "TEAM1": MockStats(10.0, 0.8, 0.5, 0.2),
            "TEAM2": MockStats(8.0, 0.4, 0.1, 0.0),
            "TEAM3": MockStats(12.0, 0.9, 0.8, 0.4)
        }

class MockTeam:
    def __init__(self, name):
        self.display_name = name
        self.id = name # simpler

teams_dict = {
    "TEAM1": MockTeam("Team One"),
    "TEAM2": MockTeam("Team Two"),
    "TEAM3": MockTeam("Team Three")
}

def test_sorting():
    result = MockResult()
    # Modify result to match what model expects (result.team_stats)
    
    model = PlayoffProbabilityModel(result, teams_dict)
    
    print("Initial order (sorted by Playoff % desc):")
    for i in range(model.rowCount()):
        print(f"{model.data(model.index(i, 0))} - {model.data(model.index(i, 2))}")

    # Sort by Avg Wins (column 1), ascending
    print("\nSorting by Avg Wins (Ascending)...")
    model.sort(1, Qt.AscendingOrder)
    for i in range(model.rowCount()):
        print(f"{model.data(model.index(i, 0))} - {model.data(model.index(i, 1))}")

    # Sort by Team Name (column 0), ascending
    print("\nSorting by Team Name (Ascending)...")
    model.sort(0, Qt.AscendingOrder)
    for i in range(model.rowCount()):
        print(f"{model.data(model.index(i, 0))}")

if __name__ == "__main__":
    test_sorting()
