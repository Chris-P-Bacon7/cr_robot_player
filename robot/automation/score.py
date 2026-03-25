import easyocr
import os
import json
import cv2
import re

class Score:
    def __init__(self, json_name, json_location):
        self.json_name = json_name
        self.json_location = json_location
        self.config = self.load_json_config(json_location, json_name)

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

    def tower_state(self, frame):
        health_data = {}

        if not self.config:
            return health_data
        
        for key, roi in self.config.items():
            if "_health" in key:
                x1, y1, x2, y2 = roi
                
                cropped = frame[y1:y2, x1:x2]

                scaled = cv2.resize(cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

                gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
                _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

                inverted = cv2.bitwise_not(binary)

                result = self.reader.readtext(inverted, allowlist='0123456789')

                if len(result) > 0:
                    raw_text = result[0][1]
                    clean_number = re.sub(r'\D', '', raw_text)

                    if clean_number:
                        health_data[key] = int(clean_number)
                    else:
                        health_data[key] = None
                    
                else:
                    health_data[key] = None
        return health_data