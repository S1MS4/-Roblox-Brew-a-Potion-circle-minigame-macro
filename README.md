# Circle Clicker for Roblox

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An advanced automation tool for Roblox that uses computer vision to detect and click circles on screen. Features undetectable mouse simulation and human-like movement patterns to bypass anti-cheat systems.

## Features

- **Computer Vision Detection**: Uses OpenCV to detect circles in real-time
- **Two Click Modes**:
  - Human-like: Smooth curved movements with random delays
  - Instaclick: Fast, precise clicks for speed
- **Undetectable Input**: Windows API mouse simulation
- **GUI Interface**: PyQt5-based control panel
- **Hotkey Controls**: Pause/resume and mode switching
- **Debug Tools**: Saves detection images for troubleshooting

## Installation

1. Clone or download the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### GUI Version (Recommended)
```bash
python menu.py
```
- Select mode from dropdown
- Click START to begin
- Use hotkeys for control

### CLI Version
```bash
python human_like.py
```

## Screenshots

### Debug Detection
![Debug Image](debug.png)

### Showcase
![Showcase](showcase.gif)

## Controls

- **N**: Pause/Resume clicking
- **Ctrl+N**: Stop script (CLI only)
- **Tab**: Switch modes (GUI only)

## Disclaimer

This tool is for educational purposes only. Use at your own risk. Automated clicking may violate game terms of service and could result in account bans. The authors are not responsible for any consequences.

## License

MIT License - see LICENSE file for details.
