import pyautogui
import time
import random
import keyboard

# SAFETY: If the bot goes crazy, slam your mouse to the top-left corner 
# of your screen to trigger a crash and stop it.
pyautogui.FAILSAFE = True

class GameController:
    def __init__(self, window_capture):
        """
        Args:
            window_capture (WindowCapture): The object that tracks where the 
                                            window is on your monitor.
        """
        self.cap = window_capture

    def _get_global_coords(self, game_x, game_y):
        """
        Internal Helper: Converts 'Game Pixels' (0,0 is top-left of game) 
        to 'Monitor Pixels' (0,0 is top-left of your actual screen).
        """
        if self.cap.monitor is None:
            # Try to find the window if we lost it
            if not self.cap.update_window_position():
                print("❌ Controls Error: Window not found!")
                return None, None

        # The math: Window Position + Pixel Offset
        # We add 'left' and 'top' to account for where the window is sitting.
        screen_x = self.cap.monitor["left"] + game_x
        screen_y = self.cap.monitor["top"] + game_y
        
        return screen_x, screen_y

    def click(self, game_x, game_y):
        """
        Moves the physical mouse to the coordinates and clicks.
        """
        sx, sy = self._get_global_coords(game_x, game_y)
        
        if sx is None: return

        # 1. Human-like movement (not instant teleportation)
        # Random speed between 0.05s and 0.15s
        duration = random.uniform(0.05, 0.15) 
        pyautogui.moveTo(sx, sy, duration=duration)
        
        # 2. Click
        pyautogui.click()

    def play_card(self, card_key, tile_target, screen_config, mapper):
        """
        The main action function.
        
        Args:
            card_key (str): The key in config (e.g., "card_1", "card_2")
            tile_target (tuple): The logic target (e.g., (9, 18) for bridge)
            screen_config (dict): The dictionary containing card coordinates
            mapper (ScreenMapper): The object that turns tiles into pixels
        """
        
        # --- STEP 1: CLICK THE CARD ---
        if card_key not in screen_config:
            print(f"❌ Error: {card_key} not found in config!")
            return

        # Get the pixel coordinates of the card slot (Relative to game)
        card_x, card_y = screen_config[card_key]
        
        print(f"Selecting {card_key}...")
        self.click(card_x, card_y)

        # Small human delay
        time.sleep(random.uniform(0.1, 0.2))

        # --- STEP 2: AIM & WAIT ---
        # Calculate target pixels
        
        tx, ty = tile_target
        field_x, field_y = mapper.tile_to_pixel(tx, ty)
        
        # 1. Move mouse to target BUT DO NOT CLICK yet
        sx, sy = self._get_global_coords(field_x, field_y)
        if sx:
            pyautogui.moveTo(sx, sy, duration=0.2)
            
        # 2. Wait for confirmation
        print(f"⚠️  AIMING at {tile_target}. Press SPACE to Drop!")
        keyboard.wait('space')
        
        # 3. Small debounce so we don't accidentally trigger other things
        time.sleep(0.1) 

        # --- STEP 3: CLICK THE FIELD ---
        print(f"Placing at Tile {tile_target}...")
        pyautogui.click() # We are already at the location, just click
        
        # Optional: Move mouse away so it doesn't hover over the game
        # pyautogui.moveRel(200, 0)