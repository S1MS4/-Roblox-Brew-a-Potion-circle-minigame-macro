import sys
import pyautogui
import cv2
import numpy as np
import time
import keyboard
import random
import ctypes
from ctypes import wintypes
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont

# ===== CONFIGURATION =====
# Human-like Mode Configuration
HUMAN_HOVER_TIME_RANGE = (0.015, 0.025)
HUMAN_JITTER_TIME_RANGE = (0.008, 0.012)
HUMAN_CLICK_HOLD_RANGE = (0.015, 0.025)
HUMAN_BETWEEN_CLICKS_RANGE = (0.04, 0.06)
HUMAN_MAIN_LOOP_RANGE = (0.04, 0.06)
HUMAN_MIN_STEPS = 8
HUMAN_MAX_STEPS = 20
HUMAN_STEPS_DISTANCE_DIVISOR = 10
HUMAN_STEP_SLEEP_TIME = 0.005
HUMAN_CURVE_STRENGTH_RANGE = (1, 3)

# Fast Click Mode Configuration
FAST_HOVER_TIME_RANGE = (0.0015, 0.0025)
FAST_JITTER_TIME_RANGE = (0.0008, 0.0012)
FAST_CLICK_HOLD_RANGE = (0.0015, 0.0025)
FAST_BETWEEN_CLICKS_RANGE = (0.004, 0.006)
FAST_MAIN_LOOP_RANGE = (0.004, 0.006)

# Circle Detection
MIN_RADIUS = 50
MAX_RADIUS = 60

# ===== WINDOWS API SETUP =====
user32 = ctypes.windll.user32

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

# ===== CLICKING THREAD =====
class ClickingThread(QThread):
    status_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.paused = True
        self.should_exit = False
        self.current_mode = "human_like"
        self.click_count = 0
        self.circles_detected = 0
        self.start_time = None
        
    def toggle_pause(self):
        self.paused = not self.paused
        status = "OFF" if self.paused else "ON"
        self.status_update.emit(status)
        
    def set_mode(self, mode):
        self.current_mode = mode
        
    def stop_clicking(self):
        self.should_exit = True
        
    def wait_while_paused(self):
        while self.paused and not self.should_exit:
            time.sleep(0.1)
    
    def smooth_human_movement(self, target_x, target_y):
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        
        current_x, current_y = pyautogui.position()
        distance = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)
        steps = max(HUMAN_MIN_STEPS, min(HUMAN_MAX_STEPS, int(distance / HUMAN_STEPS_DISTANCE_DIVISOR)))
        
        for i in range(steps):
            if self.should_exit:
                return
                
            progress = i / steps
            if progress < 0.5:
                ease = 2 * progress * progress
            else:
                ease = 1 - math.pow(-2 * progress + 2, 2) / 2
            
            curve_factor = math.sin(progress * math.pi) * random.uniform(*HUMAN_CURVE_STRENGTH_RANGE)
            curve_x = random.choice([-1, 1]) * curve_factor
            curve_y = random.choice([-1, 1]) * curve_factor
            
            inter_x = current_x + (target_x - current_x) * ease + curve_x
            inter_y = current_y + (target_y - current_y) * ease + curve_y
            
            abs_x = int(inter_x * 65535 / screen_width)
            abs_y = int(inter_y * 65535 / screen_height)
            send_mouse_input(0x8001, abs_x, abs_y)
            
            time.sleep(HUMAN_STEP_SLEEP_TIME)
        
        abs_target_x = int(target_x * 65535 / screen_width)
        abs_target_y = int(target_y * 65535 / screen_height)
        send_mouse_input(0x8001, abs_target_x, abs_target_y)

    def human_like_click(self, x, y):
        target_x = x + random.randint(-3, 3)
        target_y = y + random.randint(-3, 3)
        
        self.smooth_human_movement(target_x, target_y)
        
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        
        time.sleep(random.uniform(*HUMAN_HOVER_TIME_RANGE))
        
        for _ in range(random.randint(1, 2)):
            if self.should_exit:
                return
            jitter_x = target_x + random.randint(-2, 2)
            jitter_y = target_y + random.randint(-2, 2)
            abs_jitter_x = int(jitter_x * 65535 / screen_width)
            abs_jitter_y = int(jitter_y * 65535 / screen_height)
            send_mouse_input(0x8001, abs_jitter_x, abs_jitter_y)
            time.sleep(random.uniform(*HUMAN_JITTER_TIME_RANGE))
        
        abs_target_x = int(target_x * 65535 / screen_width)
        abs_target_y = int(target_y * 65535 / screen_height)
        send_mouse_input(0x8001, abs_target_x, abs_target_y)
        time.sleep(0.01)
        
        send_mouse_input(0x0002)
        time.sleep(random.uniform(*HUMAN_CLICK_HOLD_RANGE))
        send_mouse_input(0x0004)
        
        time.sleep(0.01)
        move_x = target_x + random.randint(-3, 3)
        move_y = target_y + random.randint(-3, 3)
        abs_move_x = int(move_x * 65535 / screen_width)
        abs_move_y = int(move_y * 65535 / screen_height)
        send_mouse_input(0x8001, abs_move_x, abs_move_y)

    def fast_undetectable_click(self, x, y):
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        
        abs_x = int(x * 65535 / screen_width)
        abs_y = int(y * 65535 / screen_height)
        
        send_mouse_input(0x8001, abs_x, abs_y)
        time.sleep(random.uniform(*FAST_HOVER_TIME_RANGE))
        
        jitter_x = random.randint(-1, 1)
        jitter_y = random.randint(-1, 1)
        jitter_abs_x = int((x + jitter_x) * 65535 / screen_width)
        jitter_abs_y = int((y + jitter_y) * 65535 / screen_height)
        send_mouse_input(0x8001, jitter_abs_x, jitter_abs_y)
        time.sleep(random.uniform(*FAST_JITTER_TIME_RANGE))
        
        send_mouse_input(0x8001, abs_x, abs_y)
        time.sleep(random.uniform(*FAST_JITTER_TIME_RANGE))
        
        send_mouse_input(0x0002)
        time.sleep(random.uniform(*FAST_CLICK_HOLD_RANGE))
        send_mouse_input(0x0004)

    def run(self):
        self.start_time = time.time()
        
        while not self.should_exit:
            self.wait_while_paused()
            if self.should_exit:
                break

            # Take screenshot and process
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)

            if self.should_exit:
                break
            self.wait_while_paused()
            if self.should_exit:
                break

            # Detect circles
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 80,
                                      param1=80, param2=50,
                                      minRadius=MIN_RADIUS, maxRadius=MAX_RADIUS)

            if circles is not None:
                circles = np.uint16(np.around(circles))
                
                for i in circles[0, :]:
                    if self.should_exit:
                        return
                    self.wait_while_paused()
                    if self.should_exit:
                        return

                    center_x, center_y, radius = i[0], i[1], i[2]

                    # Choose click method based on current mode
                    click_x = int(center_x) + random.randint(-2, 2)
                    click_y = int(center_y) + random.randint(-2, 2)
                    
                    if self.current_mode == "human_like":
                        self.human_like_click(click_x, click_y)
                        delay_range = HUMAN_BETWEEN_CLICKS_RANGE
                    else:
                        self.fast_undetectable_click(click_x, click_y)
                        delay_range = FAST_BETWEEN_CLICKS_RANGE
                    
                    self.click_count += 1
                    
                    time.sleep(random.uniform(*delay_range))

            # Main loop delay based on mode
            delay_range = HUMAN_MAIN_LOOP_RANGE if self.current_mode == "human_like" else FAST_MAIN_LOOP_RANGE
            time.sleep(random.uniform(*delay_range))

