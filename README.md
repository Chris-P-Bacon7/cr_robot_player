# cr_robot_player

A real-time AI agent that plays Clash Royale autonomously using computer vision and a custom decision engine.

> ⚠️ **Disclaimer:** Automated bots violate [Supercell's Terms of Service](https://supercell.com/en/terms-of-service/). This project is for educational purposes only. Use on a burner account or private emulator.

---

## How It Works

The bot runs a **multi-threaded pipeline** that separates heavy AI workloads from the main game loop, keeping placement actions lag-free.

```
Screen Capture → [YOLO Thread | Card Vision Thread | OCR Thread]
                              ↓
                     main.py (game loop)
                              ↓
                     bot_logic.py → mouse click
```

### Perception — Three Vision Systems

| Module | Method | What It Reads |
|---|---|---|
| `arena_ai_thread` | YOLOv8 (ONNX) | Enemy troops — type, team, bounding box |
| `card_vision_thread` | `cv2.matchTemplate` | Cards in hand (Standard / Evo / Hero variants) |
| `score_vision_thread` | EasyOCR (PyTorch) | Princess & King Tower HP |

**OCR preprocessing pipeline:** crop ROI → 300% bicubic upscale → grayscale → threshold → invert → EasyOCR with `allowlist='0123456789'`.

### State Memory — TTL Cache

The `persistent_hand` dictionary timestamps every confident card detection. Cards unseen for **1–2 seconds** are pruned, solving the flickering problem caused by elixir drop animations.

### Decision Engine — Geometry-Based Placement

1. YOLO detections are converted from screen pixels → **18×30 isometric tile coordinates** via `cv2.getPerspectiveTransform`.
2. Enemies with `tile_y > 13.5` are flagged as **active bridge threats**.
3. `card_database.json` is queried for the correct counter card.
4. A **placement offset vector** is applied to the threat's tile position, then pulled toward the center column (x=9) to kite enemies.
5. Tile coordinates are mapped back to pixels and passed to the click handler.

---

## Tech Stack

- **Python 3.11+**
- **OpenCV** — capture, template matching, HSV elixir tracking, GUI overlay
- **ONNX Runtime** — CPU-efficient YOLOv8 inference
- **EasyOCR / PyTorch** — tower health reading
- **NumPy** — image math and the synthetic eval-bar dashboard
- **scrcpy** — low-latency screen mirroring from Android device

---

## Setup

```bash
pip install opencv-python easyocr numpy keyboard onnxruntime
```

> For GPU-accelerated OCR, install the CUDA build of PyTorch first. Drops OCR time from ~1.5s → ~0.05s.

**Calibration:** Edit your device config (e.g., `Chris_S25.json`) and set the `[x1, y1, x2, y2]` ROI coordinates for:
- `arena_bounds`
- `card_slots` (1–4)
- `elixir_bar`
- `tower_health` (player/enemy, left/right/king)

Card PNG templates (Standard, `_Evo`, `_Hero`) go in `assets/cards/full_colour/`.

---

## Project Structure

```
cr_robot_player/
├── main.py              # Game loop, threading, HUD windows
├── bot_logic.py         # Threat filtering, counter selection, placement math
├── card_vision.py       # Template matching for hand detection
├── score.py             # EasyOCR tower health reader
├── screen_mapper.py     # Pixel ↔ tile coordinate transforms
├── window_capture.py    # Win32 window-specific screen capture
├── assets/
│   └── cards/full_colour/   # Card PNG templates
└── configs/
    └── Chris_S25.json        # Device ROI calibration
```
