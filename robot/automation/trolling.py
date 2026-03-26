import math
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from automation.game_state import GameState
from automation.game_controller import GameController

class Trolling:
    def __init__(self, toxicity):
        self.toxicity = toxicity / 10 ** (int(math.log10(toxicity)))


if __name__ == "__main__":
    chris = Trolling(6767)
    print(chris.toxicity)