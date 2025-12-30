import cv2
import numpy as np
import mss
import pygetwindow as gw  # The new library
import time

class WindowCapture:
    def __init__(self, window_title_keyword):
        self.window_title = window_title_keyword
        self.monitor = None
        self.sct = mss.mss()
        
        # 1. Find the window dynamically
        self.update_window_position()

    def update_window_position(self):
        # We look for any window that contains the keyword in its title
        windows = gw.getWindowsWithTitle(self.window_title)
        
        if not windows:
            print(f"❌ Error: Could not find window with name containing '{self.window_title}'")
            print("Make sure scrcpy is open and the name matches!")
            self.monitor = None
            return None

        win = windows[0]
        
        # ⚠️ CRITICAL: We need to define the capture area for MSS
        # We add a small offset to skip the window title bar (usually ~30px)
        title_bar_height = 60
        fgm_width = 20
        fgm_height = 7 

        self.monitor = {
            "top": win.top + title_bar_height, 
            "left": win.left + fgm_width // 2  , 
            "width": win.width - fgm_width, 
            "height": win.height - title_bar_height - fgm_height
        }
        print(f"✅ Locked onto window: {self.monitor}")

    def get_screenshot(self):
        if self.monitor is None:
            self.update_window_position()
            return None

        # Capture using mss (High Speed)
        screenshot = self.sct.grab(self.monitor)
        img = np.array(screenshot)
        
        # Drop Alpha channel (BGRA -> BGR)
        img = img[:, :, :3]
        
        # Make it contiguous (required for some OpenCV functions)
        img = np.ascontiguousarray(img)
        
        return img