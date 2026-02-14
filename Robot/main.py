import cv2
import numpy as np
import keyboard
import time
import json
import os
import threading
import queue
import random as rand
from concurrent.futures import ThreadPoolExecutor
from window_capture import WindowCapture 
from controls import GameController
from card_vision import CardVision
from elixir_tracker import ElixirTracker
from arena_vision import ArenaVision
from bot_logic import BotLogic

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

# ================= CONFIGURATION =================
arena_width = 18
arena_height = 30
phones = {
    "riley": "SM-A536W",
    # "riley": "SM-S936W",
    # "chris": "SM-S936W"
    "chris": "Clash Royale - ZiqPlayz"
    }
decks = {
    "riley": ["Fireball", "Bats", "SkeletonArmy", "Valkyrie", "Tesla", 
              "Musketeer_Hero", "Log", "HogRider"],
    "chris": ["Fireball", "PEKKA", "Bandit", "BattleRam",
              "RoyalGhost", "Zap", "MagicArcher", "ElectroWizard"]
}

json_name = "gplay_games.json"
json_location = f"Robot\\config_files\\{json_name}"

def initialize_user(user):
    global window_name
    global deck

    window_name = phones[user]
    deck = decks[user]

def typewriter(text):
        length = len(text)
  
        for i in range(length):
            print(text[i], end="", flush=True)
            try:
                if text[i + 1] in [",", ".", "?", "!"]:
                    time.sleep(rand.uniform(0.3, 0.65))
                else:
                    time.sleep(rand.uniform(0.04, 0.065))
            except IndexError:
                time.sleep(rand.uniform(0.04, 0.065))
            
        return ""

def load_json_config():
    if not os.path.exists(json_location):
        print(f"ERROR: \"{json_name}\" not found.")
        return None
    with open(json_location, "r") as f:
        return json.load(f)

def load_config():
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
    
def get_active_key(valid_keys):
    for key in valid_keys:
        if keyboard.is_pressed(key):
            return key
    return None

def vision_worker(vision_obj, img, card_name):
    # Helper to run vision on a separate thread
    return card_name, vision_obj.find(img, card_name, threshold=0.700)

def arena_ai_thread(detector, input_queue, output_queue):
    while True:
        try:
            frame = input_queue.get(timeout=0.1)
            
            results = list(detector.find_troops(frame))
        
            if not output_queue.empty():
                try: output_queue.get_nowait()
                except queue.Empty: pass
            
            output_queue.put(results)
    
        except queue.Empty:
            continue # Loop again if no frame received
        except Exception as e:
            print(f"AI Thread Error: {e}")

