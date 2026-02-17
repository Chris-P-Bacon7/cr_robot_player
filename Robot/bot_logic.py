
counter_chart = {
    # This will be the default defending & counterpushing strategy for the bot
    # Format: "EnemyTroop": [[Primary counters], [Secondary counters], [Spell if close to tower (optional)]]
    "Giant": [["Pekka"], ["ElectroWizard", "Bandit", "RoyalGhost"]],
    "Night_Witch": [["MagicArcher", "RoyalGhost"], ["Bandit", "ElectroWizard"]],
    "Firecracker": [["RoyalGhost", "Bandit"], 
                    ["MagicArcher", "ElectroWizard"], ["Fireball"]],
    "DarkPrince": [["Bandit", "ElectroWizard"], ["Pekka", "RoyalGhost"]],
    "ElectroWizard": [["Bandit", "RoyalGhost"], 
                      ["ElectroWizard", "MagicArcher"], ["Fireball"]],
    "Balloon": [["ElectroWizard", "MagicArcher"], ["Fireball"]],
    "Bat": [["MagicArcher", "Electrowizard"], ["Zap"]]
}

elixir_stat = {
    "Pekka": 7,
    "ElectroWizard": 4,
    "Bandit": 3,
    "RoyalGhost": 3,
    "MagicArcher": 4,
    "BattleRam": 4,
    "Fireball": 4,
    "Zap": 2
}

class BotLogic:
    def __init__(self, arena_height=900, arena_width=450):
        self.arena_height = arena_height
        self.arena_width = arena_width
        self.crossed_bridge = arena_height * 0.45
    
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

            if team == "Enemy" and troop not in ("PrincessTower", "KingTower"):
                if cy > self.crossed_bridge:
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
        if enemy_name not in counter_chart: # Make sure we have a counter
            print(f"LOGIC WARNING: No defined counter for {enemy_name}.")
            return None

        counter_options = counter_chart[enemy_name][0]
        available_cards = [card[0] for card in current_hand]
        
        for card_name in counter_options:
            if card_name in available_cards:
                cost = elixir_stat.get(card_name, 11)
                
                if current_elixir >= cost:
                    play_x = most_dangerous["x"]
                    play_y = most_dangerous["y"]

                    return (card_name, (play_x, play_y))
        
        return None