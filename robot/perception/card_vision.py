import cv2
import numpy as np
import json
import os

class CardVision:
    def __init__(self):
        # This dictionary serves as the bot's "Memory"
        # Format: { "name_of_thing": image_data_matrix }
        self.templates = {}

    def load_template(self, name, image_path, evo_hero):
        """
        Loads an image file (like 'hog_rider.png') into memory.
        """
        # cv2.IMREAD_COLOR loads it in BGR format (Standard for OpenCV)
        # cv2.IMREAD_UNCHANGED would include transparency (alpha), which we usually strip for matching
        
        filename = f"Card_{name}"

        if evo_hero == 1:
            filename = f"Card_{name}_Evo"
        elif evo_hero == 2:
            filename = f"Card_{name}_Hero"
        
        filename = f"{filename}.png"
        full_path = os.path.join(image_path, filename)
        
        img = cv2.imread(full_path, cv2.IMREAD_COLOR)
        
        if img is None:
            print(f"Error: Could not find image at '{image_path}'")
        else:
            if name not in self.templates:
                self.templates[name] = []
            
            self.templates[name].append(img)
            print(f"- Learned pattern: {name}, {full_path}")

    def find(self, haystack_img, template_name, threshold, debug_mode=False):
        """
        Scans the 'haystack' (screenshot) for the 'template'.
        Returns: A list of Rectangles (x, y, w, h) where matches were found.
        """
        if template_name not in self.templates:
            return []

        frame = cv2.cvtColor(haystack_img, cv2.COLOR_BGR2GRAY)

        all_matches = []

        for needle_img in self.templates[template_name]:

            # 1. Run the matching algorithm
            # TM_CCOEFF_NORMED is the best all-rounder. 1.0 = Perfect Match, 0.0 = No Match.

            template = cv2.cvtColor(needle_img, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)

            needle_w = needle_img.shape[1]
            needle_h = needle_img.shape[0]

            # 2. Filter out weak matches
            locations = np.where(result >= threshold)
            locations = list(zip(*locations[::-1]))

            # 3. Consolidate overlapping matches (Clean up the noise)
            rectangles = []
            for loc in locations:
                rect = [int(loc[0]), int(loc[1]), needle_w, needle_h]
                # Add twice to allow grouping logic later (OpenCV requirement for groupRectangles)
                rectangles.append(rect)
                rectangles.append(rect)

            # groupRectangles merges boxes that are right on top of each other
            # eps=0.5 (grouping threshold), groupThreshold=1 (min number of overlaps)
            rectangles, weights = cv2.groupRectangles(rectangles, groupThreshold=1, eps=0.5)

            for (x, y, w, h) in rectangles:
                try:
                    confidence = result[int(y), int(x)]
                except IndexError:
                    confidence = 0

                all_matches.append(((x, y, w, h), confidence))

        return all_matches