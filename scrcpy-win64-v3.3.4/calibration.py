import cv2
import numpy as np
import mss
import pygetwindow as gw
import time
import keyboard
import json

# ================= CONFIGURATION =================
WINDOW_NAME = "SM-S936W" # Check your window title!
ARENA_WIDTH = 18
ARENA_HEIGHT = 32
# =================================================

class WindowCapture:
    def __init__(self, window_title_keyword):
        self.window_title = window_title_keyword
        self.monitor = None
        self.sct = mss.mss()
        self.update_window_position()

    def update_window_position(self):
        try:
            windows = gw.getWindowsWithTitle(self.window_title)
        except Exception:
            windows = []
            
        if not windows:
            print(f"Searching for window: '{self.window_title}'...")
            self.monitor = None
            return False
        
        win = windows[0]
        title_bar_height = 60
        fgm_width = 20
        fgm_height = 7
        self.monitor = {
            "top": win.top + title_bar_height, 
            "left": win.left + fgm_width // 2, 
            "width": win.width - fgm_width, 
            "height": win.height - title_bar_height - fgm_height
        }
        return True

    def get_screenshot(self):
        if self.monitor is None:
            if not self.update_window_position():
                return None
        try:
            img = np.array(self.sct.grab(self.monitor))
            img = np.ascontiguousarray(img[:, :, :3])
            return img
        except Exception:
            self.monitor = None
            return None