# ===== GUI WINDOW =====
class CircleClickerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.clicking_thread = ClickingThread()
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        self.setWindowTitle("Circle Clicker")
        self.setFixedSize(200, 80)
        
        # Set always on top
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555555;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QComboBox {
                background-color: #404040;
                color: #cccccc;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 3px;
                min-width: 80px;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #cccccc;
                border: 1px solid #666666;
                selection-background-color: #555555;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Status indicator
        self.status_label = QLabel("OFF")
        self.status_label.setStyleSheet("font-size: 12px; color: #ff4444;")
        self.status_label.setFixedWidth(30)
        
        # Mode selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Human-like", "Instaclick"])
        self.mode_combo.setFixedWidth(80)
        
        # Toggle button
        self.toggle_button = QPushButton("START")
        self.toggle_button.setFixedWidth(60)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.toggle_button)
        
    def setup_connections(self):
        # Button connections
        self.toggle_button.clicked.connect(self.toggle_pause)
        self.mode_combo.currentTextChanged.connect(self.change_mode)
        
        # Thread connections
        self.clicking_thread.status_update.connect(self.update_status)
        
        # Setup keyboard hotkeys
        keyboard.add_hotkey('n', self.toggle_pause)
        keyboard.add_hotkey('tab', self.switch_mode_combo)
        
    def toggle_pause(self):
        self.clicking_thread.toggle_pause()
        
    def switch_mode_combo(self):
        current_index = self.mode_combo.currentIndex()
        new_index = 1 if current_index == 0 else 0
        self.mode_combo.setCurrentIndex(new_index)
        
    def change_mode(self, mode_text):
        mode = "human_like" if mode_text == "Human-like" else "fast_click"
        self.clicking_thread.set_mode(mode)
        
    def update_status(self, status):
        self.status_label.setText(status)
        if status == "ON":
            self.status_label.setStyleSheet("font-size: 12px; color: #4CAF50;")
            self.toggle_button.setText("STOP")
        else:
            self.status_label.setStyleSheet("font-size: 12px; color: #ff4444;")
            self.toggle_button.setText("START")
            
    def stop_program(self):
        self.clicking_thread.stop_clicking()
        if self.clicking_thread.isRunning():
            self.clicking_thread.wait(2000)
        QApplication.quit()
        
    def closeEvent(self, event):
        self.stop_program()
        event.accept()
        
    def start_clicking(self):
        if not self.clicking_thread.isRunning():
            self.clicking_thread.start()

# ===== MAIN APPLICATION =====
def main():
    app = QApplication(sys.argv)
    
    # Create and show GUI
    gui = CircleClickerGUI()
    gui.show()
    gui.start_clicking()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()