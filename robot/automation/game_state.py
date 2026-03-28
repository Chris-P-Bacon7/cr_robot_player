from ultralytics import YOLO
import easyocr
import os
import json
import cv2
import re

class GameState:
    def __init__(self, device_json_name, device_json_location, db_json_name, db_json_location, 
                 screen_mapper, model_path="runs\\detect\\train7\\weights\\best.pt"): 
        self.config = self.load_json_config(device_json_location, device_json_name)
        
        self.data = self.load_json(db_json_location, db_json_name)
        
        self.screen_mapper = screen_mapper

        self.model = YOLO(model_path)
        self.names = self.model.names

        print("Loading OCR for Tower Health Detection...")
        self.reader = easyocr.Reader(['en'])
        print("OCR Ready.")
    
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
    
    def load_json_config(self, json_location, json_name):
        if not os.path.exists(json_location):
            print(f"ERROR: \"{json_name}\" not found.")
            return None
        with open(json_location, "r") as f:
            data = json.load(f)

            config = {}
            
            for k, v in data["arena"].items(): config[f"arena_{k}"] = tuple(v)
            for k, v in data["tower_health"].items(): config[f"{k}_health"] = tuple(v)

            return config
    
    def tower_detection(self, detections):
        player_princess_count = 0
        enemy_princess_count = 0

        for detection in detections:
            boxes = detection.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                cls_id = int(box.cls[0])
                cls_name = self.names[cls_id]
                conf = float(box.conf[0])

                if "PrincessTower" in cls_name:
                    if "Player" in cls_name: player_princess_count += 1
                    if "Enemy" in cls_name: enemy_princess_count += 1

        return player_princess_count, enemy_princess_count                

    def tower_state(self, frame):
        health_data = {}

        if not self.config:
            return health_data
        
        for key, roi in self.config.items():
            if "_health" in key:
                x1, y1, x2, y2 = roi
                
                cropped = frame[y1:y2, x1:x2]

                # Upscale and Grayscale
                scaled = cv2.resize(cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)

                # Dynamic Otsu Thresholding (Replaces the 200!)
                _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                inverted = cv2.bitwise_not(binary)

                # Read the text
                result = self.reader.readtext(inverted, allowlist='0123456789')

                # 1. Collect every single number EasyOCR found in the box
                valid_numbers = []
                for (bbox, text, prob) in result:
                    clean_number = re.sub(r'\D', '', text)
                    if clean_number:
                        valid_numbers.append(int(clean_number))

                # Filter the Shield Level from the actual Tower Health
                if valid_numbers:
                    # If it ONLY found a number 15 or lower, it's just the shield. 
                    # The health is hidden (King Tower is asleep!)
                    if len(valid_numbers) == 1 and valid_numbers[0] <= 15:
                        health_data[key] = None
                    else:
                        # If it found multiple numbers (e.g., [15, 4424]), 
                        # the actual health will always be the highest number!
                        health_data[key] = max(valid_numbers)
                else:
                    health_data[key] = None

                valid_numbers = [] # Collect all valid numbres
                for (bbox, text, prob) in result:
                    clean_number = re.sub(r'\D', '', text)
                    if clean_number: valid_numbers.append(int(clean_number))

        return health_data, inverted
        
    def detect_threats(self, detections, names_map):
        threats = []
        for box in detections:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])

            if cls_id not in names_map: continue
            raw_name = names_map[cls_id]
            if "-" not in raw_name: continue

            name_parts = raw_name.split("-")
            team = name_parts[0]
            troop = name_parts[1]

            # Grab everything from index 2 onwards. If it doesn't exist, it safely returns an empty list []
            state = name_parts[2:] if len(name_parts) > 2 else None

            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            tile_x, tile_y = self.screen_mapper.pixel_to_tile(cx, cy)

            if team == "Enemy" and troop not in ("PrincessTower", "KingTower"):
                threats.append({"Troop": troop, "x": cx, "y": cy, 
                                "tile_x": tile_x, "tile_y": tile_y, "conf": conf, "state": state})
            
            threats.sort(key=lambda t: t["tile_y"], reverse=True)
        return threats

    def evaluate_threats(self, threats):
        if not threats:
            return []
        
        final_evaluation = []

        tower_y = 24.0

        w_urgency = 1.5
        w_power = 2.0
        
        for threat in threats:
            enemy_name = threat["Troop"]
            enemy_data = self.data["cards"].get(enemy_name, {})

            # 1. Calculate urgency
            speed_unit = enemy_data.get("speed", 60)
            tiles_per_sec = speed_unit * 0.02

            distance = max(tower_y - threat["tile_y"], 0)
            eta = distance / tiles_per_sec

            urgency_eval = 10.0 / (eta + 1.0)

            # 2. Calculate importance
            elixir = enemy_data.get("elixir", 3)
            card_class = enemy_data.get("class", "").lower()

            if card_class == "wincon":
                class_multiplier = 2.0
            elif card_class == "tank":
                class_multiplier = 1.5
            elif card_class == "mini":
                class_multiplier = 0.25
            else:
                class_multiplier = 1.0
            
            power_eval = elixir * class_multiplier

            # 3. Apply weights
            evaluation = (w_urgency * urgency_eval) + (w_power * power_eval)

            threat["threat_score"] = evaluation
            threat["eta"] = eta
            
            final_evaluation.append(threat)

        final_evaluation.sort(key=lambda t: t["threat_score"], reverse=True)

        return final_evaluation
    