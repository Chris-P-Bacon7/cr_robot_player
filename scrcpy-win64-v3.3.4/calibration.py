import cv2
import numpy as np
import subprocess
import os
import sys

# --- CONFIGURATION ---
TARGET_HEIGHT = 800  # We will shrink the image to this height so it fits your screen

def get_screenshot():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    adb_path = os.path.join(script_dir, "adb.exe")
    
    if not os.path.exists(adb_path):
        print("ERROR: adb.exe not found! Make sure this script is in the SAME folder as adb.exe")
        sys.exit(1)

    try:
        pipe = subprocess.Popen([adb_path, 'shell', 'screencap', '-p'], stdout=subprocess.PIPE)
        image_bytes = pipe.stdout.read()
    except Exception as e:
        print(f"Failed to run ADB: {e}")
        return None
    
    # Fix ADB data format
    image_bytes = image_bytes.replace(b'\r\n', b'\n')
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return img

points = []

def click_event(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Draw on the displayed image
        cv2.circle(img_display, (x, y), 5, (0, 0, 255), -1)
        cv2.imshow('Calibrate - Fit to Screen', img_display)
        
        # Save the click
        points.append((x, y))
        print(f"Clicked point #{len(points)}: {x}, {y}")

# --- MAIN ---
print("Capturing screen...")
img = get_screenshot()

if img is None:
    print("Failed to get screenshot.")
    sys.exit(1)

# 1. Calculate the scale to fit your monitor
original_h, original_w = img.shape[:2]
scale_factor = TARGET_HEIGHT / original_h
new_w = int(original_w * scale_factor)
new_h = int(original_h * scale_factor)

print(f"\nOriginal Resolution: {original_w}x{original_h}")
print(f"Resizing to: {new_w}x{new_h} (Scale: {scale_factor:.3f})")

# 2. Resize
img_display = cv2.resize(img, (new_w, new_h))

print("\n" + "="*50)
print("INSTRUCTIONS:")
print("Click the 4 corners of the PLAYABLE GRASS AREA in this order:")
print("1. TOP-LEFT")
print("2. TOP-RIGHT")
print("3. BOTTOM-LEFT")
print("4. BOTTOM-RIGHT")
print("="*50)

cv2.imshow('Calibrate - Fit to Screen', img_display)
cv2.setMouseCallback('Calibrate - Fit to Screen', click_event)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 3. Calculate Real Coordinates
if len(points) == 4:
    # We divide by scale_factor to convert clicks back to ORIGINAL resolution
    real_points = []
    for (x, y) in points:
        real_x = int(x / scale_factor)
        real_y = int(y / scale_factor)
        real_points.append((real_x, real_y))

    print("\n" + "#"*40)
    print("SUCCESS! PASTE THIS INTO YOUR BOT SETTINGS:")
    print("#"*40)
    print(f"TOP_LEFT     = {real_points[0]}")
    print(f"TOP_RIGHT    = {real_points[1]}")
    print(f"BOTTOM_LEFT  = {real_points[2]}")
    print(f"BOTTOM_RIGHT = {real_points[3]}")
    print("#"*40)
else:
    print(f"Error: You clicked {len(points)} times. Please run again and click exactly 4 times.")