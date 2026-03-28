from roboflow import Roboflow
from ultralytics import YOLO
import os
import dotenv

dotenv.load_dotenv(os.path.join("robot", ".env"))

# --- Paste snippet from Roboflow here ---

my_key = os.getenv("ROBOFLOW_API_KEY")
rf = Roboflow(api_key=my_key)
project = rf.workspace("automated-game-bot").project("clashroyale-bot-v2")
version = project.version(1)
dataset = version.download("yolo26")

                
# ----------------------------------------
                
print("Dataset downloaded.")
model = YOLO('yolov8s.pt')
print("Starting training...")

USE_GIGABYTE_AERO = True  # Toggle this to False if using the Acer Swift

if USE_GIGABYTE_AERO:
    print("Training on Gigabyte Aero x16 (Ryzen 7, RTX 5070, 32GB RAM)...")
    results = model.train(
        data=f"{dataset.location}/data.yaml",
        epochs=300,
        imgsz=640,
        batch=16, # Significantly increased batch size for the RTX 5070
        device=0, # Use the NVIDIA GPU for massive speedup
        workers=8, # Utilize the multi-core Ryzen CPU for faster data loading
        patience=30,
        plots=True
    )
else:
    print("Training on Acer Swift (CPU Mode)...")
    results = model.train(
        data=f"{dataset.location}/data.yaml", # Points to the yaml file downloaded
        # via Roboflow
        epochs=300, # Number of iterations
        imgsz=640, # Image size
        batch=4, # How many to do at once (more = higher performance impact)
        device="cpu", # Forces Intel i7 to be used, increasing stability
        patience=30, # Stop if no progress made after certain iterations
        plots=True # Save training plots and charts
    )

print("Training Complete.")