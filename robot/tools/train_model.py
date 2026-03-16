from roboflow import Roboflow
from ultralytics import YOLO
import os
import dotenv

dotenv.load_dotenv(os.path.join("robot", ".env"))

# --- Paste snippet from Roboflow here ---

my_key = os.getenv("ROBOFLOW_API_KEY")
rf = Roboflow(api_key=my_key)
project = rf.workspace("automated-game-bot").project("clashroyale-bot-v1")
version = project.version(9)
dataset = version.download("yolo26")
                
# ----------------------------------------
                
print("Dataset downloaded.")
model = YOLO('yolov8s.pt')
print("Starting training...")

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