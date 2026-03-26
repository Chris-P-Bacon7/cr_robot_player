# cr_robot_player 🤖👑

A real-time, autonomous AI agent that plays Clash Royale using advanced computer vision, kinematic threat evaluation, and a custom state-aware decision engine.

> ⚠️ **Disclaimer:** Automated bots violate [Supercell's Terms of Service](https://supercell.com/en/terms-of-service/). This project is for **educational and engineering research purposes only**. Use on a burner account or a private emulator.

---

## 🧠 How It Works

The bot operates on a high-speed, **multi-threaded pipeline**. To achieve superhuman reaction times without dropping frames, heavy AI workloads (like YOLO object detection and Optical Character Recognition) run asynchronously on background threads, feeding data to the main decision loop.

```text
Screen Capture → [ YOLO Thread | Card Edge-Vision Thread | OCR Thread ]
                                       ↓ (State Matrix)
                                    main.py (Game Loop)
                                       ↓ (Threat Score & Memory Check)
                             play_automation.py (Decision Engine)
                                       ↓ (Tile-to-Pixel Coordinates)
                                  Mouse Click & Deployment Delay
```

---

## 👀 Perception: Three Vision Systems

Instead of relying on basic color matching, the bot uses tailored computer vision techniques to bypass the game's dynamic lighting, shadows, and animations.

- **Arena Radar (YOLOv8 ONNX):** Detects enemy troops, classifies their team/state (e.g., `Enemy-DarkPrince-Charge`), and outputs bounding boxes.
- **Card Vision (Canny Edge Detection):** Extracts structural features (edges/outlines) of the cards in the player's hand. By converting `cv2.matchTemplate` to compare black-and-white edge gradients rather than RGB pixels, the bot flawlessly recognizes cards even when they are darkened by 0-Elixir shadows.
- **Sub-Pixel Elixir Tracker:** Scans the Elixir bar at an 80% depth to dodge white text overlays, counting total purple pixels across micro-slices to return highly accurate floating-point Elixir values (e.g., `7.4`).
- **Tower OCR (EasyOCR / PyTorch):** Reads Princess and King Tower HP using a specialized pipeline: ROI crop → 300% bicubic upscale → grayscale → threshold → invert → OCR (allowlist: `0-9`).

---

## ⚙️ Cognition: The Decision Engine

The bot does not just react to whatever is closest — it calculates actual mathematical danger using a **Multivariate Kinematic Model**.

1. **Threat Evaluation (Urgency & Power):** Every YOLO detection is fed through a physics engine. The bot calculates the Estimated Time of Arrival (ETA) to the Princess Tower based on the unit's velocity ($d = r \times t$). It combines this with a Power score (Elixir Cost × Class Multiplier) to generate a final `threat_score`.

2. **Short-Term State Memory:** The bot tracks `recent_plays` with 8-second TTL (Time-To-Live) timestamps. Before defending, it calculates how much Elixir it has already committed to a specific lane. If it has already played enough Elixir to secure a positive trade, it intentionally saves its bank, preventing panic-overcommitting.

3. **Efficiency Sorter:** When choosing a defense, the bot uses lambda functions to sort available valid counters in its hand from cheapest to most expensive, ensuring optimal resource management.

4. **Offensive Lane Pressure:** The bot evaluates the cumulative `threat_score` of both lanes. If the enemy heavily invests in the right lane, the bot mathematically recognizes the imbalance and launches counter-attacks in the left lane to split the enemy's attention.

---

## 🦾 Execution: Geometry & Placement

1. **Coordinate Mapping:** YOLO pixel detections are transformed into an 18×30 isometric tile grid via `cv2.getPerspectiveTransform`.
2. **Predictive Spell Aiming:** If defending with a spell (e.g., Fireball), the bot calculates the spell's flight time and the enemy troop's velocity to mathematically aim ahead of the moving target.
3. **Troop Kiting:** Ground troops are placed using offset vectors that pull incoming enemies toward the center "kill zone" (Tile X=9).

---

## 🛠️ Tech Stack

| Library | Role |
|---|---|
| Python 3.11+ | Core runtime |
| OpenCV | Capture, Canny Edge extraction, template matching, HUD rendering |
| ONNX Runtime | CPU-efficient YOLOv8 inference (GPU-ready) |
| EasyOCR / PyTorch | Tower health reading |
| NumPy | Matrix math, pixel arrays, and geometry transforms |

---

## 🚀 Setup & Installation

### 1. Install Dependencies

```bash
pip install opencv-python easyocr numpy keyboard onnxruntime
```

> **Pro-Tip:** For GPU-accelerated OCR and YOLO, install the CUDA build of PyTorch and `onnxruntime-gpu`. This drops inference time from ~150ms to ~15ms per frame.

### 2. Calibration

Edit your device config file (e.g., `Chris_S25.json`) and set the `[x1, y1, x2, y2]` Region of Interest (ROI) coordinates for:

- `arena_bounds`
- `card_slots` (1–4)
- `elixir_bar`
- `tower_health` (player/enemy, left/right/king)

### 3. Assets

Place your Card PNG templates (Standard, `_Evo`, `_Hero`) in the `assets/cards/full_colour/` directory.

### 4. Run the Bot

```bash
python robot/main.py
```

---

## 📂 Project Structure

```
cr_robot_player/
├── robot/
│   ├── main.py                  # Game loop, threading, memory, and HUD
│   ├── card_database.json       # Master troop stats (Speed, Elixir, Counters)
│   ├── automation/
│   │   ├── play_automation.py   # Kinematics, threat evaluation, placement math
│   │   ├── game_controller.py   # Mouse click execution
│   │   └── score.py             # EasyOCR health reader
│   └── perception/
│       ├── arena_vision.py      # YOLOv8 inference wrapper
│       ├── card_vision.py       # Canny Edge template matching
│       ├── elixir_tracker.py    # Sub-pixel Elixir calculation
│       ├── screen_mapper.py     # Pixel ↔ Tile geometry transforms
│       └── window_capture.py    # Win32 fast screen capture
├── assets/
│   └── cards/full_colour/       # Card PNG templates
└── configs/
    └── Chris_S25.json           # Device ROI calibration
```
