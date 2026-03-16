import cv2
import time
import os
from robot.perception.window_capture import WindowCapture

windcap = WindowCapture("SM-S936W")
data_path = 'assets\\raw_images'
if not os.path.exists(data_path):
    os.makedirs(data_path)

print("Data collection initialized...Press 'q' to quit.")

loop_time = time.time()
count = 0

while True:
    screenshot = windcap.get_screenshot()

    if time.time() - loop_time > 2:
        filename = f"{data_path}/clash_gameplay_{count}.png"
        cv2.imwrite(filename, screenshot)
        print(f"Saved {filename}")
        count += 1
        loop_time = time.time()
    
    try:
        continue
    except KeyboardInterrupt:
        print("Exiting data collector...")