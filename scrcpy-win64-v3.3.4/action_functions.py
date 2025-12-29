import cv2
import numpy as np
import subprocess
import os
import time

SCREEN_CONFIG = {
    "TOP_LEFT":     (30, 410),  # Replace with your numbers!
    "TOP_RIGHT":    (1400, 410),
    "BOTTOM_LEFT":  (40, 2280),
    "BOTTOM_RIGHT": (1380, 2280),

    # NEW: Your Card Slot Calibration (Replace with your new numbers!)
    "CARD_1": (448, 2850), # Example
    "CARD_2": (725, 2850),
    "CARD_3": (994, 2850),
    "CARD_4": (1263, 2850)
}

def get_adb_path():
    # 1. Find the directory where this script is running
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Join it with the file name
    adb_path = os.path.join(script_dir, "adb.exe")
    
    # 3. Check if it exists. If not, fallback to just "adb" (for system installed versions)
    if not os.path.exists(adb_path):
        return "adb"
        
    return adb_path

def get_screenshot():
    adb_path = get_adb_path()

    try:
        pipe = subprocess.Popen([adb_path, "shell", "screencap", "-p"], stdout=subprocess.PIPE)
        image_bytes = pipe.stdout.read().replace(b"\r\n", b"\n")
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    except:
        return None

def tap_screen(x, y):
    adb_path = get_adb_path()
    cmd = [adb_path, "shell", "input", "tap", str(x), str(y)]
    subprocess.Popen(cmd)

def play_card(mapper, card_index, tile_x, tile_y):
    """
    Selects a card from the hand and places it on the map.
    card_index: 1, 2, 3, or 4
    tile_x, tile_y: Grid location (e.g., 9, 18)
    """
    # 1. Look up where the card slot is
    key = f"CARD_{card_index}"
    if key not in SCREEN_CONFIG:
        print(f"Invalid Card Index: {card_index}")
        return

    card_x, card_y = SCREEN_CONFIG[key]

    # 2. Tap the Card Slot
    print(f"Selecting Card {card_index}...")
    tap_screen(card_x, card_y)
    
    # Wait 0.1s for the game to register the selection
    time.sleep(0.15) 

    # 3. Calculate where the Tile is on the screen
    target_x, target_y = mapper.tile_to_pixel(tile_x, tile_y)

    # 4. Tap the Arena
    print(f"Placing at Tile ({tile_x}, {tile_y})")
    tap_screen(target_x, target_y)