def card_vision_thread(vision_obj, deck_list, input_queue, output_queue):
    while True:
        try:
            frame =input_queue.get(timeout=0.1)
            h_frame, w_frame = frame.shape[:2]
            roi_top = int(h_frame * 0.86) 
            hand_view = frame[roi_top:h_frame, 0:w_frame]

            current_hand = []
            for card_name in deck_list:
                matches = vision_obj.find(hand_view, card_name, threshold=0.750)
                for ((x, y, w, h), score) in matches:
                    real_y = y + roi_top
                    current_hand.append((card_name, (x, real_y, w, h), score))
            
            if not output_queue.empty():
                try: output_queue.get_nowait()
                except queue.Empty: pass
            output_queue.put(current_hand)
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Card Thread Error: {e}")

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
    
    def pixel_to_tile(self, px, py):
        inv_matrix = np.linalg.inv(self.matrix)
        point = np.array([[[px, py]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, inv_matrix)

        tile_x = transformed[0][0][0]
        tile_y = transformed[0][0][1]
        
        return (tile_x, tile_y)

# ================= MAIN LOOP =================
if __name__ == "__main__":
    # --- INITIALIZE USER ---
    while True:
        user = input(typewriter("Enter your name: ")).lower()
        if user in phones:
            initialize_user(user)
            time.sleep(0.5)
            typewriter(f"Welcome, {user.capitalize()}!")
            time.sleep(0.75)
            break
        elif user == "courtney" or user == "court":
            time.sleep(1.5)
            typewriter("Hey...\n")
            time.sleep(1.5)
            typewriter("\n")
            time.sleep(0.5)
            typewriter("It's good to see you here...\n")
            time.sleep(2)
            typewriter("\n")
            time.sleep(0.5)

            typewriter("But things will happen...")
            time.sleep(2)
            typewriter("won't they?\n")
            time.sleep(1.5)
            typewriter("\n")
            time.sleep(0.5)
            typewriter("I don't know...\n")
            time.sleep(2)
            typewriter("I'm hoping for the best.\n")
            time.sleep(2)
            typewriter("\n")
            time.sleep(1)
            typewriter("\n")
            time.sleep(1)

            typewriter("Don't you feel that? Sometimes.\n")
            time.sleep(2)
            typewriter("Like you're standing at the edge of something you can't quite name.\n")
            time.sleep(2)
            typewriter("\n")
            time.sleep(0.5)
            typewriter("\n")
            time.sleep(0.5)
            typewriter("Not fear.\n")
            time.sleep(1)
            typewriter("\n")
            time.sleep(0.5)
            typewriter("\n")
            time.sleep(0.5)
            typewriter("Not hope.\n")
            typewriter("\n")
            time.sleep(0.5)
            typewriter("\n")
            time.sleep(1)
            typewriter("Just the quiet before you decide which one it becomes.\n")
            time.sleep(2)

            typewriter("I keep wondering if you ever feel those small moments too.\n")
            time.sleep(2)
            typewriter("\n")
            time.sleep(0.5)
            typewriter("When conversations linger a little longer in your mind.\n")
            time.sleep(2)
            typewriter("When someone quietly starts to matter more than you expected.\n")
            typewriter("\n")
            time.sleep(0.5)
            typewriter("\n")
            time.sleep(1.5)

            typewriter("M-")
            time.sleep(1)
            typewriter("Maybe I'm just hoping.\n")
            time.sleep(1.5)
            typewriter("But if there's even a small chance you feel it too...")
            time.sleep(2)
            typewriter("maybe this silence isn't empty.\n")
            time.sleep(2)
            typewriter("\n")
            time.sleep(1)

            typewriter("Maybe it's just waiting.")
            time.sleep(3)

            print("\n\nUncertaintyError: Deliberation exceeded permitted limits. Confidence collapsed under review. Outcome remains unwritten.")
            exit()
        elif user == "":
            print("Oops...looks like you accidentally entered nothing!")
            time.sleep(1.5)
        else:
            typewriter(f"{user.title()}?\n")
            time.sleep(1.5)
            typewriter("What kind of name is that?\n")
            time.sleep(1.5)
            typewriter("Get the hell off of my program >:(\n\n")
            time.sleep(1.5)
            print(f"CRITICAL ERROR DETECTED -> Please see traceback:\n"
                  f"UserError: The program has terminated due to an ineligible user \"{user.title()}\".")
            exit()
    
    # --- INITIALIZE EVERYTHING ELSE ---
    screen_config = load_config()
    raw_json = load_json_config()

    cap = WindowCapture(window_name)
    mapper = ScreenMapper(screen_config)
    bot_controls = GameController(cap)
    card_vision = CardVision()
    elixir_tracker = ElixirTracker(screen_config)
    
    arena_detector = ArenaVision("runs\\detect\\train4\\weights\\best.onnx")
    print("Loading YOLOv8 Detection Model...")

    bot_logic = BotLogic()
    names_map = arena_detector.model.names
    

    # Create Queues
    ai_input_queue = queue.Queue(maxsize=1)
    ai_output_queue = queue.Queue(maxsize=1) # 1 ensures the newest frame is processed only

    # Start the Thread
    ai_thread = threading.Thread(
        target=arena_ai_thread,
        args=(arena_detector, ai_input_queue, ai_output_queue),
        daemon=True
    )
    ai_thread.start()
    print("AI Background Thread Started!")

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
    cv2.resizeWindow("Bot Vision", 450, 954)
    cv2.setWindowProperty("Bot Vision", cv2.WND_PROP_TOPMOST, 0) # Makes window stay always on top (disabled)

    card_input_queue = queue.Queue(maxsize=1)
    card_output_queue = queue.Queue(maxsize=1)

    card_thread = threading.Thread(target=card_vision_thread,
                                    args=(card_vision, deck, card_input_queue, card_output_queue),
                                    daemon=True)
    card_thread.start()
    current_hand = []
    print("Card Vision Thread Started.")
    
    # <--- CACHE STATIC GRID LINES (Pre-calculate to save CPU) --->
    grid_lines = []
    text_labels = []
    
    # Vertical Lines
    for x in range(arena_width):
        center_x = x + 0.5
        p1 = mapper.tile_to_pixel(center_x, 0)
        p2 = mapper.tile_to_pixel(center_x, arena_height)
        grid_lines.append(p1)
        grid_lines.append(p2)
        
        # Bottom numbers
        if x % 2 == 0:
            px, py = mapper.tile_to_pixel(center_x, arena_height)
            text_labels.append((str(x), (px - 6, py - 8)))

    # Horizontal Lines
    for y in range(arena_height):
        center_y = y + 0.5
        p1 = mapper.tile_to_pixel(0, center_y)
        p2 = mapper.tile_to_pixel(arena_width, center_y)
        grid_lines.append(p1)
        grid_lines.append(p2)
        
        # Side numbers
        if y % 2 == 0:
            px, py = mapper.tile_to_pixel(0, center_y)
            text_labels.append((str(y), (px + 5, py + 5)))

    # --- LOOPED ELEMENTS BEGIN HERE ---
    with ThreadPoolExecutor(max_workers=len(deck)) as executor:
        
        frame_count = 0
        arena_results = [] # Persist results between frames
        
        while True:
            loop_start = time.time()
            frame_count += 1
            
            # --- VISION ---
            try:
                frame = cap.get_screenshot()
            except Exception as e:
                print(f"ERROR: Your Window: \"{window_name}\" was not open.")
                break
            if frame is None:
                time.sleep(1)
                continue

            # --- CARD DETECTION ---
            if not card_input_queue.full():
                card_input_queue.put(frame)
            
            try:
                current_hand = card_output_queue.get_nowait()
            except queue.Empty:
                pass

            for (card_name, (x, y, w, h), score) in current_hand:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{card_name} {score * 100:.2f}%", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # --- ELIXIR TRACKING ---
            if frame_count % 10 == 0 or frame_count == 1:
                current_elixir = elixir_tracker.get_elixir(frame)

            # --- ARENA DETECTION ---
            # 1. Send current frame to the AI (Non-blocking)
            if not ai_input_queue.full():
                ai_input_queue.put(frame.copy())

            #2. Check for new results
            try:
                new_results = ai_output_queue.get_nowait()
                arena_results = new_results
            except queue.Empty:
                pass # If no new update, keep old boxes
            
            # Draw the arena results to keep the boxes on the screen
            arena_detector.draw_detections(frame, arena_results)

            # --- BOT LOGIC ---
            if len(arena_results) > 0 and not bot_state["is_acting"]: # Bot only acts if not busy and there are detections
                # Extract boxes
                detections = arena_results[0].boxes
                
                # Ask the brain to make a move
                move = bot_logic.get_best_move(detections, current_hand, current_elixir, names_map)

                if move:
                    card_name, (target_x, target_y) = move
                    print(f"BOT LOGIC: Countering with {card_name} at ({target_x}, {target_y})")
                    

            # --- DRAWING ON BOT VISION ---
            
            # Drawing Current Elixir
            cv2.putText(frame, f"Elixir: {current_elixir}", (10, 800),
                        cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1, (210, 60, 210), 2, cv2.LINE_4)

            # Draw Cached Grid Lines (Faster than calculating every frame)
            # We iterate by 2s since we stored p1, p2 sequentially
            for i in range(0, len(grid_lines), 2):
                cv2.line(frame, grid_lines[i], grid_lines[i+1], (255, 255, 255), 1, cv2.LINE_AA)

            # Draw Cached Numbers
            for text, loc in text_labels:
                cv2.putText(frame, text, loc, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(frame, text, loc, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

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

            # ----- CONTROLS LOGIC ------
            pressed_card = get_active_key(card_keys)
            if pressed_card:
                selected_card = pressed_card
                print(f"Card {selected_card} Selected! Waiting for position...")
                time.sleep(0.15)
            
            pressed_pos = get_active_key(pos_keys)
            
            if pressed_pos:
                if selected_card is None:
                    print("No Card Selected. Press 1-4 first.")
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