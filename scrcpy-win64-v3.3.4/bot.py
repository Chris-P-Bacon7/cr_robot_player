import cv2
import numpy as np
import subprocess
import os
import time

# ==========================================
#              BOT CONFIGURATION
# ==========================================
# PASTE YOUR CALIBRATION NUMBERS HERE!
# These map the 18x32 grid to your screen pixels
SCREEN_CONFIG = {
    "TOP_LEFT":     (58, 417),  # Replace with your numbers!
    "TOP_RIGHT":    (1388, 417),
    "BOTTOM_LEFT":  (58, 2262),
    "BOTTOM_RIGHT": (1388, 2262)
}

# The logical size of the Clash Royale Arena (in tiles)
ARENA_WIDTH = 18
ARENA_HEIGHT = 32

class ScreenMapper:
    def __init__(self, config):
        # 1. Define where the tiles are in the "Logical World"
        # We treat the arena as a flat 18x32 rectangle
        self.src_points = np.float32([
            [0, 0],             # Top-Left Tile
            [ARENA_WIDTH, 0],   # Top-Right Tile
            [0, ARENA_HEIGHT],  # Bottom-Left Tile
            [ARENA_WIDTH, ARENA_HEIGHT] # Bottom-Right Tile
        ])

        # 2. Define where those tiles are on your "Physical Screen"
        self.dst_points = np.float32([
            config["TOP_LEFT"],
            config["TOP_RIGHT"],
            config["BOTTOM_LEFT"],
            config["BOTTOM_RIGHT"]
        ])

        # 3. Calculate the "Perspective Matrix"
        # This magical matrix learns how to stretch/squash the grid to fit the angled view
        self.matrix = cv2.getPerspectiveTransform(self.src_points, self.dst_points)

    def tile_to_pixel(self, tile_x, tile_y):
        """Converts a Tile (e.g., 9, 16) to Screen Pixels (e.g., 540, 900)"""
        # Math magic to apply the matrix
        point = np.array([[[tile_x, tile_y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, self.matrix)
        
        pixel_x = int(transformed[0][0][0])
        pixel_y = int(transformed[0][0][1])
        return (pixel_x, pixel_y)

# ==========================================
#           CORE BOT FUNCTIONS
# ==========================================
def get_screenshot():
    # Helper to grab the screen (same as before)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    adb_path = os.path.join(script_dir, "adb.exe")
    
    if not os.path.exists(adb_path):
        # Fallback if adb.exe isn't in the folder
        adb_path = "adb" 

    try:
        pipe = subprocess.Popen([adb_path, 'shell', 'screencap', '-p'], stdout=subprocess.PIPE)
        image_bytes = pipe.stdout.read()
        image_bytes = image_bytes.replace(b'\r\n', b'\n')
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"ADB Error: {e}")
        return None

# ==========================================
#                 MAIN LOOP
# ==========================================
if __name__ == "__main__":
    # 1. Initialize the Brain
    mapper = ScreenMapper(SCREEN_CONFIG)
    
    print("Bot initialized. Drawing the Grid to verify accuracy...")
    print("Press 'q' in the window to quit.")

    while True:
        # 2. Get Vision
        frame = get_screenshot()
        if frame is None:
            time.sleep(1)
            continue

        # 3. DEBUG: Draw the 18x32 grid on the screen
        # If this grid lines up with the grass, your bot is PERFECT.
        
        # Draw vertical lines
        for x in range(ARENA_WIDTH + 1):
            top = mapper.tile_to_pixel(x, 0)
            bottom = mapper.tile_to_pixel(x, ARENA_HEIGHT)
            cv2.line(frame, top, bottom, (255, 255, 255), 1) # White lines

        # Draw horizontal lines
        for y in range(ARENA_HEIGHT + 1):
            left = mapper.tile_to_pixel(0, y)
            right = mapper.tile_to_pixel(ARENA_WIDTH, y)
            cv2.line(frame, left, right, (255, 255, 255), 1)

        # Draw the "Bridge" line (River is usually around row 14-18)
        left_river = mapper.tile_to_pixel(0, 14)
        right_river = mapper.tile_to_pixel(18, 14)
        cv2.line(frame, left_river, right_river, (0, 0, 255), 2) # Red line for river

        # 4. Show the visualizer (Shrink it so it fits)
        h, w = frame.shape[:2]
        small_frame = cv2.resize(frame, (w//2, h//2))
        cv2.imshow("Bot Vision - Grid Verification", small_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()