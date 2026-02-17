import cv2
import numpy as np
import subprocess
import os
import sys

# ==========================================
#        SAFE START CONFIGURATION
# ==========================================
# We start with a small box in the center to GUARANTEE it works.
# You will push these corners out to the grass edges.
CURRENT_CONFIG = {
    "TOP_LEFT":     (400, 800),   # Starting near middle-left
    "TOP_RIGHT":    (800, 800),   # Starting near middle-right
    "BOTTOM_LEFT":  (300, 1800),  # Starting lower-left
    "BOTTOM_RIGHT": (900, 1800)   # Starting lower-right
}

ARENA_WIDTH = 18
ARENA_HEIGHT = 32

def get_screenshot():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    adb_path = os.path.join(script_dir, "adb.exe")
    if not os.path.exists(adb_path): adb_path = "adb"
    try:
        pipe = subprocess.Popen([adb_path, 'shell', 'screencap', '-p'], stdout=subprocess.PIPE)
        image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n')
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    except:
        return None

def get_matrix(corners):
    # This matrix maps the 18x32 logic grid to your 4 points
    src = np.float32([[0, 0], [ARENA_WIDTH, 0], [0, ARENA_HEIGHT], [ARENA_WIDTH, ARENA_HEIGHT]])
    dst = np.float32(corners)
    return cv2.getPerspectiveTransform(src, dst)

def tile_to_pixel(matrix, tile_x, tile_y):
    point = np.array([[[tile_x, tile_y]]], dtype=np.float32)
    transformed = cv2.perspectiveTransform(point, matrix)
    return (int(transformed[0][0][0]), int(transformed[0][0][1]))

if __name__ == "__main__":
    print("Capturing screen... Please wait.")
    base_image = get_screenshot()
    if base_image is None:
        print("Error: Could not capture screen.")
        sys.exit()

    corners = [
        list(CURRENT_CONFIG["TOP_LEFT"]),
        list(CURRENT_CONFIG["TOP_RIGHT"]),
        list(CURRENT_CONFIG["BOTTOM_LEFT"]),
        list(CURRENT_CONFIG["BOTTOM_RIGHT"])
    ]
    
    idx = 0 
    names = ["TOP_LEFT", "TOP_RIGHT", "BOTTOM_LEFT", "BOTTOM_RIGHT"]

    print("\n--- INSTRUCTIONS ---")
    print("1. Use WASD to move the BLUE selected corner.")
    print("2. Press TAB to switch to the next corner.")
    print("3. Push the corners OUT until they match the grass edges.")
    print("4. Press Q to save.")

    while True:
        frame = base_image.copy()
        
        # 1. Draw the Outline FIRST (to check for twists)
        # Connect TL->TR->BR->BL->TL
        pts = np.array(corners, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], True, (0, 255, 0), 3) # Green Box

        # 2. Draw the Grid (Only if math is safe)
        try:
            matrix = get_matrix(corners)
            
            # Draw Vertical Lines
            for x in range(ARENA_WIDTH + 1):
                p1 = tile_to_pixel(matrix, x, 0)
                p2 = tile_to_pixel(matrix, x, ARENA_HEIGHT)
                cv2.line(frame, p1, p2, (255, 255, 255), 1)

            # Draw River Banks (Rows 15 and 17)
            r1_L = tile_to_pixel(matrix, 0, 15)
            r1_R = tile_to_pixel(matrix, 18, 15)
            cv2.line(frame, r1_L, r1_R, (0, 255, 255), 2) # Cyan
            
            r2_L = tile_to_pixel(matrix, 0, 17)
            r2_R = tile_to_pixel(matrix, 18, 17)
            cv2.line(frame, r2_L, r2_R, (0, 255, 255), 2) # Cyan

        except:
            pass # If grid breaks, just show the Green Box

        # 3. Draw Labels on Corners
        for i, point in enumerate(corners):
            color = (255, 0, 0) if i == idx else (0, 0, 255) # Blue if active, Red if not
            cv2.circle(frame, tuple(point), 20, color, -1)
            cv2.putText(frame, names[i], tuple(point), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # 4. Display
        h, w = frame.shape[:2]
        target_h = 800
        scale = target_h / h
        small_frame = cv2.resize(frame, (int(w * scale), target_h))
        cv2.imshow("Safe Grid Tuner", small_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif key == 9: idx = (idx + 1) % 4 # TAB
        
        # Move Faster (Speed 10)
        speed = 10
        if key == ord('w'): corners[idx][1] -= speed
        if key == ord('s'): corners[idx][1] += speed
        if key == ord('a'): corners[idx][0] -= speed
        if key == ord('d'): corners[idx][0] += speed

    cv2.destroyAllWindows()
    print("="*40)
    print(f'"TOP_LEFT":     {tuple(corners[0])},')
    print(f'"TOP_RIGHT":    {tuple(corners[1])},')
    print(f'"BOTTOM_LEFT":  {tuple(corners[2])},')
    print(f'"BOTTOM_RIGHT": {tuple(corners[3])},')
    print("="*40)