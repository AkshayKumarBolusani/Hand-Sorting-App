# Hand-Tracking Food Sorting Game

## Overview
This is an AI-based interactive hand-tracking food sorting application for desktop use. It uses your laptop's camera for real-time gesture interaction, allowing you to sort food items into veg and non-veg categories using hand gestures. The app is built with Python, OpenCV, MediaPipe, and PyGame, and features a modern, animated UI.

## Features
- Real-time hand tracking using your webcam (MediaPipe + OpenCV)
- Interactive circular food menu that follows your hand
- Menu rotates with your wrist (selfie camera compatible, direction can be changed in code)
- Drag-and-drop food sorting with gestures (pick with left hand, menu with right)
- Score system and timer-based game mode (customizable timer)
- Audio feedback for selections and results
- Confetti and happy/sad emoji rain effects for correct/incorrect drops
- Customizable food items (add/remove/change classification in settings)
- Logging of all actions and scores to CSV
- Elegant, responsive PyGame GUI overlay
- Robust error handling and user feedback

## How It Works
1. **Start the App:**
   - Use the menu to start the game, open settings, or quit.
2. **Game Play:**
   - Show your right hand (open palm) to display and rotate the circular food menu.
   - Use your left hand (grab gesture) to pick a food item and drag it to the veg (top) or non-veg (bottom) box.
   - Drop the item by opening your hand near a box. Score updates based on correctness.
   - Confetti and happy emoji rain for correct drops, sad emoji rain for incorrect.
   - Timer counts down; game ends when time is up or all items are sorted.
3. **Settings:**
   - Drag and drop an image file to add a new food item.
   - Select a food item with up/down arrows. Press `Delete` to remove.
   - Press `V` to set as Veg, `N` for Non-Veg.
   - Adjust timer with left/right arrows.
   - Press `ESC` to return to menu and save settings.

## Foolproof Setup & Run Instructions

### 1. **Install Python 3.11**
Make sure you have Python 3.11 installed:
```bash
python3.11 --version
```
If not, download from https://www.python.org/downloads/release/python-3110/

### 2. **Install Dependencies**
#### Option A: Using a Virtual Environment (Recommended)
```bash
cd hand_sorting_app
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
#### Option B: Install Globally
```bash
cd hand_sorting_app
python3.11 -m pip install --upgrade pip
python3.11 -m pip install -r requirements.txt
```

### 3. **Run the App**
```bash
python3.11 app.py
```

If you see any error about missing modules (like `cv2`), repeat step 2 to ensure all dependencies are installed for Python 3.11.

## Customization & Future Modifications
- **Add/Remove Food Items:** Use the settings screen in the app (drag and drop images, use Delete to remove).
- **Change Food Classification:** Select an item in settings, press `V` (veg) or `N` (non-veg).
- **Change Timer:** Use left/right arrows in settings.
- **Change UI/Effects:** Edit `main.py` and `ui_utils.py` for UI, animations, and effects.
- **Change Game Logic:** Edit `main.py` for gesture logic, scoring, or new features.
- **Dependencies:** Update `requirements.txt` if you add new Python packages.
- **Images:** Add new images to the `images/` folder as needed.
- **Error Handling:** All errors are logged and shown in the UI; check `game_log.csv` for game history.

## Requirements
- Python 3.11
- Webcam

## Troubleshooting
- Ensure your webcam is connected and not used by another application.
- If you encounter issues with audio, check your system's TTS engine.
- If you see `ModuleNotFoundError`, make sure you installed requirements for Python 3.11.
- For any other issues, check the terminal output and `game_log.csv`.

## License
MIT 