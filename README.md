# Clash Royale AI Bot 🤖👑

A hybrid computer-vision bot for Clash Royale that uses **YOLOv8** for real-time object detection and **OpenCV** for UI analysis. It automatically recognizes enemy troops, calculates threats, manages Elixir, and deploys counters based on strategic logic.

## 🚀 Key Features

* **Dual-Layer Vision System:**
* **YOLOv8 (ONNX):** Detects moving troops (Giants, Pekkas, etc.) with high performance.
* **OpenCV:** Uses Template Matching to identify cards in hand and track Elixir levels.


* **Intelligent Logic Engine:**
* **Threat Assessment:** Prioritizes enemies closest to the bridge/tower.
* **Counter System:** Automatically selects the best counter-card from your hand (e.g., *Pekka* vs. *Giant*).
* **Elixir Management:** Checks costs before attempting to play.


* **Precision Control:**
* **Screen Mapping:** Converts raw pixels to in-game "Tile" coordinates for accurate placement.
* **Multi-Threading:** Runs Vision, Logic, and Input on separate threads to minimize latency.


* **Device Agnostic:** Works via `scrcpy`, supporting any Android device.

## 🛠️ Prerequisites

* **Hardware:**
* Android Device (Developer Mode + USB Debugging ON)
* USB Data Cable


* **Software:**
* [Python 3.10+](https://www.python.org/)
* [Scrcpy](https://github.com/Genymobile/scrcpy) (Must be added to System PATH)
* ADB (Android Debug Bridge)



## 📦 Installation

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/cr-robot-player.git
cd cr-robot-player

```


2. **Install Dependencies**
It is recommended to use a virtual environment.
```bash
pip install -r requirements.txt

```


*(If you don't have a requirements file yet, install these manually):*
```bash
pip install ultralytics opencv-python numpy keyboard pywin32

```


3. **Prepare the Model**
Place your trained YOLO weights (converted to ONNX for speed) in the directory:
`runs/detect/train4/weights/best.onnx`
4. **Asset Setup**
Ensure your card templates (screenshots of cards in your hand) are stored in:
`Robot/assets/cards/`

## ⚙️ Configuration

The bot uses JSON files to map screen coordinates to your specific device resolution.

1. Navigate to `Robot/config_files/`.
2. Create or edit a config file (e.g., `Chris_S25.json`) with your device's specific anchor points:
* **Arena Bounds:** Top-Left, Top-Right, Bottom-Left, Bottom-Right.
* **Card Slots:** Coordinates for the 4 card slots.
* **Elixir Bar:** Coordinates for reading elixir.



## 🎮 Usage

1. **Connect your Phone** via USB.
2. **Start Scrcpy** (optimized for low latency):
```bash
scrcpy --max-fps 40 --bit-rate 4M --render-driver opengl

```


3. **Run the Bot**:
```bash
python Robot/main.py

```


4. **Select User**: Type your name (e.g., "chris") to load your specific deck and config.

## 🧠 Bot Logic (How it thinks)

The `BotLogic` class processes data in 3 steps:

1. **Detection:** YOLO identifies all objects on screen. The bot parses names like `Enemy-Giant-Walk`.
2. **Filtering:** It ignores enemies that haven't crossed the bridge (y > 0.45) to save Elixir.
3. **Reaction:**
* Identifies the biggest threat (closest to bottom).
* Checks `counter_chart` for a matching counter in the current hand.
* Verifies Elixir availability.
* Places the troop directly on the threat's coordinates.



## ⚠️ Disclaimer

This project is for **educational purposes only**. Using automation tools in online games likely violates the Terms of Service of Supercell. Use at your own risk. The creator is not responsible for banned accounts.