import cv2
import numpy as np
import keyboard
import time
import json
import os
from window_capture import WindowCapture 
from controls import GameController 

# ================= CONFIGURATION =================
arena_width = 18
arena_height = 30
phone_name = "SM-S936W" 

def load_json_config():
    if not os.path.exists("bot_config.json"):
        print("❌ Error: 'bot_config.json' not found.")
        return None
    with open("bot_config.json", "r") as f:
        return json.load(f)

def load_config():
    """Flattens nested JSON for the bot logic"""
    if not os.path.exists("bot_config.json"):
        print("❌ Error: 'bot_config.json' not found!")
        exit()
        
    with open("bot_config.json", "r") as f:
        data = json.load(f)
        
    config = {}
    for k, v in data["arena"].items(): config[f"arena_{k}"] = tuple(v)
    for k, v in data["card_slots"].items(): config[k] = tuple(v)
    for k, v in data["elixir"].items(): config[f"elixir_{k}"] = tuple(v)
    return config

def get_active_key(valid_keys):
    for key in valid_keys:
        if keyboard.is_pressed(key):
            return key
    return None

class ScreenMapper:
    def __init__(self, config):
        self.src_points = np.float32([[0, 0], [arena_width, 0], [0, arena_height], [arena_width, arena_height]])
        self.dst_points = np.float32([
            config["arena_top_left"], config["arena_top_right"], 
            config["arena_bottom_left"], config["arena_bottom_right"]
        ])
        self.matrix = cv2.getPerspectiveTransform(self.src_points, self.dst_points)

    def tile_to_pixel(self, tile_x, tile_y):
        point = np.array([[[tile_x, tile_y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, self.matrix)
        return (int(transformed[0][0][0]), int(transformed[0][0][1]))


# ================= MAIN LOOP =================
if __name__ == "__main__":
    screen_config = load_config()
    raw_json = load_json_config()

    cap = WindowCapture(phone_name)
    mapper = ScreenMapper(screen_config)
    bot_controls = GameController(cap)

    # Initialization
    card_keys = ["1", "2", "3", "4"]
    pos_map = {}
    pos_keys = []

    if "location" in raw_json:
        for name, data in raw_json["location"].items():
            tile_x, tile_y, trigger_key = data
            pos_map[trigger_key] = (tile_x, tile_y)
            pos_keys.append(trigger_key)
    
    selected_card = None

    print(f"Configuration Loaded.")
    print("Card Keys: {card_keys}")
    print("Pos keys: {pos_keys}")
    print("Press 1-4, then press a Pos key to place the card.")
    
    while True:
        loop_start = time.time()
        
        # --- VISION ---
        frame = cap.get_screenshot()
        if frame is None:
            time.sleep(1)
            continue

        # 1. Draw Grid Lines (Faint White)
        for x in range(arena_width + 1):
            p1 = mapper.tile_to_pixel(x, 0)
            p2 = mapper.tile_to_pixel(x, arena_height)
            cv2.line(frame, p1, p2, (255, 255, 255), 1) 

        for y in range(arena_height + 1):
            p1 = mapper.tile_to_pixel(0, y)
            p2 = mapper.tile_to_pixel(arena_width, y)
            cv2.line(frame, p1, p2, (255, 255, 255), 1)

        # 2. Draw Numbers (High Visibility Mode)
        
        # X-Axis (Bottom Edge)
        for x in range(0, arena_width + 1, 2):
            px, py = mapper.tile_to_pixel(x, arena_height)
            # Draw slightly ABOVE the bottom line (py - 8) so it doesn't get cut off
            location = (px - 6, py - 8)
            
            # Black Outline (Thickness 3)
            cv2.putText(frame, str(x), location, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
            # Cyan Text (Thickness 1)
            cv2.putText(frame, str(x), location, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Y-Axis (Left Edge)
        for y in range(0, arena_height + 1, 2):
            px, py = mapper.tile_to_pixel(0, y)
            # Draw slightly to the RIGHT of the edge (px + 5)
            location = (px + 5, py + 5)
            
            # Black Outline
            cv2.putText(frame, str(y), location, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
            # Cyan Text
            cv2.putText(frame, str(y), location, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 3. Draw Card Slots
        for i in range(1, 5):
            key_str = str(i)
            if f"card_{i}" in screen_config:
                cx, cy = screen_config[f"card_{i}"]
                
                color = (0, 255, 255) 
                thickness = 2
                
                if selected_card == key_str:
                    color = (0, 255, 0)
                    thickness = -1 
                    
                cv2.circle(frame, (cx, cy), 10, color, thickness)
        
        # 4. FPS
        fps = int(1 / (time.time() - loop_start + 0.001))
        cv2.putText(frame, f"FPS: {fps}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("High Speed Vision", frame)
        if cv2.waitKey(1) == ord('q'): break

        # ----- Controls Logic ------
        pressed_card = get_active_key(card_keys)
        if pressed_card:
            selected_card = pressed_card
            print(f"Card {selected_card} SELECTED! Waiting for position...")
            time.sleep(0.15)
        
        pressed_pos = get_active_key(pos_keys)
        if pressed_pos:
            if selected_card is None:
                print("NO CARD SELECTED. Press 1-4 first.")
                time.sleep(0.15)
                pressed_pos = None
            else:
                target_loc = pos_map[pressed_pos]
                print(f"Playing {selected_card} at {pressed_pos} {target_loc}")

                try:
                    bot_controls.play_card(f"card_{selected_card}", target_loc, screen_config, mapper)
                except Exception as e:
                    print(f"Action Failed: {e}")
                
                selected_card = None
                time.sleep(0.15)
    cv2.destroyAllWindows