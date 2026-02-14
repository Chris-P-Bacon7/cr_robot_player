from roboflow import Roboflow
from ultralytics import YOLO


# --- Paste snippet from Roboflow here ---

rf = Roboflow(api_key="LSC1PpIYHkNpDrA9KdvL")
project = rf.workspace("automated-game-bot").project("clashroyale-bot-v1")
version = project.version(5)
dataset = version.download("yolov8")
                
# ----------------------------------------
                
print("Dataset downloaded.")
model = YOLO('yolov8s.pt')
print("Starting training...")

results = model.train(
    data=f"{dataset.location}/data.yaml", # Points to the yaml file downloaded
    # via Roboflow
    epochs=50, # Number of iterations
    imgsz=1280, # Image size
    batch=8, # How many to do at once (more = higher performance impact)
    patience=30, # Stop if no progress made after certain iterations
    plots=True # 
)

print("Training Complete.")