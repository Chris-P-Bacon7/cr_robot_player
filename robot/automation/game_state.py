from ultralytics import YOLO
import easyocr
import os
import json
import cv2
import re

class GameState:
    def __init__(self, json_name, json_location, model_path="runs\\detect\\train2\\weights\\best.pt"):
        self.json_name = json_name
        self.json_location = json_location
        self.config = self.load_json_config(json_location, json_name)

        self.model = YOLO(model_path)
        self.names = self.model.names

        print("Loading OCR for Tower Health Detection...")
        self.reader = easyocr.Reader(['en'])
        print("OCR Ready.")

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

                # 1. Upscale and Grayscale
                scaled = cv2.resize(cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)

                # 2. THE FIX: Dynamic Otsu Thresholding (Replaces the 200!)
                _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                inverted = cv2.bitwise_not(binary)

                # 3. THE CAMERA: Save exactly what the bot sees to your project folder!
                cv2.imwrite(f"debug_ocr_{key}.png", inverted)

                # 4. Read the text
                result = self.reader.readtext(inverted, allowlist='0123456789')

                # 1. Collect every single number EasyOCR found in the box
                valid_numbers = []
                for (bbox, text, prob) in result:
                    clean_number = re.sub(r'\D', '', text)
                    if clean_number:
                        valid_numbers.append(int(clean_number))

                # 2. Filter the Shield Level from the actual Tower Health
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
                
                if valid_numbers:
                    if len(valid_numbers) == 1 and valid_numbers[0] <= 15:
                        health_data[key] = None
                    else:
                        health_data[key] = max(valid_numbers)
                else:
                    health_data[key] = None

        return health_data, inverted
    