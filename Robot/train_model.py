from roboflow import Roboflow
from ultralytics import YOLO


# --- Paste snippet from Roboflow here ---

from roboflow import Roboflow
rf = Roboflow(api_key="LSC1PpIYHkNpDrA9KdvL")
project = rf.workspace("automated-game-bot").project("clashroyale-bot-v1")
version = project.version(4)
dataset = version.download("yolov8")

# ----------------------------------------
                
print("Dataset downloaded.")

# 1. Load the YOLOv8 model
# 'yolov8n.pt' is the "Nano" version (Fastest, least accurate). 
# Good for your first test.
model = YOLO('yolov8s.pt')

# 2. Train the model
# data: points to the yaml file downloaded by Roboflow
# epochs: how many times it studies (50 is a good start)
# imgsz: size of image (640 is standard)
print("Starting training...")

results = model.train(
    data=f"{dataset.location}/data.yaml",
    epochs=50,
    imgsz=1280,
    batch=8,
    patience=30,
    plots=True
)

print("Training Complete!")