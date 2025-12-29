import cv2
import numpy as np
import keyboard
import time
from action_functions import get_adb_path, get_screenshot, \
    tap_screen, play_card

# ==========================================
#              BOT CONFIGURATION
# ==========================================
# PASTE YOUR CALIBRATION NUMBERS HERE!
# These map the 18x32 grid to your screen pixels
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


ARENA_WIDTH = 18
ARENA_HEIGHT = 32

class ScreenMapper:
    def __init__(self, config):
        self.src_points = np.float32([
            [0, 0], [ARENA_WIDTH, 0], [0, ARENA_HEIGHT], [ARENA_WIDTH, ARENA_HEIGHT]
        ])
        self.dst_points = np.float32([
            config["TOP_LEFT"], config["TOP_RIGHT"], 
            config["BOTTOM_LEFT"], config["BOTTOM_RIGHT"]
        ])
        self.matrix = cv2.getPerspectiveTransform(self.src_points, self.dst_points)

    def tile_to_pixel(self, tile_x, tile_y):
        point = np.array([[[tile_x, tile_y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, self.matrix)
        return (int(transformed[0][0][0]), int(transformed[0][0][1]))


# ==========================================
#                 MAIN LOOP
# ==========================================
if __name__ == "__main__":
    mapper = ScreenMapper(SCREEN_CONFIG)
    print("Bot Running! Press 't' to test playing a card.")

    while True:
        frame = get_screenshot()
        if frame is None: continue

        # --- VISUALIZATION ---
        # Draw the Grid
        for x in range(ARENA_WIDTH + 1):
            p1 = mapper.tile_to_pixel(x, 0)
            p2 = mapper.tile_to_pixel(x, ARENA_HEIGHT)
            cv2.line(frame, p1, p2, (255, 255, 255), 1)
        
        for y in range(ARENA_HEIGHT + 1):
            p1 = mapper.tile_to_pixel(0, y)
            p2 = mapper.tile_to_pixel(ARENA_WIDTH, y)
            cv2.line(frame, p1, p2, (255, 255, 255), 1)

        # Draw the Card Slots (so you can see if calibration is right)
        for i in range(1, 5):
            cx, cy = SCREEN_CONFIG[f"CARD_{i}"]
            cv2.circle(frame, (cx, cy), 20, (0, 255, 255), 2) # Yellow circles for cards

        # Smart Resize for Display
        h, w = frame.shape[:2]
        target_h = 880
        scale = target_h / h
        small_frame = cv2.resize(frame, (int(w * scale), target_h))
        cv2.imshow("Bot Vision", small_frame)
        cv2.waitKey(1)

        # --- CONTROLS ---
        if keyboard.is_pressed("q"):
            print("Quitting...")
            break

        if keyboard.is_pressed("space") and keyboard.is_pressed("1"):
            print("Middle Placement: Card 1")
            play_card(mapper, card_index=1, tile_x=9, tile_y=22)
            time.sleep(0.2)
        if keyboard.is_pressed("space") and keyboard.is_pressed("2"):
            print("Middle Placement: Card 2")
            play_card(mapper, card_index=2, tile_x=9, tile_y=22)
            time.sleep(0.2)
        if keyboard.is_pressed("space") and keyboard.is_pressed("3"):
            print("Middle Placement: Card 3")
            play_card(mapper, card_index=3, tile_x=9, tile_y=22)
            time.sleep(0.2)
        if keyboard.is_pressed("space") and keyboard.is_pressed("4"):
            print("Middle Placement: Card 4")
            play_card(mapper, card_index=4, tile_x=9, tile_y=22)
            time.sleep(0.2)
        

        if keyboard.is_pressed("1") and keyboard.is_pressed("e"):
            print("Bridge Spam!!! Card 1")
            play_card(mapper, card_index=1, tile_x=9, tile_y=22)
            time.sleep(0.2)
        if keyboard.is_pressed("2") and keyboard.is_pressed("e"):
            print("Bridge Spam!!! Card 2")
            play_card(mapper, card_index=2, tile_x=9, tile_y=22)
            time.sleep(0.2)
        if keyboard.is_pressed("3") and keyboard.is_pressed("e"):
            print("Bridge Spam!!! Card 3")
            play_card(mapper, card_index=3, tile_x=9, tile_y=22)
            time.sleep(0.2)
        if keyboard.is_pressed("4") and keyboard.is_pressed("e"):
            print("Bridge Spam!!! Card 4")
            play_card(mapper, card_index=4, tile_x=9, tile_y=22)
            time.sleep(0.2)
    cv2.destroyAllWindows()