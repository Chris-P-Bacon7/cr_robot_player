import cv2
import numpy as np
import json
import os

class ElixirTracker:
    def __init__(self, config):
        self.config = config
    
    def get_elixir(self, frame):
        """
        Checks the 10 specific points on the screen.
        Returns the highest point that is purple.
        """
        current_elixir = 0
        h, w = frame.shape[:2]

        width = self.config["elixir_top_right"][0] - \
            self.config["elixir_top_left"][0]
        middle = (self.config["elixir_top_left"][1] + 
                  self.config["elixir_bottom_left"][1]) / 2
        dx = width / 9

        # Create a dictionary of the 10 points to iterate through
        points = {}
        starting_x = self.config["elixir_top_right"][0]
        for i in range(1, 11):
            points[i] = (starting_x + i * (dx - 1), middle)

        # Loop through points 1 to 10
        for i in range(1, 11):
            key = i

            if key not in points:
                continue

            px, py = points[key]

            px, py = int(px), int(py)

            # Check if the point is within the screen
            if px >= w or py >= h:
                continue

            pixel = frame[py, px]

            if self.is_purple(pixel):
                current_elixir = i
            else:
                # Stop program early if elixir has been determined
                # for efficiency
                break

        return current_elixir
    
    def is_purple(self, pixel):
        """
        Helper function to determine if pixel is purple.
        Pixel is a BGR value. 
        """

        given_colours = int(pixel[0]), int(pixel[1]), int(pixel[2])

        # Check with tolerance to the given value
        ideal_colours = (239, 138, 242)
        tolerance = (0.05)

        for i in range(3):
            if ideal_colours[i] * (1 - 0.05) >= \
                given_colours[i] or given_colours >= ideal_colours[i] * (1 + 0.05):
                return False
        
        return True
