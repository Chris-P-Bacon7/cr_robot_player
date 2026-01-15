import cv2
import numpy as np
import keyboard
import time
import json
import os
import threading
import random as rand
from concurrent.futures import ThreadPoolExecutor
from window_capture import WindowCapture 
from controls import GameController
from card_vision import CardVision
from elixir_tracker import ElixirTracker

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

# ================= CONFIGURATION =================
arena_width = 18
arena_height = 30
phones = {
    # "Riley": "SM-A536W",
    "riley": "SM-S936W",
    "chris": "SM-S936W"}
decks = {
    "riley": ["Fireball", "Bats", "SkeletonArmy", "Valkyrie", "Tesla", 
              "Musketeer_Hero", "Log", "HogRider"],
    "chris": ["Fireball", "PEKKA", "Bandit", "BattleRam",
              "RoyalGhost", "Zap", "MagicArcher", "ElectroWizard"]
}

def initialize_user(user):
    global phone_name
    global deck

    phone_name = phones[user]
    deck = decks[user]

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

def vision_worker(vision_obj, img, card_name):
    # Helper to run vision on a separate thread
    return card_name, vision_obj.find(img, card_name, threshold=0.750)

# ================= MAIN LOOP =================
if __name__ == "__main__":
    user = input("Enter your name (Riley/Chris): ").lower()
    time.sleep(0.5)
    print(f"Welcome, {user.capitalize()}!")
    time.sleep(0.75)

    if user in phones:
        initialize_user(user)
    else:
        print(f"{user.capitalize()}?")
        time.sleep(1.5)
        print(f"What kind of name is that?")
        time.sleep(1.5)
        print("Get the hell off of my program >:(")
        time.sleep(1.5)
        print(f"CRITICAL ERROR DETECTED -> Please see traceback: \n\
              UserError: The program has terminated due to an ineligible user '{user.capitalize()}'.")
        exit()
        
    screen_config = load_config()
    raw_json = load_json_config()

    cap = WindowCapture(phone_name)
    mapper = ScreenMapper(screen_config)
    bot_controls = GameController(cap)
    card_vision = CardVision()
    elixir_tracker = ElixirTracker(screen_config)

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

    for card in deck:
        card_vision.load_template(card, "Robot\\assets\\cards", 0)
        
    cv2.namedWindow("Bot Vision", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Bot Vision", 450, 954) # Opens window at the same ratio as scrcpy
    cv2.setWindowProperty("Bot Vision", cv2.WND_PROP_TOPMOST, 0) # Makes window stay always on top (disabled)
    
    # <--- OPTIMIZATION: OPEN THREAD POOL ONCE HERE --->
    with ThreadPoolExecutor(max_workers=len(deck)) as executor:
        
        while True:
            loop_start = time.time()
            
            # --- VISION ---
            try:
                frame = cap.get_screenshot()
            except Exception as e:
                print(f"Your scrcpy window was not open: {e}")
                break
            if frame is None:
                time.sleep(1)
                continue

            # --- ELIXIR TRACKING ---
            # 1. Get current Elixir
            current_elixir = elixir_tracker.get_elixir(frame)

            # --- CARD RECOGNITION (OPTIMIZED) ---
            # 1. Define Region of Interest (Bottom 40% of screen)
            h_frame, w_frame = frame.shape[:2]
            roi_top = int(h_frame * 0.86) 
            
            # Create a view of just the hand area
            hand_view = frame[roi_top:h_frame, 0:w_frame]

            # 2. Submit ALL tasks first (Parallel execution)
            futures = []
            for card_name in deck:
                futures.append(executor.submit(vision_worker, card_vision, hand_view, card_name))

            # 3. Collect Results
            for future in futures:
                card_name, matches = future.result()
                
                for ((x, y, w, h), score) in matches:
                    # <--- TRANSLATE COORDINATES BACK TO FULL SCREEN --->
                    real_y = y + roi_top

                    # Draw the box
                    cv2.rectangle(frame, (x, real_y), (x + w, real_y + h), (0, 255, 0), 2)

                    # Draw the Label and the Score
                    label = f"{card_name} {score:.3f}"
                    cv2.putText(frame, label, (x, real_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                                0.5, (0, 255, 0), 2)

            # --- DRAWING ON BOT VISION ---
            
            # Drawing Current Elixir
            cv2.putText(frame, f"Elixir: {current_elixir}", (10, 800),
                        cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1, (210, 60, 210), 2, cv2.LINE_4)
            # cv2.circle(frame, (screen_config["elixir_top_left"][0], 
            #                    screen_config["elixir_top_left"][1]), 3, (0, 0, 0))

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
                    colour = (0, 255, 255) 
                    thickness = 2
                    if selected_card == key_str:
                        colour = (0, 255, 0)
                        thickness = -1 
                    cv2.circle(frame, (cx, cy), 10, colour, thickness)
            
            fps = int(1 / (time.time() - loop_start + 0.001))
            cv2.putText(frame, f"FPS: {fps}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if bot_state["is_acting"]:
                cv2.putText(frame, "BUSY", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow("Bot Vision", frame)
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
                    
                    target_x = int(raw_x + 0.5) 
                    target_y = int(raw_y + 0.5) 
                    
                    # Draw a red dot at the target 
                    cv2.circle(frame, (target_x, target_y), 5, (0, 0, 255), -1)
                    
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