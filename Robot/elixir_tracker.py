import cv2

class ElixirTracker:
    def __init__(self, config):
        self.config = config
        self.points = {}
        
        # Calculate the 10 points ONCE when the bot starts
        # This prevents doing math 60 times a second
        self._calculate_grid()

    def _calculate_grid(self):
        """
        Internal helper to map out the 10 elixir bubbles based on config.
        """
        # Safety Check: Ensure keys exist
        if "elixir_top_left" not in self.config:
            print("⚠️ Warning: Elixir coordinates missing from config.")
            return

        # 1. Get Coordinates
        left_x = self.config["elixir_top_left"][0]
        right_x = self.config["elixir_top_right"][0]
        
        top_y = self.config["elixir_top_left"][1]
        bottom_y = self.config["elixir_bottom_left"][1]

        # 2. Calculate Geometry
        # Width is Right - Left
        bar_width = right_x - left_x 
        middle_y = int((top_y + bottom_y) / 2)
        
        # Distance between bubbles (9 gaps for 10 bubbles)
        dx = bar_width / 9

        # 3. Store the 10 Points
        for i in range(1, 11):
            # Start at Left X.
            # (i - 1) ensures bubble #1 is at 0 distance.
            px = int(left_x + (i - 1) * dx)
            py = int(middle_y)
            
            self.points[i] = (px, py)

    def get_elixir(self, frame):
        """
        Checks the pre-calculated points.
        Returns the highest point that is purple.
        """
        current_elixir = 0
        h, w = frame.shape[:2]

        # Loop through our pre-calculated points
        for i in range(1, 11):
            if i not in self.points:
                continue
                
            px, py = self.points[i]

            # Safety Check: Boundary
            if px >= w or py >= h:
                continue

            pixel = frame[py, px]

            # if i == 1:
            #     print(f"Elixir 1 Colour: {pixel}") # Check what colour the bot sees.

            if self.is_purple(pixel):
                current_elixir = i
            else:
                # Optimization: If bubble 5 is empty, 6-10 are definitely empty.
                break

        return current_elixir
    
    def is_purple(self, pixel):
        """
        Helper function to determine if pixel is purple.
        Pixel is [Blue, Green, Red]
        """
        b, g, r = (int(pixel[0]), int(pixel[1]), int(pixel[2]))

        # Target Color (Pink/Purple)
        if r > 120 and b > 120: # Ensures that the colour is bright enough
            if g < 200 and r > (g + 25) and b > (g + 25):
                # Allows the colour to be super bright (glow) or purple
                # as long as it's not too bright or gray
                return True
        
        return False