# --- VISUALIZATION HELPERS ---
def draw_perspective_grid(img, corners, show_inner_grid=True):
    h, w = img.shape[:2]
    
    # Source: The logical 18x32 grid
    src_points = np.float32([[0, 0], [ARENA_WIDTH, 0], [0, ARENA_HEIGHT], [ARENA_WIDTH, ARENA_HEIGHT]])
    dst_points = np.float32(corners)
    
    # Calculate transform matrix
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    
    def tile_to_pixel(tx, ty):
        point = np.array([[[tx, ty]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, matrix)
        return (int(transformed[0][0][0]), int(transformed[0][0][1]))

    # Draw Frame (Always visible)
    # TL->TR, TR->BR, BR->BL, BL->TL
    tl, tr = tile_to_pixel(0, 0), tile_to_pixel(ARENA_WIDTH, 0)
    bl, br = tile_to_pixel(0, ARENA_HEIGHT), tile_to_pixel(ARENA_WIDTH, ARENA_HEIGHT)
    
    cv2.line(img, tl, tr, (0, 255, 0), 1) # Top
    cv2.line(img, tr, br, (0, 255, 0), 1) # Right
    cv2.line(img, br, bl, (0, 255, 0), 1) # Bottom
    cv2.line(img, bl, tl, (0, 255, 0), 1) # Left

    if show_inner_grid:
        # Vertical Inner Lines
        for x in range(1, ARENA_WIDTH):
            p1 = tile_to_pixel(x, 0)
            p2 = tile_to_pixel(x, ARENA_HEIGHT)
            color = (50, 200, 200) if x == 9 else (100, 100, 100) # Cyan center, Grey others
            cv2.line(img, p1, p2, color, 1)

        # Horizontal Inner Lines
        for y in range(1, ARENA_HEIGHT):
            p1 = tile_to_pixel(0, y)
            p2 = tile_to_pixel(ARENA_WIDTH, y)
            color = (50, 50, 255) if y == 18 else (100, 100, 100) # Red river, Grey others
            cv2.line(img, p1, p2, color, 1)
        
    return img

def main():
    cap = WindowCapture(WINDOW_NAME)
    print("Waiting for window...")
    while True:
        frame = cap.get_screenshot()
        if frame is not None: break
        time.sleep(1)

    h, w = frame.shape[:2]
    
    # --- 1. ARENA (PERSPECTIVE) ---
    top_margin = int(w * 0.12)
    bot_margin = int(w * 0.04)
    top_y = int(h * 0.12)
    bot_y = int(h * 0.82)
    
    arena_pts = [
        [top_margin, top_y],            # TL
        [w - top_margin, top_y],        # TR
        [bot_margin, bot_y],            # BL
        [w - bot_margin, bot_y]         # BR
    ]
    
    # --- 2. CARD SLOTS ---
    card_y = int(h * 0.90)
    card_spread = int(w / 4.5)
    start_x = int(w / 2) - int(card_spread * 1.5)
    card_pts = [
        [start_x, card_y], [start_x + card_spread, card_y],
        [start_x + card_spread*2, card_y], [start_x + card_spread*3, card_y]
    ]

    # --- 3. ELIXIR BAR (RECTANGLE) ---
    elixir_tl = [int(w * 0.25), int(h * 0.96)]
    elixir_br = [int(w * 0.75), int(h * 0.99)]
    elixir_rect_pts = [elixir_tl, elixir_br] 

    modes = ["ARENA (3D)", "CARDS", "ELIXIR (2D)"]
    current_mode = 0
    active_idx = 0
    show_grid = True # Toggle state
    
    print("\n--- CONTROLS ---")
    print("SPACE:  Switch Mode")
    print("TAB:    Select Corner")
    print("G:      Toggle Grid Lines")
    print("ARROWS: Move Corner (Shift for speed)")
    print("ENTER:  Save & Quit")

    while True:
        frame = cap.get_screenshot()
        if frame is None: continue
        
        # --- INPUT ---
        if keyboard.is_pressed('space'):
            current_mode = (current_mode + 1) % 3
            active_idx = 0
            time.sleep(0.3)
            
        if keyboard.is_pressed('tab'):
            limit = 2 if current_mode == 2 else 4
            active_idx = (active_idx + 1) % limit
            time.sleep(0.2)
            
        if keyboard.is_pressed('g'):
            show_grid = not show_grid
            time.sleep(0.2)

        speed = 4 if keyboard.is_pressed('shift') else 1 # Slower precision speed
        
        # Select Target
        if current_mode == 0: target = arena_pts
        elif current_mode == 1: target = card_pts
        elif current_mode == 2: target = elixir_rect_pts

        if keyboard.is_pressed('up'):    target[active_idx][1] -= speed
        if keyboard.is_pressed('down'):  target[active_idx][1] += speed
        if keyboard.is_pressed('left'):  target[active_idx][0] -= speed
        if keyboard.is_pressed('right'): target[active_idx][0] += speed

        # --- DRAWING ---
        
        # MODE 1: ARENA
        if current_mode == 0:
            frame = draw_perspective_grid(frame, arena_pts, show_inner_grid=show_grid)
            
            # Tiny Green Dot for Active Corner
            cv2.circle(frame, tuple(arena_pts[active_idx]), 3, (0, 255, 0), -1)
            
            # Helper Text
            cv2.putText(frame, "Align outer green box to playable tiles", (20, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            # Passive faint outline
            pts = np.array(arena_pts, np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, (50, 50, 50), 1)

        # MODE 2: CARDS
        if current_mode == 1:
            for i, pt in enumerate(card_pts):
                color = (0, 255, 0) if i == active_idx else (0, 255, 255)
                # Small circle (radius 4)
                cv2.circle(frame, tuple(pt), 4, color, 1)
                # Tiny center dot
                cv2.circle(frame, tuple(pt), 1, color, -1)
        elif current_mode != 1:
             for pt in card_pts: cv2.circle(frame, tuple(pt), 2, (0, 100, 100), -1)

        # MODE 3: ELIXIR
        e_tl = elixir_rect_pts[0]
        e_br = elixir_rect_pts[1]
        cv2.rectangle(frame, tuple(e_tl), tuple(e_br), (255, 0, 255), 1)
        
        if current_mode == 2:
            cv2.circle(frame, tuple(elixir_rect_pts[active_idx]), 3, (0, 255, 0), -1)
        
        # Header
        cv2.putText(frame, f"MODE: {modes[current_mode]}", (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Calibration Wizard", frame)
        if cv2.waitKey(1) == 13: break 
        if keyboard.is_pressed('q'): exit()

    cv2.destroyAllWindows()

    # --- SAVE ---
    ex_full = [
        e_tl,                    # TL
        [e_br[0], e_tl[1]],      # TR
        [e_tl[0], e_br[1]],      # BL
        e_br                     # BR
    ]
    
    config_data = {
        "arena": {
            "top_left": arena_pts[0], "top_right": arena_pts[1],
            "bottom_left": arena_pts[2], "bottom_right": arena_pts[3]
        },
        "card_slots": {
            "card_1": card_pts[0], "card_2": card_pts[1],
            "card_3": card_pts[2], "card_4": card_pts[3]
        },
        "elixir": {
            "top_left": ex_full[0], "top_right": ex_full[1],
            "bottom_left": ex_full[2], "bottom_right": ex_full[3]
        }
    }

    print("\nSaving to 'bot_config.json'...")
    with open("bot_config.json", "w") as f:
        json.dump(config_data, f, indent=4)
    print("✅ Configuration Saved!")

if __name__ == "__main__":
    main()