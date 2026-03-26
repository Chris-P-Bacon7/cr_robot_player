import cv2
import numpy as np
import os
import sys

# Tell Python to look one folder up for imports

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from perception.window_capture import WindowCapture

# ================= CONFIGURATION =================
WINDOW_NAME = "SM-S936W"

# Make sure this path exactly matches where your Zap template is saved!
# I pulled this path from your main.py file.
TEMPLATE_PATH = "assets/cards/full_colour/Card_Zap.png" 
# =================================================

def debug_zap():
    print("Booting up Zap Debugger...")
    cap = WindowCapture(WINDOW_NAME)
    frame = cap.get_screenshot()
    
    if frame is None:
        print(f"CRITICAL ERROR: Could not find the game window '{WINDOW_NAME}'.")
        print("Make sure your scrcpy window is open and the name matches exactly.")
        return

    # Load template in FULL COLOR (BGR)
    template = cv2.imread(TEMPLATE_PATH, cv2.IMREAD_COLOR)
    if template is None:
        print(f"CRITICAL ERROR: Could not load template at '{TEMPLATE_PATH}'.")
        print("Check your folder spelling and make sure the .png file is actually there.")
        return

    print("\n--- ZAP TEMPLATE DIAGNOSTIC ---")
    print(f"Original Template Size: {template.shape[1]}x{template.shape[0]}")
    print(f"Live Frame Size: {frame.shape[1]}x{frame.shape[0]}\n")

    best_match_val = 0
    best_scale = 1.0
    best_loc = (0, 0)
    best_dim = (0, 0)

    print("Scanning multiple scales... Please wait.")
    
    # Test scaling the template from 80% to 120% in 2% increments
    for scale in np.linspace(0.8, 1.2, 21):
        # Resize template mathematically
        width = int(template.shape[1] * scale)
        height = int(template.shape[0] * scale)
        
        # Prevent OpenCV crash if math forces scale to 0
        if width == 0 or height == 0:
            continue
            
        resized_template = cv2.resize(template, (width, height))

        # Run Match in Color
        result = cv2.matchTemplate(frame, resized_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        print(f"Scale {scale*100:.1f}% -> Max Confidence: {max_val:.3f}")

        if max_val > best_match_val:
            best_match_val = max_val
            best_scale = scale
            best_loc = max_loc
            best_dim = (width, height)

    print("\n--- RESULTS ---")
    if best_match_val > 0.60:
        print(f"✅ SUCCESS! Found Zap at {best_scale*100:.1f}% scale with {best_match_val:.3f} confidence.")
        
        # Draw the bounding box to prove it
        cv2.rectangle(frame, best_loc, (best_loc[0] + best_dim[0], best_loc[1] + best_dim[1]), (0, 255, 0), 2)
        cv2.putText(frame, f"ZAP: {best_match_val:.2f}", (best_loc[0], best_loc[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        print("\nDisplaying result window. Press any key in the window to close it.")
        cv2.imshow("Zap Debugger", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print(f"❌ FAILURE. Highest confidence was only {best_match_val:.3f} at {best_scale*100:.1f}% scale.")
        print("Conclusion: Your template image is fundamentally mathematically different from the live feed.")

if __name__ == "__main__":
    debug_zap()