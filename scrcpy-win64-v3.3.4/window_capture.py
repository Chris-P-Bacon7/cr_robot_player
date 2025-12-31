import numpy as np
import mss
import pygetwindow as gw
import json
import os

class WindowCapture:
    def __init__(self, window_title_keyword):
        self.window_title = window_title_keyword
        self.monitor = None
        self.sct = mss.mss()
        self.update_window_position()

    def update_window_position(self):
        # Get ALL windows that match the title
        windows = gw.getWindowsWithTitle(self.window_title)
        
        if not windows:
            print(f"❌ Error: Window '{self.window_title}' not found!")
            self.monitor = None
            return False
        
        # --- NEW LOGIC: FIND THE REAL WINDOW ---
        # We loop through all matches and ignore the tiny ones (hidden processes)
        target_win = None
        for w in windows:
            # A valid game window is likely larger than 300x300 pixels
            if w.width > 300 and w.height > 300:
                target_win = w
                break
        
        if target_win is None:
            print(f"⚠️ Found {len(windows)} windows matching '{self.window_title}', but they were all too small.")
            print("   (This happens if the game is minimized or only background processes are found).")
            self.monitor = None
            return False
            
        win = target_win
        
        # Define Offsets
        title_bar_height = 60
        fgm_width = 20
        fgm_height = 7 

        # Calculate dimensions
        final_w = win.width - fgm_width
        final_h = win.height - title_bar_height - fgm_height

        # Final Guard against crashes
        if final_w <= 0 or final_h <= 0:
            print("❌ Error: Capture area is negative. Window might be collapsed.")
            self.monitor = None
            return False

        self.monitor = {
            "top": win.top + title_bar_height, 
            "left": win.left + fgm_width // 2, 
            "width": final_w, 
            "height": final_h
        }
        
        print(f"✅ Locked onto Main Window: {final_w}x{final_h}")
        
        # Save config (refactored for cleanliness)
        self._save_config()
        return True

    def _save_config(self):
        new_data = {"window": self.monitor}
        if os.path.exists("bot_config.json"):
            with open("bot_config.json", "r") as f:
                try: current = json.load(f)
                except: current = {}
        else: current = {}
        
        current.update(new_data)
        with open("bot_config.json", "w") as f:
            json.dump(current, f, indent=4)

    def get_screenshot(self):
        if self.monitor is None:
            if not self.update_window_position():
                return None
        
        try:
            screenshot = self.sct.grab(self.monitor)
            img = np.array(screenshot)
            img = img[:, :, :3]
            return np.ascontiguousarray(img)
        except Exception as e:
            # If the window is closed/moved mid-game, don't crash. Just retry next frame.
            print(f"⚠️ Capture glitch: {e}")
            self.monitor = None 
            return None