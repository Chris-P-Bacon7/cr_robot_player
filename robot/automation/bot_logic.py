import os
import sys

# Tell Python to look one folder up for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from perception.screen_mapper import ScreenMapper

class BotLogic:
    def __init__(self, cur_deck, arena_height=30, arena_width=18):
        self.arena_height = arena_height
        self.arena_width = arena_width
        self.crossed_bridge = arena_height * 0.45

        self.json_name = "card_database.json"
        self.json_location = f"robot\\{self.json_name}"
        self.deck = cur_deck

        self.data = self.load_json(self.json_location, self.json_name)
        self.counter_chart = self.config_json(self.data, "counters", cur_deck)
        self.card_info = self.config_json(self.data, "cards", cur_deck)
        self.screen_mapper = ScreenMapper(self.load_config("robot\\Chris_S25.json", "Chris_S25.json"), 18, 30)

    def load_config(self, json_location, json_name):
        if not os.path.exists(json_location):
            print(f"ERROR: \"{json_name}\" not found.")
            exit()
        
        with open(json_location, "r") as f:
            data = json.load(f)

        config = {}

        for k, v in data["arena"].items(): config[f"arena_{k}"] = tuple(v)
        for k, v in data["card_slots"].items(): config[k] = tuple(v)
        for k, v in data["elixir"].items(): config[f"elixir_{k}"] = tuple(v)
        
        return config

    def load_json(self, json_location, json_name):
        """Loads the .json file for the counters of cards.

        Args:
            json_location (str): Relative path of the json
            json_name (str): your_json_name.json

        Returns:
            dict: Fully configured counter_chart
        """
        if not os.path.exists(json_location):
            print(f"ERROR: \"{json_name}\" not found.")
            exit()
        
        with open(json_location, "r") as f:
            data = json.load(f)

        return data
    
    def config_json(self, data, config_type, deck):
        """Following loading the .json file, organize info into
        respective dictionaries for easier processing.

        Args:
            data (dic): Raw dictionary from loaded .json file.
            config_type (str): Enter "counters", "cards" in separate calls.
            deck (list): Current deck being used.

        Returns:
            dict: Configured dictionary based on requested config_type.
        """
        if config_type == "cards":
            cards_info = {}
            for card in deck:
                cards_info[f"{card}"] = data["cards"][card]
            return cards_info
        else:
            chart = data[f"{config_type}"]
            return chart
        
    
    def get_best_move(self, detections, current_hand, current_elixir, names_map):
        """
        Main brain function.

        Args:
            detections: List of YOLO "box" objects
            current_hand: List of card names currently available
            current_elixir: Integer
        """

        # 1. Find threats
        threats = []

        for box in detections:
            # Obtain all 6 data points from boxes in YOLOv8
            x1, y1, x2, y2 = box.xyxy[0]
            confidence = float(box.conf[0])
            cls_id = int(box.cls[0])

            if cls_id in names_map:
                raw_name = names_map[cls_id]
            else:
                continue

            # The classes are named [Team]-[TroopName]-[States]
            # We will split this into 3+ data points

            if "-" in raw_name:
                parts = raw_name.split("-")
                team = parts[0]
                troop = parts[1]

            # Calculate the centre of the enemy
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            tile_x, tile_y = self.screen_mapper.pixel_to_tile(cx, cy)

            if team == "Enemy" and troop not in ("PrincessTower", "KingTower"):
                if tile_y > self.crossed_bridge:
                    threats.append({
                        "Troop": troop,
                        "x": cx,
                        "y": cy,
                        "conf": confidence
                    })
            
        # Sort threats based on distance from bottom
        threats.sort(key=lambda t: t["y"], reverse=True)

        if len(threats) == 0:
            return None # No threats = Do nothing
        
        most_dangerous = threats[0]
        enemy_name = most_dangerous["Troop"]

        # 2. Decide counter
        if enemy_name not in self.counter_chart: # Make sure we have a counter
            print(f"LOGIC WARNING: No defined counter for {enemy_name}.")
            return None

        card_counters = []
        spell_counters = []

        for card in self.counter_chart[enemy_name]["primary"]:
            card_counters.append(card)
        for card in self.counter_chart[enemy_name]["secondary"]:
            card_counters.append(card)
        for card in self.counter_chart[enemy_name]["spell"]:
            spell_counters.append(card)
        
        available_cards = [card[0] for card in current_hand]
        elixir_stat = {}

        for card in self.data["cards"]:
            elixir_stat[f"{card}"] = self.data["cards"][f"{card}"]["elixir"]
        
        for card_name in card_counters:
            if card_name in available_cards:
                cost = elixir_stat[card_name]
                enemy_x = most_dangerous["x"]
                enemy_y = most_dangerous["y"]

                if current_elixir >= cost:
                    offset = self.card_info[card_name]["placement_offset"]
                    play_x, play_y = self.screen_mapper.pixel_to_tile(enemy_x, enemy_y)
                    
                    if play_x >= 9:
                        play_x -= (0.5 * offset ** 2) ** 0.5
                    else:
                        play_x += (0.5 * offset ** 2) ** 0.5
                    if play_x < 0:
                        play_x = 0
                    elif play_x > self.arena_width:
                        play_x = self.arena_width
                    
                    play_y -= (0.5 * offset ** 2) ** 0.5
                    if play_y < 0:
                        play_y = 0
                    elif play_y > self.arena_height:
                        play_y = self.arena_height
                    
                    play_x, play_y = self.screen_mapper.tile_to_pixel(play_x, play_y)
                    
                    return (card_name, (play_x, play_y), most_dangerous)
    
        return None
    

if __name__ == "__main__":
    current_hand = {
    "Bandit": {
        "rect": (215, 929, 69, 73),
        "score": 0.7785,
        "last_seen": 1773327128.7904
    },
    "PEKKA": {
        "rect": (118, 922, 71, 89),
        "score": 0.8169,
        "last_seen": 1773327128.7904
    },
    "RoyalGhost": {
        "rect": (120, 916, 68, 70),
        "score": 0.7889,
        "last_seen": 1773327109.5059
    },
    "MagicArcher": {
        "rect": (120, 915, 70, 75),
        "score": 0.7566,
        "last_seen": 1773327094.8958
    }
}
    deck = ["Fireball", "PEKKA", "Bandit", "BattleRam",
              "RoyalGhost", "Zap", "MagicArcher", "ElectroWizard",
              "GoldenKnight", "Poison"]
    bot_logic = BotLogic(deck)
    # print(bot_logic.counter_chart)
    # print(bot_logic.card_info)
    
    elixir_stat = {}
    for card in bot_logic.data["cards"]:
        if card in current_hand:
            elixir_stat[f"{card}"] = bot_logic.data["cards"][f"{card}"]["elixir"]
    print(elixir_stat)
    