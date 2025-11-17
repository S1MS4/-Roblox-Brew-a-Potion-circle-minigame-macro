import pyautogui
import cv2
import numpy as np
import time
import keyboard
import random
import ctypes
from ctypes import wintypes

# Timing Configuration - Random Ranges with 10ms offsets
HOVER_TIME_RANGE = (0.015, 0.025)      # 15-25ms (was 20ms)
JITTER_TIME_RANGE = (0.008, 0.012)     # 8-12ms (was 10ms)  
CLICK_HOLD_RANGE = (0.015, 0.025)      # 15-25ms (was 20ms)
BETWEEN_CLICKS_RANGE = (0.04, 0.06)    # 40-60ms (was 50ms)
MAIN_LOOP_RANGE = (0.04, 0.06)         # 40-60ms (was 50ms)

# Timing Configuration - Random Ranges (10x faster)
HOVER_TIME_RANGE = (0.0015, 0.0025)      # 1.5-2.5ms (was 15-25ms)
JITTER_TIME_RANGE = (0.0008, 0.0012)     # 0.8-1.2ms (was 8-12ms)  
CLICK_HOLD_RANGE = (0.0015, 0.0025)      # 1.5-2.5ms (was 15-25ms)
BETWEEN_CLICKS_RANGE = (0.004, 0.006)    # 4-6ms (was 40-60ms)
MAIN_LOOP_RANGE = (0.004, 0.006)         # 4-6ms (was 40-60ms)

# Pause/Resume and Stop control
paused = True
should_exit = False

def toggle_pause():
    global paused
    paused = not paused
    if paused:
        print("Script PAUSED. Press N again to resume.")
    else:
        print("Script RESUMED.")

def set_exit():
    global should_exit
    should_exit = True

# Set up hotkeys
keyboard.add_hotkey('n', toggle_pause)
keyboard.add_hotkey('ctrl+n', set_exit)

def should_stop():
    global should_exit
    return should_exit

def wait_while_paused():
    """Wait while script is paused"""
    global should_exit, paused
    while paused and not should_exit:
        time.sleep(0.1)

# Windows API for undetectable input
user32 = ctypes.windll.user32

# Structures for SendInput
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

def send_mouse_input(flags, x=0, y=0, data=0):
    """Send low-level mouse input that games can't detect as automated"""
    input_struct = INPUT()
    input_struct.type = 0  # INPUT_MOUSE
    input_struct.mi.dx = x
    input_struct.mi.dy = y
    input_struct.mi.mouseData = data
    input_struct.mi.dwFlags = flags
    input_struct.mi.time = 0
    input_struct.mi.dwExtraInfo = None
    
    user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(INPUT))

def fast_undetectable_click(x, y):
    """Fast but reliable click for Roblox"""
    # Convert to absolute coordinates
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    abs_x = int(x * 65535 / screen_width)
    abs_y = int(y * 65535 / screen_height)
    
    # PHASE 1: Move to position (minimal hover)
    send_mouse_input(0x8001, abs_x, abs_y)
    time.sleep(random.uniform(*HOVER_TIME_RANGE))
    
    # PHASE 2: Quick single jitter
    jitter_x = random.randint(-1, 1)
    jitter_y = random.randint(-1, 1)
    jitter_abs_x = int((x + jitter_x) * 65535 / screen_width)
    jitter_abs_y = int((y + jitter_y) * 65535 / screen_height)
    send_mouse_input(0x8001, jitter_abs_x, jitter_abs_y)
    time.sleep(random.uniform(*JITTER_TIME_RANGE))
    
    # PHASE 3: Return and click fast
    send_mouse_input(0x8001, abs_x, abs_y)
    time.sleep(random.uniform(*JITTER_TIME_RANGE))
    
    # PHASE 4: Click down and up
    send_mouse_input(0x0002)  # MOUSEEVENTF_LEFTDOWN
    time.sleep(random.uniform(*CLICK_HOLD_RANGE))
    send_mouse_input(0x0004)  # MOUSEEVENTF_LEFTUP

def click_on_patterns():
    # Fixed circle detection parameters
    min_radius = 50
    max_radius = 60

    while True:
        # Check for exit at the start of each iteration
        if should_stop():
            break

        # Wait if paused
        wait_while_paused()
        if should_stop():
            print("Stopping script.")
            break

        screenshot = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)

        # Check for exit before processing circles
        if should_stop():
            break
        wait_while_paused()
        if should_stop():
            break

        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 80,
                          param1=80, param2=50,
                          minRadius=min_radius, maxRadius=max_radius)

        debug_img = screenshot_cv.copy()
        matches_found = False

        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                # Check for exit before each click
                if should_stop():
                    print("Stopping script.")
                    return
                wait_while_paused()
                if should_stop():
                    print("Stopping script.")
                    return

                center_x, center_y, radius = i[0], i[1], i[2]
                matches_found = True

                # Small random offset
                click_x = int(center_x) + random.randint(-2, 2)
                click_y = int(center_y) + random.randint(-2, 2)
                
                # Use fast click
                fast_undetectable_click(click_x, click_y)
                print(f"Clicked on circle at ({click_x}, {click_y})")
                
                # Fast delay between clicks
                time.sleep(random.uniform(*BETWEEN_CLICKS_RANGE))

        if matches_found:
            cv2.imwrite('debug_matches.png', debug_img)
            print("Debug image saved as 'debug_matches.png' showing detected circles.")

        time.sleep(random.uniform(*MAIN_LOOP_RANGE))

if __name__ == "__main__":
    print("Starting FAST circle click macro with random timing.")
    print("Timing Ranges:")
    print(f"  - Hover Time: {HOVER_TIME_RANGE[0]*1000:.0f}-{HOVER_TIME_RANGE[1]*1000:.0f}ms")
    print(f"  - Jitter Time: {JITTER_TIME_RANGE[0]*1000:.0f}-{JITTER_TIME_RANGE[1]*1000:.0f}ms")
    print(f"  - Click Hold: {CLICK_HOLD_RANGE[0]*1000:.0f}-{CLICK_HOLD_RANGE[1]*1000:.0f}ms")
    print(f"  - Between Clicks: {BETWEEN_CLICKS_RANGE[0]*1000:.0f}-{BETWEEN_CLICKS_RANGE[1]*1000:.0f}ms")
    print(f"  - Main Loop: {MAIN_LOOP_RANGE[0]*1000:.0f}-{MAIN_LOOP_RANGE[1]*1000:.0f}ms")
    print("\nControls:")
    print("  - Press N to PAUSE/RESUME")
    print("  - Press Ctrl+N to STOP the script completely")
    click_on_patterns()