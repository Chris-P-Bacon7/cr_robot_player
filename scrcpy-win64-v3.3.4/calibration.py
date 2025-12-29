import cv2
import numpy as np
import subprocess

def get_screenshot():
    # Capture phone screen via ADB
    pipe = subprocess.Popen(['.\adb.exe', 'shell', 'screencap', '-p'], stdout=subprocess.PIPE)
    image_bytes = pipe.stdout.read()
    
    # Standard fix for ADB image data
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return img

points = []

def click_event(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Captured: {x}, {y}")
        points.append((x, y))
        cv2.circle(img_display, (x, y), 10, (0, 255, 0), -1)
        cv2.imshow('Calibrate Your Phone', img_display)

# 1. Capture
img = get_screenshot()
if img is None:
    print("ADB failed! Check your USB cable and 'USB Debugging' settings.")
    exit()

# 2. Resize for your monitor (so it's not too big to see)
height, width = img.shape[:2]
scale = 0.5 # Shrink to 50% so it fits your PC screen
img_display = cv2.resize(img, (0,0), fx=scale, fy=scale)

print("CLICK THE 4 CORNERS OF THE TILED GRASS AREA:")
print("Top-Left -> Top-Right -> Bottom-Left -> Bottom-Right")

cv2.imshow('Calibrate Your Phone', img_display)
cv2.setMouseCallback('Calibrate Your Phone', click_event)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 3. MATH TIME: Adjust the points back to full resolution
if len(points) == 4:
    real_points = [(int(x/scale), int(y/scale)) for x, y in points]
    print("\n--- YOUR CALIBRATION DATA ---")
    print(f"TL = {real_points[0]}")
    print(f"TR = {real_points[1]}")
    print(f"BL = {real_points[2]}")
    print(f"BR = {real_points[3]}")