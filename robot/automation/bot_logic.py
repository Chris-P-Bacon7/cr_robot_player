import os
import sys
import random as rand

# Tell Python to look one folder up for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from perception.screen_mapper import ScreenMapper

class BotLogic:
    def __init__(self, cur_deck, arena_height=30, arena_width=18):
        self.arena_height = arena_height
        self.arena_width = arena_width
        self.crossed_bridge = arena_height * 0.45
        self.speed_multiplier = 0.02

        self.json_name = "card_database.json"
        self.json_location = f"robot\\{self.json_name}"
        self.deck = cur_deck

        self.data = self.load_json(self.json_location, self.json_name)
        self.counter_chart = self.config_json(self.data, "counters", cur_deck)
        self.card_info = self.config_json(self.data, "cards", cur_deck)
        self.screen_mapper = ScreenMapper(self.load_config("robot\\Chris_S25.json", "Chris_S25.json"), 30, 18)

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
        
    def analyze_threats(self, detections, names_map):
        threats = []
        for box in detections:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])

            if cls_id not in names_map: continue
            raw_name = names_map[cls_id]
            if "-" not in raw_name: continue

            team, troop = raw_name.split("-", 1)
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            tile_x, tile_y = self.screen_mapper.pixel_to_tile(cx, cy)

            if team == "Enemy" and troop not in ("PrincessTower", "KingTower"):
                if tile_y > self.crossed_bridge:
                    threats.append({"Troop": troop, "x": cx, "y": cy, 
                                    "tile_x": tile_x, "tile_y": tile_y, "conf": conf})
            
            threats.sort(key=lambda t: t["tile_y"], reverse=True)
        return threats
    
    def get_defensive_move(self, threats, available_cards, current_elixir):
        most_dangerous = threats[0]
        enemy_name = most_dangerous["Troop"]

        if enemy_name not in self.counter_chart:
            print(f"LOGIC WARNING: No defined counter for {enemy_name}.")
            return None
        
        primary_counters = []
        primary_counters.extend(self.counter_chart[enemy_name].get("primary", []))
        primary_counters.extend(self.counter_chart[enemy_name].get("spell", []))
        primary_counters.extend(self.counter_chart[enemy_name].get("secondary", []))

        for card_name in primary_counters:
            if card_name in available_cards:
                cost = self.card_info[card_name]["elixir"]
                card_class = self.card_info[card_name].get("class", "troop")

                # Check if enemy is an air troop
                enemy_data_full = self.data["cards"].get(enemy_name, {})

                latency_compensation = 0.75
                if current_elixir >= cost:
                    enemy_x, enemy_y = most_dangerous["tile_x"], most_dangerous["tile_y"]

                    if "ability" in enemy_data_full and "air" in enemy_data_full["ability"]:
                        enemy_y += 2.0

                    if "spell" in card_class.lower():
                        raw_speed_unit = self.card_info[card_name].get("speed", 800)
                        tiles_per_sec = raw_speed_unit * 0.02
                        king_x, king_y = 9.0, 28.0

                        distance = ((enemy_x - king_x) **2 + (enemy_y - king_y) ** 2) ** 0.5
                        flight_time = distance / tiles_per_sec

                        total_spell_latency = 1 + flight_time

                        play_x = enemy_x
                        play_y = enemy_y + total_spell_latency
                    else:
                        offset = self.card_info[card_name]["placement_offset"]

                        if enemy_x >= 9: play_x = enemy_x - (0.5 * offset ** 2) ** 0.5
                        else: play_x = enemy_x + (0.5 * offset ** 2) ** 0.5

                        play_y = enemy_y + (0.5 * offset ** 2) ** 0.5 + latency_compensation
                        
                    play_x = max(0, min(play_x, self.arena_width))
                    play_y = max(0, min(play_y, self.arena_height))

                    pixel_x, pixel_y = self.screen_mapper.tile_to_pixel(play_x, play_y)
                    return (card_name, (pixel_x, pixel_y), most_dangerous)
        return None
    
    def get_offensive_move(self, available_cards, current_elixir):
        """ 
        IMPROVEMENTS NEEDED:
        Check to make sure that the arena conditions are favourable
        before initiating an offensive decision 
        """
        if current_elixir < 9:
            return None
        
        for card_name in available_cards:
            card_class = self.card_info[card_name].get("class", "").lower()
            cost = self.card_info[card_name]["elixir"]

            if card_class == "wincon" and current_elixir >= cost:
                lane_x = rand.choice([3, 15])
                pixel_x, pixel_y = self.screen_mapper.tile_to_pixel(lane_x, 14)

                fake_enemy_data = {"Troop": "Offensive Push", "x": pixel_x, "y": pixel_y}
                return (card_name, (pixel_x, pixel_y), fake_enemy_data)
        
        for card_name in available_cards:
            card_class = self.card_info[card_name].get("class", "").lower()
            if card_class != "tank" and "spell" not in card_class:
                lane_x = 9
                pixel_x, pixel_y = self.screen_mapper.tile_to_pixel(lane_x, 28)
                
                return (card_name, (pixel_x, pixel_y), {"Troop": "Cycle Tank in Back", "x": pixel_x, "y": pixel_y})

        return None

    def get_best_move(self, detections, current_hand, current_elixir, names_map):
        """
        Main brain function.

        Args:
            detections: List of YOLO "box" objects
            current_hand: List of card names currently available
            current_elixir: Integer
        """
        available_cards = [card[0] for card in current_hand]

        threats = self.analyze_threats(detections, names_map)

        if threats and threats[0]["tile_y"] <= 20:
            move = self.get_defensive_move(threats, available_cards, current_elixir)
            if move: return move
        elif not threats or threats[0]["tile_y"] > 20:
            move = self.get_offensive_move(available_cards, current_elixir)
            if move: return move
        
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
    