import cv2
import os
import time
from window_capture import WindowCapture 

# CONFIG
phone_name = "SM-S936W"  # Must match your scrcpy window

cap = WindowCapture(phone_name)

print("-------------------------------------------------")
print("   CAPTURE TOOL - Create Perfect Templates")
print("-------------------------------------------------")
print("1. Open Clash Royale.")
print("2. Hover your mouse over the 'High Speed Vision' window.")
print("3. Press 's' to save a snapshot.")
print("4. Press 'q' to quit.")
print("-------------------------------------------------")

while True:
    frame = cap.get_screenshot()
    if frame is None:
        time.sleep(1)
        continue

    cv2.imshow("High Speed Vision", frame)
    
    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    elif key == ord('s'):
        # Generate a unique filename based on time
        filename = f"snapshot_{int(time.time())}.png"
        cv2.imwrite(filename, frame)
        print(f"✅ Saved {filename}! Go crop it.")

cv2.destroyAllWindows()