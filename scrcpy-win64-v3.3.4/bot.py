import cv2
import numpy as np
import keyboard
import time
import mss
import pygetwindow as gw
from window_capture import WindowCapture
# ==========================================
#             BOT CONFIGURATION
# ==========================================
# PASTE YOUR CALIBRATION NUMBERS HERE!
# These map the 18x32 grid to your screen pixels
screen_config = {
    "top_left":     (30, 410),  # Replace with your numbers!
    "top_right":    (1400, 410),
    "bottom_left":  (40, 2280),
    "bottom_right": (1380, 2280),

    # NEW: Your Card Slot Calibration (Replace with your new numbers!)
    "card_1": (448, 2850), # Example
    "card_2": (725, 2850),
    "card_3": (994, 2850),
    "card_4": (1263, 2850)
}

arena_width = 18
arena_height = 32

# Strategic Locations (Tile X, Tile Y)
locations = {
    "defense": (9, 10),
    "bridge_left": (3, 18),
    "bridge_right": (15, 18)
}

# class ScreenMapper:
#     def __init__(self, config):
#         self.src_points = np.float32([
#             [0, 0], [arena_width, 0], [0, arena_height], [arena_width, arena_height]
#         ])
#         self.dst_points = np.float32([
#             config["top_left"], config["top_right"], 
#             config["bottom_left"], config["bottom_right"]
#         ])
#         self.matrix = cv2.getPerspectiveTransform(self.src_points, self.dst_points)

#     def tile_to_pixel(self, tile_x, tile_y):
#         point = np.array([[[tile_x, tile_y]]], dtype=np.float32)
#         transformed = cv2.perspectiveTransform(point, self.matrix)
#         return (int(transformed[0][0][0]), int(transformed[0][0][1]))


# ==========================================
#                 MAIN LOOP
# ==========================================

if __name__ == "__main__":
    # REPLACE 'SM-G' WITH PART OF YOUR SCRCPY WINDOW NAME
    cap = WindowCapture("SM-S936W") 
    
    while True:
        loop_start = time.time()
        
        frame = cap.get_screenshot()
        if frame is None:
            time.sleep(1)
            continue

        # Calculate 
        try:
            fps = 1 / (time.time() - loop_start)
        except Exception as e:
            print(f"Failure to calculate FPS because of: {e}")
        
        cv2.putText(frame, f"FPS: {int(fps)}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow("High Speed Vision", frame)
        
        if cv2.waitKey(1) == ord('q'):
            break

        # Controls
        
        if keyboard.is_pressed()
            
    cv2.destroyAllWindows()