import pyautogui
import cv2
import numpy as np
import time
import keyboard
import random
import ctypes
from ctypes import wintypes
import math

# Timing Configuration - Random Ranges
HOVER_TIME_RANGE = (0.015, 0.025)      # 15-25ms
JITTER_TIME_RANGE = (0.008, 0.012)     # 8-12ms  
CLICK_HOLD_RANGE = (0.015, 0.025)      # 15-25ms
BETWEEN_CLICKS_RANGE = (0.04, 0.06)    # 40-60ms
MAIN_LOOP_RANGE = (0.04, 0.06)         # 40-60ms

# Movement Configuration - Global Variables for Easy Adjustment
MIN_STEPS = 8                          # Minimum movement steps
MAX_STEPS = 20                         # Maximum movement steps  
STEPS_DISTANCE_DIVISOR = 10            # Distance divisor for step calculation
STEP_SLEEP_TIME = 0.005                # Time between each movement step (5ms)
CURVE_STRENGTH_RANGE = (1, 3)          # How much curve in movement (1-3 pixels)


# Faster but less smooth:
MIN_STEPS = 5
MAX_STEPS = 12
STEP_SLEEP_TIME = 0.001

# Slower but more human-like:
# MIN_STEPS = 12
# MAX_STEPS = 25  
# STEP_SLEEP_TIME = 0.008


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

def smooth_human_movement(target_x, target_y):
    """Smooth human-like movement using Windows API"""
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    # Get current position
    current_x, current_y = pyautogui.position()
    
    # Calculate distance for realistic movement
    distance = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)
    steps = max(MIN_STEPS, min(MAX_STEPS, int(distance / STEPS_DISTANCE_DIVISOR)))
    
    # Smooth curved movement (humans don't move in straight lines)
    for i in range(steps):
        progress = i / steps
        
        # Bezier-like easing for natural movement
        if progress < 0.5:
            ease = 2 * progress * progress  # Accelerate
        else:
            ease = 1 - math.pow(-2 * progress + 2, 2) / 2  # Decelerate
        
        # Add subtle curve to movement
        curve_factor = math.sin(progress * math.pi) * random.uniform(*CURVE_STRENGTH_RANGE)
        curve_x = random.choice([-1, 1]) * curve_factor
        curve_y = random.choice([-1, 1]) * curve_factor
        
        # Calculate intermediate position
        inter_x = current_x + (target_x - current_x) * ease + curve_x
        inter_y = current_y + (target_y - current_y) * ease + curve_y
        
        # Convert to absolute coordinates and move
        abs_x = int(inter_x * 65535 / screen_width)
        abs_y = int(inter_y * 65535 / screen_height)
        send_mouse_input(0x8001, abs_x, abs_y)  # MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
        
        time.sleep(STEP_SLEEP_TIME)  # Smooth timing between steps
    
    # Final precise movement to target
    abs_target_x = int(target_x * 65535 / screen_width)
    abs_target_y = int(target_y * 65535 / screen_height)
    send_mouse_input(0x8001, abs_target_x, abs_target_y)

def human_like_click(x, y):
    """Combined smooth movement with nuclear click"""
    # Add human-like variance to target
    target_x = x + random.randint(-3, 3)
    target_y = y + random.randint(-3, 3)
    
    # Smooth movement to target
    smooth_human_movement(target_x, target_y)
    
    # Hover with micro-movements
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    time.sleep(random.uniform(*HOVER_TIME_RANGE))
    
    # Natural hand jitter while hovering
    for _ in range(random.randint(1, 2)):
        jitter_x = target_x + random.randint(-2, 2)
        jitter_y = target_y + random.randint(-2, 2)
        abs_jitter_x = int(jitter_x * 65535 / screen_width)
        abs_jitter_y = int(jitter_y * 65535 / screen_height)
        send_mouse_input(0x8001, abs_jitter_x, abs_jitter_y)
        time.sleep(random.uniform(*JITTER_TIME_RANGE))
    
    # Return to exact position
    abs_target_x = int(target_x * 65535 / screen_width)
    abs_target_y = int(target_y * 65535 / screen_height)
    send_mouse_input(0x8001, abs_target_x, abs_target_y)
    time.sleep(0.01)
    
    # Nuclear click (undetectable)
    send_mouse_input(0x0002)  # MOUSEEVENTF_LEFTDOWN
    time.sleep(random.uniform(*CLICK_HOLD_RANGE))
    send_mouse_input(0x0004)  # MOUSEEVENTF_LEFTUP
    
    # Natural post-click movement
    time.sleep(0.01)
    move_x = target_x + random.randint(-3, 3)
    move_y = target_y + random.randint(-3, 3)
    abs_move_x = int(move_x * 65535 / screen_width)
    abs_move_y = int(move_y * 65535 / screen_height)
    send_mouse_input(0x8001, abs_move_x, abs_move_y)

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

                # Use combined human-like movement with nuclear click
                human_like_click(int(center_x), int(center_y))
                print(f"Clicked on circle at ({center_x}, {center_y})")
                
                # Natural delay between clicks
                time.sleep(random.uniform(*BETWEEN_CLICKS_RANGE))

        if matches_found:
            cv2.imwrite('debug_matches.png', debug_img)
            print("Debug image saved as 'debug_matches.png' showing detected circles.")

        time.sleep(random.uniform(*MAIN_LOOP_RANGE))

if __name__ == "__main__":
    print("Starting ULTIMATE circle click macro - Smooth + Nuclear")
    print("Timing Ranges:")
    print(f"  - Hover Time: {HOVER_TIME_RANGE[0]*1000:.0f}-{HOVER_TIME_RANGE[1]*1000:.0f}ms")
    print(f"  - Jitter Time: {JITTER_TIME_RANGE[0]*1000:.0f}-{JITTER_TIME_RANGE[1]*1000:.0f}ms")
    print(f"  - Click Hold: {CLICK_HOLD_RANGE[0]*1000:.0f}-{CLICK_HOLD_RANGE[1]*1000:.0f}ms")
    print(f"  - Between Clicks: {BETWEEN_CLICKS_RANGE[0]*1000:.0f}-{BETWEEN_CLICKS_RANGE[1]*1000:.0f}ms")
    print(f"  - Main Loop: {MAIN_LOOP_RANGE[0]*1000:.0f}-{MAIN_LOOP_RANGE[1]*1000:.0f}ms")
    print("\nMovement Settings:")
    print(f"  - Min Steps: {MIN_STEPS}")
    print(f"  - Max Steps: {MAX_STEPS}")
    print(f"  - Step Sleep: {STEP_SLEEP_TIME*1000:.0f}ms")
    print(f"  - Curve Strength: {CURVE_STRENGTH_RANGE[0]}-{CURVE_STRENGTH_RANGE[1]} pixels")
    print("\nControls:")
    print("  - Press N to PAUSE/RESUME")
    print("  - Press Ctrl+N to STOP the script completely")
    click_on_patterns()