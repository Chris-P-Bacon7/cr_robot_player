from roboflow import Roboflow
from ultralytics import YOLO


# --- Paste snippet from Roboflow here ---

rf = Roboflow(api_key="LSC1PpIYHkNpDrA9KdvL")
project = rf.workspace("automated-game-bot").project("clashroyale-bot-v1")
version = project.version(5)
dataset = version.download("yolov8")
                
# ----------------------------------------
                
print("Dataset downloaded.")

# 1. Load the YOLOv8 model
model = YOLO('yolov8s.pt')

# 2. Train the model
# data: points to the yaml file downloaded by Roboflow
# epochs: how many times it studies
# imgsz: size of image
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