import cv2
import numpy as np
import keyboard
import time
import json
import os
import threading 
from window_capture import WindowCapture 
from controls import GameController
from card_vision import CardVision

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

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
    card_vision = CardVision()

    # Initialization
    card_keys = ["1", "2", "3", "4"]
    pos_map = {}
    pos_keys = []

    if "location" in raw_json:
        for name, data in raw_json["location"].items():
            if len(data) >= 3:
                tile_x, tile_y, trigger_key = data
                pos_map[trigger_key] = (tile_x, tile_y)
                pos_keys.append(trigger_key)
    
    selected_card = None
    bot_state = {"is_acting": False}

    print(f"Configuration Loaded.")
    print(f"Card Keys: {card_keys}")
    print(f"Pos keys: {pos_keys}")

    card_vision.load_template("Fireball", r"Robot\assets\cards", 0)
    
    while True:
        loop_start = time.time()
        
        # --- VISION ---
        frame = cap.get_screenshot()
        if frame is None:
            time.sleep(1)
            continue

        # <--- KEY CHANGE: DRAWING GRID AT CENTERS --->
        # Draw Vertical Lines (Centers)
        for x in range(arena_width):
            # x + 0.5 is the center of the tile
            center_x = x + 0.5
            p1 = mapper.tile_to_pixel(center_x, 0)
            p2 = mapper.tile_to_pixel(center_x, arena_height)
            cv2.line(frame, p1, p2, (255, 255, 255), 1, cv2.LINE_AA) 

        # Draw Horizontal Lines (Centers)
        for y in range(arena_height):
            center_y = y + 0.5
            p1 = mapper.tile_to_pixel(0, center_y)
            p2 = mapper.tile_to_pixel(arena_width, center_y)
            cv2.line(frame, p1, p2, (255, 255, 255), 1, cv2.LINE_AA)

        # Draw Numbers (At Centers)
        for x in range(0, arena_width, 2):
            px, py = mapper.tile_to_pixel(x + 0.5, arena_height)
            location = (px - 6, py - 8)
            cv2.putText(frame, str(x), location, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(frame, str(x), location, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

        for y in range(0, arena_height, 2):
            px, py = mapper.tile_to_pixel(0, y + 0.5)
            location = (px + 5, py + 5)
            cv2.putText(frame, str(y), location, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(frame, str(y), location, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

        # Draw Card Slots
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
        
        fps = int(1 / (time.time() - loop_start + 0.001))
        cv2.putText(frame, f"FPS: {fps}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if bot_state["is_acting"]:
             cv2.putText(frame, "BUSY", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

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
            elif not bot_state["is_acting"]:
                # <--- KEY CHANGE: OFFSET TARGET TO TILE CENTER --->
                raw_x, raw_y = pos_map[pressed_pos]
                # Adding 0.5 ensures we click the visual center of the tile
                target_loc = (raw_x + 0.5, raw_y + 0.5)
                
                print(f"Playing {selected_card} at {(raw_x, raw_y)}")

                def action_task(card, loc):
                    bot_state["is_acting"] = True
                    try:
                        bot_controls.play_card(f"card_{card}", loc, screen_config, mapper)
                    except Exception as e:
                        print(f"Action Failed: {e}")
                    bot_state["is_acting"] = False

                t = threading.Thread(target=action_task, args=(selected_card, target_loc))
                t.start()
                
                selected_card = None
                time.sleep(0.15)
    
    cv2.destroyAllWindows()