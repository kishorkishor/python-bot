"""Kishor Farm Merger Pro GUI module - Flet Edition with Glassmorphism."""

import json
import multiprocessing
import os
import threading
import time
from datetime import datetime
from multiprocessing import Process, Queue
from typing import List

import cv2
import flet as ft
import keyboard
import numpy as np
from pyautogui_safe import pyautogui
import queue as thread_queue
from PIL import Image

from item_finder import ImageFinder
from merging_points_selector import MergingPointsSelector
from screen_area_selector import ScreenAreaSelector
from template_collector import TemplateCollector

# GPU detection
def check_gpu_available():
    """Check if GPU acceleration (OpenCL) is available."""
    try:
        import cv2
        # Try to create a UMat to test OpenCL
        test_img = cv2.UMat(np.zeros((10, 10, 3), dtype=np.uint8))
        cv2.UMat.get(test_img)  # Get it back
        return True
    except:
        return False

# Live detection overlay
try:
    from live_detection_overlay import LiveDetectionManager
    LIVE_DETECTION_AVAILABLE = True
except ImportError:
    LIVE_DETECTION_AVAILABLE = False
    LiveDetectionManager = None

# Unified GUI Integration
try:
    from unified_gui_integration import add_automation_and_tests_tabs
    UNIFIED_INTEGRATION_AVAILABLE = True
except ImportError:
    UNIFIED_INTEGRATION_AVAILABLE = False
    add_automation_and_tests_tabs = None

# Import all global variables and callbacks from gui.py
# We'll import these to preserve functionality
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# LogQueue for process communication
class LogQueue:
    def __init__(self):
        self.queue = Queue()
    
    def get_queue(self):
        return self.queue

queue = LogQueue()

# Global variables (same as gui.py)
p = None
stop_event = None
start_hotkey_handle = None
is_merge_running = False

merge_count = 5
area = tuple()
hotkey = {"="}
stop_hotkey = {"="}
merging_points = []
resize_factor = 1.2
drag_duration_seconds = 0.55
box_button_point = tuple()
box_amount = 6
board_rows = 9
board_cols = 9
board_slots = []
slot_overrides = {}
disallowed_slots = set()
sort_plan = []
auto_board_detection_enabled = True
box_counter_region = tuple()
last_detected_grid_summary = ""
last_detected_grid_color = (132, 140, 165, 255)
box_counter_last_value = None
last_box_counter_read_time = 0.0
box_counter_failure_logged = False
tesseract_status = {"available": None, "message": "", "checked_at": 0.0}

# Detection mode and threshold settings
detection_mode = "cpu"  # "cpu", "gpu", "hybrid", or "express"
global_threshold = 0.75  # Global threshold (0.50 - 0.95)

# Resource tracking
resource_regions = {
    "coins": tuple(),
    "gems": tuple(),
    "thunder": tuple(),
}
resource_values = {
    "coins": 0,
    "gems": 0,
    "thunder": 0,
}
resource_tracking_enabled = False

# Glassmorphism Color Palette
BACKGROUND = "#12121C"
GLASS_BG = "rgba(52, 58, 82, 0.4)"
GLASS_BG_DARK = "rgba(36, 40, 56, 0.5)"
GLASS_BORDER = "rgba(160, 200, 255, 0.3)"
GLASS_HOVER = "rgba(88, 178, 255, 0.5)"
ACCENT_BLUE = "#58B2FF"
ACCENT_BLUE_LIGHT = "#78C8FF"
ACCENT_BLUE_DARK = "#3480E0"
PURPLE = "#A05AFF"
PURPLE_LIGHT = "#B070FF"
SUCCESS_GREEN = "#4CD964"
WARNING_ORANGE = "#FFB800"
DANGER_RED = "#FF5A5F"
TEXT_PRIMARY = "#FFFFFF"
TEXT_MUTED = "#B4BED2"
TEXT_SUBTLE = "#828CA0"

CONFIG_FILE = "farm_merger_config.json"

# ============================================================================
# Helper Functions (from gui.py)
# ============================================================================

def get_image_file_paths(folder):
    """Get all image file paths from folder and subdirectories"""
    if not os.path.exists(folder):
        return []
    image_files = []
    for root, dirs, files in os.walk(folder):
        for name in files:
            if name.endswith((".png", ".jpg", ".jpeg")):
                image_files.append(os.path.join(root, name))
    return sorted(image_files, reverse=True)


def apply_slot_overrides():
    """Apply slot coordinate overrides to board_slots"""
    global board_slots
    if not board_slots:
        return
    
    for slot in board_slots:
        default_center = slot.get("default_center") or slot.get("center")
        slot["default_center"] = default_center
        override = slot_overrides.get(slot["id"])
        if override:
            slot["center"] = tuple(override)
        else:
            slot["center"] = tuple(default_center)


def auto_detect_board_geometry(area_rect, detection_points):
    """Auto-detect board rows/cols from detection points"""
    if len(area_rect) != 4 or not detection_points or len(detection_points) < 4:
        return None

    start_x, start_y, end_x, end_y = area_rect
    width = max(1, end_x - start_x)
    height = max(1, end_y - start_y)

    def _cluster_axis_counts(values):
        if not values:
            return 0, [], 0.0
        sorted_values = sorted(values)
        if len(sorted_values) < 2:
            return 1, [float(sorted_values[0])], 0.0
        diffs = [sorted_values[i + 1] - sorted_values[i] for i in range(len(sorted_values) - 1)]
        positive_diffs = [diff for diff in diffs if diff > 3]
        if positive_diffs:
            spacing_estimate = float(np.median(positive_diffs))
        else:
            spacing_estimate = float(max(diffs)) if diffs else 0.0
        tolerance = max(12.0, spacing_estimate * 0.45) if spacing_estimate else 24.0
        clusters = [[sorted_values[0]]]
        for value in sorted_values[1:]:
            if abs(value - clusters[-1][-1]) <= tolerance:
                clusters[-1].append(value)
            else:
                clusters.append([value])
        centers = [sum(cluster) / len(cluster) for cluster in clusters]
        return len(centers), centers, spacing_estimate

    col_count, _, spacing_x = _cluster_axis_counts([pt[0] for pt in detection_points])
    row_count, _, spacing_y = _cluster_axis_counts([pt[1] for pt in detection_points])

    if col_count < 2 or row_count < 2:
        return None

    if spacing_x > 0:
        estimated_cols = int(round(width / spacing_x))
        col_count = max(col_count, estimated_cols)

    if spacing_y > 0:
        estimated_rows = int(round(height / spacing_y))
        row_count = max(row_count, estimated_rows)

    col_count = max(1, min(20, col_count))
    row_count = max(1, min(20, row_count))

    return {"rows": row_count, "cols": col_count}


def detect_board_layout(area_rect, rows, cols, resize):
    """Detect board layout and create slot map"""
    global board_rows, board_cols, last_detected_grid_summary, last_detected_grid_color
    
    if len(area_rect) != 4:
        last_detected_grid_summary = "Set the screen area before scanning the board."
        return []

    start_x, start_y, end_x, end_y = area_rect
    width = max(1, end_x - start_x)
    height = max(1, end_y - start_y)

    img_folder = "./img"
    template_paths = get_image_file_paths(img_folder)

    template_points = {}
    aggregated_points = []

    for template_path in template_paths:
        template_name = os.path.basename(template_path)
        points, _ = ImageFinder.find_image_on_screen(
            template_path,
            start_x, start_y, end_x, end_y,
            resize,
        )
        template_points[template_name] = points
        aggregated_points.extend(points)

    detection_summary = ""
    detection_color = (130, 140, 160, 255)  # TEXT_SUBTLE
    detection_updated = False

    if auto_board_detection_enabled:
        geometry = auto_detect_board_geometry(area_rect, aggregated_points)
        if geometry:
            rows = geometry["rows"]
            cols = geometry["cols"]
            detection_summary = f"Auto detected {rows}x{cols} grid ({len(aggregated_points)} matches)"
            detection_color = (76, 217, 100, 255)  # SUCCESS_COLOR
            if board_rows != rows or board_cols != cols:
                board_rows = rows
                board_cols = cols
                detection_updated = True
        else:
            detection_summary = "Auto detection failed - using manual grid."
            detection_color = (255, 184, 0, 255)  # WARNING_COLOR
    else:
        detection_summary = f"Manual grid: {rows}x{cols}"
        detection_color = (130, 140, 160, 255)  # TEXT_SUBTLE

    rows = int(rows)
    cols = int(cols)

    if rows <= 0 or cols <= 0:
        last_detected_grid_summary = "Unable to determine grid."
        return []

    cell_w = width / cols
    cell_h = height / rows

    slot_map = {}

    for r in range(rows):
        for c in range(cols):
            slot_id = f"{r}-{c}"
            center_x = int(start_x + (c + 0.5) * cell_w)
            center_y = int(start_y + (r + 0.5) * cell_h)
            slot_map[(r, c)] = {
                "id": slot_id,
                "row": r,
                "col": c,
                "default_center": (center_x, center_y),
                "center": (center_x, center_y),
                "type": None,
                "template": None,
                "detected_center": None,
            }
            override = slot_overrides.get(slot_id)
            if override and len(override) == 2:
                slot_map[(r, c)]["center"] = tuple(override)

    for template_path in template_paths:
        template_name = os.path.basename(template_path)
        points = template_points.get(template_name, [])
        for point in points:
            px, py = point
            col = min(cols - 1, max(0, int((px - start_x) / cell_w)))
            row = min(rows - 1, max(0, int((py - start_y) / cell_h)))
            slot = slot_map[(row, col)]
            if slot["type"] is None:
                slot["type"] = template_name
                slot["template"] = template_path
                slot["detected_center"] = point
            else:
                slot.setdefault("duplicates", []).append(
                    {"type": template_name, "template": template_path, "center": point}
                )

    last_detected_grid_summary = detection_summary
    last_detected_grid_color = detection_color

    if detection_updated:
        save_config()

    return [
        {
            **slot,
            "allowed": slot["id"] not in disallowed_slots,
        }
        for slot in slot_map.values()
    ]


def find_tesseract_path():
    """Try to find Tesseract installation path"""
    import os
    import platform
    
    # Common installation paths
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tesseract-OCR", "tesseract.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Tesseract-OCR", "tesseract.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Tesseract-OCR", "tesseract.exe"),
    ]
    
    # Also check PATH
    path_env = os.environ.get("PATH", "").split(os.pathsep)
    for path_dir in path_env:
        tesseract_exe = os.path.join(path_dir, "tesseract.exe")
        if os.path.exists(tesseract_exe):
            return tesseract_exe
    
    # Check common paths
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None


def is_tesseract_ready_inline(force=False):
    """Check if Tesseract OCR is available"""
    global tesseract_status
    try:
        import pytesseract
        
        # Try to configure pytesseract with found path if not already set
        if not hasattr(pytesseract, '_tesseract_configured'):
            tesseract_path = find_tesseract_path()
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                pytesseract._tesseract_configured = True
        
        pytesseract.get_tesseract_version()
        return True, ""
    except ImportError:
        return False, "Install pytesseract: pip install pytesseract"
    except Exception as e:
        error_msg = str(e)
        if "not installed" in error_msg.lower() or "not in your path" in error_msg.lower():
            # Try to find and configure it
            tesseract_path = find_tesseract_path()
            if tesseract_path:
                try:
                    import pytesseract
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    pytesseract._tesseract_configured = True
                    pytesseract.get_tesseract_version()
                    return True, ""
                except:
                    pass
            return False, "Tesseract OCR not installed. Download from: https://github.com/UB-Mannheim/tesseract/wiki"
        return False, f"Tesseract error: {error_msg}"


def read_resource_value(region):
    """Read numeric value from screen region using OCR"""
    if not region or len(region) != 4:
        log_message("[debug] Resource region not set or invalid")
        return None
    
    x, y, width, height = region
    if width <= 0 or height <= 0:
        log_message(f"[debug] Invalid region dimensions: {width}x{height}")
        return None
    
    # Check Tesseract availability
    available, message = is_tesseract_ready_inline()
    if not available:
        log_message(f"[warn] OCR not available: {message}")
        return None
    
    try:
        log_message(f"[debug] Reading resource from region: ({x}, {y}, {width}, {height})")
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        frame = cv2.resize(frame, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        frame = cv2.GaussianBlur(frame, (3, 3), 0)
        _, thresh = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        import pytesseract
        text = pytesseract.image_to_string(thresh, config="--psm 7")
        log_message(f"[debug] OCR raw text: '{text}'")
        
        # Extract digits, handle K/M suffixes
        text = text.strip().upper().replace(',', '').replace('.', '')
        multiplier = 1
        if 'K' in text:
            multiplier = 1000
            text = text.replace('K', '')
        elif 'M' in text:
            multiplier = 1000000
            text = text.replace('M', '')
        
        import re
        digits = re.findall(r'\d+', text)
        if digits:
            value = int(digits[0]) * multiplier
            log_message(f"[debug] Parsed value: {value}")
            return value
        else:
            log_message(f"[debug] No digits found in text: '{text}'")
    except pytesseract.pytesseract.TesseractNotFoundError:
        log_message("[error] Tesseract not found. Install Tesseract OCR.")
    except Exception as exc:
        log_message(f"[error] OCR error: {exc}")
        import traceback
        log_message(f"[error] Traceback: {traceback.format_exc()}")
    return None


def update_log_message():
    """Update log messages from queue"""
    global box_amount
    current_log = ""
    messages = []
    while not queue.get_queue().empty():
        messages.append(queue.get_queue().get())
    
    for message in messages:
        if message.startswith("BOX_DECREMENT|"):
            try:
                decrement = int(message.split("|")[1])
                box_amount = max(0, box_amount - decrement)
                log_message(f"[info] Boxes remaining: {box_amount}")
            except:
                pass
        else:
            log_message(message)


# ============================================================================
# Merge Core Functions (from gui.py)
# ============================================================================

def validate_merge_parameters(area_rect, scale, count, points):
    """Validate merge parameters before starting"""
    if len(area_rect) != 4:
        log_message("[error] Screen area not configured.")
        return False
    if scale <= 0:
        log_message("[error] Resize factor must be greater than zero.")
        return False
    if len(points) < count - 1:
        log_message(f"[error] Not enough merge points. Expected {count - 1}, received {len(points)}.")
        return False
    if not os.path.exists("./img"):
        log_message("[error] img folder not found. Please ensure image files are present.")
        return False
    if not any(f.endswith(('.png', '.jpg', '.jpeg')) for f in os.listdir("./img")):
        log_message("[error] No image files found in img folder.")
        return False
    return True


def perform_merge_operations(template_centers, points, count, queue_log, drag_duration):
    """Perform the drag operations for merging"""
    for idx in range(count):
        start_x, start_y = template_centers[idx]
        end_x, end_y = points[idx % (count - 1)]
        pyautogui.mouseUp()
        pyautogui.moveTo(start_x, start_y)
        pyautogui.mouseDown()
        pyautogui.moveTo(end_x, end_y, duration=drag_duration)
        pyautogui.mouseUp()
        time.sleep(0.05)


def perform_box_clicks_at_point(point, queue_log, num_clicks=5):
    """Perform box clicks at specified point"""
    if not point or len(point) != 2:
        queue_log("[error] Box button point not configured.")
        return
    x, y = point
    num_clicks = max(1, min(num_clicks, 5))
    interval = 0.3
    for _ in range(num_clicks):
        pyautogui.moveTo(x, y, duration=0.05)
        pyautogui.click()
        time.sleep(interval)


def perform_merge_cycle(image_files, area_rect, scale, count, points, queue_log, drag_duration):
    """Enhanced merge cycle with priority-based merging"""
    producer_templates = []
    regular_templates = []
    
    for target_image in image_files:
        basename = os.path.basename(target_image).lower()
        if any(keyword in basename for keyword in ['chicken', 'cow', 'sheep', 'wheat', 'corn', 'producer']):
            producer_templates.append(target_image)
        else:
            regular_templates.append(target_image)
    
    prioritized_templates = producer_templates + regular_templates
    
    for target_image in prioritized_templates:
        template_centers, _ = ImageFinder.find_image_on_screen(target_image, *area_rect, scale)
        if template_centers:
            queue_log(f"[info] Found {len(template_centers)} matches for {os.path.basename(target_image)}.")
        if len(template_centers) > count - 1 and len(points) >= count - 1:
            perform_merge_operations(template_centers, points, count, queue_log, drag_duration)
            queue_log("[info] Drag operations completed.")
            return True
    return False


def start_merge(log_queue, area_rect, scale, count, points, cancel_keys, box_point, drag_duration, stop_signal, initial_box_amount):
    """Main merge process function"""
    def queue_log(message):
        log_queue.put(message)

    stop_flag = {"active": False}
    local_box_amount = initial_box_amount

    def mark_stop():
        stop_flag["active"] = True
        if stop_signal is not None:
            stop_signal.set()
        queue_log("[info] Stop hotkey pressed. Finishing current cycle.")

    if stop_signal is not None:
        stop_signal.clear()

    stop_hotkey_handle = keyboard.add_hotkey("+".join(sorted(cancel_keys)), mark_stop)
    queue_log("[info] Loading templates.")
    image_files = get_image_file_paths("./img")

    if not validate_merge_parameters(area_rect, scale, count, points):
        return

    queue_log("[info] Merge cycle started with self-healing enabled.")
    consecutive_failures = 0
    max_failures_before_rescan = 2
    
    while not stop_flag["active"] and (stop_signal is None or not stop_signal.is_set()):
        merge_success = perform_merge_cycle(image_files, area_rect, scale, count, points, queue_log, drag_duration)
        
        if merge_success:
            consecutive_failures = 0
            continue
        else:
            consecutive_failures += 1
            if consecutive_failures >= max_failures_before_rescan:
                queue_log("[info] Self-healing: Rescanning board after failed cycles...")
                time.sleep(1.0)
                consecutive_failures = 0
                if perform_merge_cycle(image_files, area_rect, scale, count, points, queue_log, drag_duration):
                    continue
        
        if local_box_amount <= 0:
            queue_log("[info] No boxes available. Continuing without box clicks...")
            time.sleep(2.0)
            continue
        
        clicks_to_make = min(local_box_amount, 5)
        queue_log(f"BOX_DECREMENT|{clicks_to_make}")
        perform_box_clicks_at_point(box_point, queue_log, clicks_to_make)
        local_box_amount -= clicks_to_make

    try:
        keyboard.remove_hotkey(stop_hotkey_handle)
    except KeyError:
        pass
    queue_log("[info] Stop request acknowledged.")


# ============================================================================
# Core Merge Process Functions
# ============================================================================

def terminate_merge_process(force=False):
    """Terminate the merge process"""
    global p, stop_event, is_merge_running
    if p is None:
        return

    pyautogui.mouseUp()
    if stop_event is not None:
        stop_event.set()

    if p.is_alive():
        p.terminate()
        p.join(timeout=0.5)
        if p.is_alive():
            p.kill()
            p.join()

    update_log_message()
    p = None
    is_merge_running = False
    if stop_event is not None:
        stop_event.clear()
        stop_event = None


def start_merge_process():
    """Start the merge automation process"""
    global p, stop_hotkey, area, resize_factor, merge_count, merging_points
    global box_button_point, box_amount, drag_duration_seconds, stop_event, is_merge_running

    if p is not None and p.is_alive():
        log_message("[warn] Merge process already running.")
        return

    if len(box_button_point) != 2 or box_amount is None:
        log_message("[error] Configure box button and amount first.")
        return
    if box_amount < 0:
        log_message("[warn] Invalid box amount.")
        return

    stop_event = multiprocessing.Event()
    log_message(f"[info] Starting with {box_amount} box(es)...")
    
    process = Process(
        target=start_merge,
        args=(
            queue.get_queue(),
            area,
            resize_factor,
            merge_count,
            merging_points,
            stop_hotkey,
            box_button_point,
            drag_duration_seconds,
            stop_event,
            box_amount,
        ),
    )
    
    p = process
    process.start()
    is_merge_running = True
    
    # Start background thread to poll log messages
    def poll_log_messages():
        while process.is_alive():
            update_log_message()
            time.sleep(0.1)
        update_log_message()
        log_message("[info] Merge process stopped.")
        global p
        p = None
        is_merge_running = False
        if stop_event is not None:
            stop_event.clear()
            stop_event = None
    
    log_thread = threading.Thread(target=poll_log_messages, daemon=True)
    log_thread.start()


def toggle_merge_process():
    """Instant toggle - start if stopped, stop if running."""
    global p, is_merge_running
    if is_merge_running and p is not None and p.is_alive():
        log_message("[info] Stopping...")
        terminate_merge_process()
        is_merge_running = False
    else:
        log_message("[info] Starting...")
        start_merge_process()
        is_merge_running = True


def format_hotkey_label(keys):
    """Format hotkey set as display string"""
    if not keys:
        return "Select hotkey"
    return "+".join(sorted(keys))


LOG_BACKLOG_LIMIT = 200
_log_callback = None
_pending_log_messages = []

def log_message(message, level="info"):
    """Log a message - adapter for Flet"""
    print(message)
    if _log_callback:
        _log_callback(message, level)
    else:
        _pending_log_messages.append((message, level))
        if len(_pending_log_messages) > LOG_BACKLOG_LIMIT:
            _pending_log_messages.pop(0)


def save_config():
    """Save configuration to JSON file"""
    config = {
        "merge_count": merge_count,
        "area": list(area) if area else [],
        "hotkey": list(hotkey),
        "stop_hotkey": list(stop_hotkey),
        "merging_points": merging_points,
        "resize_factor": resize_factor,
        "drag_duration_seconds": drag_duration_seconds,
        "box_button_point": list(box_button_point) if box_button_point else [],
        "box_amount": box_amount,
        "box_counter_region": list(box_counter_region) if box_counter_region else [],
        "resource_regions": {
            "coins": list(resource_regions.get("coins", [])) if resource_regions.get("coins") else [],
            "gems": list(resource_regions.get("gems", [])) if resource_regions.get("gems") else [],
            "thunder": list(resource_regions.get("thunder", [])) if resource_regions.get("thunder") else [],
        },
        "advanced_settings": {
            "board_rows": board_rows,
            "board_cols": board_cols,
            "disallowed_slots": list(disallowed_slots),
            "slot_overrides": {slot_id: list(coords) for slot_id, coords in slot_overrides.items()},
            "auto_board_detection": auto_board_detection_enabled,
        },
        "detection_settings": {
            "detection_mode": detection_mode,
            "global_threshold": global_threshold,
        },
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        log_message("[info] Configuration saved.")
    except Exception as exc:
        log_message(f"[error] Unable to save configuration: {exc}")


def load_config():
    """Load configuration from JSON file"""
    global merge_count, area, hotkey, stop_hotkey, merging_points
    global resize_factor, drag_duration_seconds, box_button_point
    global box_amount, board_rows, board_cols, disallowed_slots
    global slot_overrides, auto_board_detection_enabled, box_counter_region
    global resource_regions, detection_mode, global_threshold
    
    if not os.path.exists(CONFIG_FILE):
        log_message("[info] No saved configuration found. Using defaults.")
        return
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        merge_count = config.get("merge_count", 5)
        area = tuple(config.get("area", [])) if config.get("area") else tuple()
        hotkey = set(config.get("hotkey", ["="]))
        stop_hotkey = set(config.get("stop_hotkey", ["="]))
        merging_points = config.get("merging_points", [])
        resize_factor = config.get("resize_factor", 1.2)
        drag_duration_seconds = config.get("drag_duration_seconds", 0.55)
        box_button_point = tuple(config.get("box_button_point", [])) if config.get("box_button_point") else tuple()
        box_amount = config.get("box_amount", 6)
        box_counter_region = tuple(config.get("box_counter_region", [])) if config.get("box_counter_region") else tuple()
        
        if LIVE_DETECTION_AVAILABLE and live_detection_manager:
            if area:
                live_detection_manager.update_game_area(area)
            live_detection_manager.set_resize_factor(resize_factor)
        
        # Load resource regions
        if "resource_regions" in config:
            res_regions = config["resource_regions"]
            # Convert list back to tuple, ensuring we have 4 values
            for res_type in ["coins", "gems", "thunder"]:
                region_list = res_regions.get(res_type, [])
                if region_list and len(region_list) == 4:
                    resource_regions[res_type] = tuple(region_list)
                    log_message(f"[info] Loaded {res_type} region: {resource_regions[res_type]}")
                else:
                    resource_regions[res_type] = tuple()
        
        if "advanced_settings" in config:
            adv = config["advanced_settings"]
            board_rows = adv.get("board_rows", 9)
            board_cols = adv.get("board_cols", 9)
            disallowed_slots = set(adv.get("disallowed_slots", []))
            slot_overrides = {k: tuple(v) for k, v in adv.get("slot_overrides", {}).items()}
            auto_board_detection_enabled = adv.get("auto_board_detection", True)
        
        # Load detection settings
        if "detection_settings" in config:
            det_settings = config["detection_settings"]
            detection_mode = det_settings.get("detection_mode", "cpu")
            global_threshold = det_settings.get("global_threshold", 0.75)
            # Update catalog default threshold
            from item_finder import TEMPLATE_CATALOG
            TEMPLATE_CATALOG.set_default_threshold(global_threshold)
        
        log_message("[info] Configuration loaded successfully.")
    except Exception as exc:
        log_message(f"[error] Unable to load configuration: {exc}")


# Callback wrappers - these will call original functions when needed
def manual_save_callback_wrapper():
    """Save configuration callback"""
    try:
        save_config()
        log_message("[info] Settings saved successfully")
    except Exception as exc:
        log_message(f"[error] Failed to save settings: {exc}")


def manual_load_callback_wrapper():
    """Load configuration callback"""
    try:
        load_config()
        log_message("[info] Settings loaded successfully")
    except Exception as exc:
        log_message(f"[error] Failed to load settings: {exc}")


def select_area_callback_wrapper(page_ref, status_ref):
    """Wrapper for area selection"""
    def callback(e):
        try:
            selector = ScreenAreaSelector()
            coordinates = selector.get_coordinates()
            if coordinates and len(coordinates) == 4:
                global area
                area = coordinates
                if LIVE_DETECTION_AVAILABLE and live_detection_manager:
                    live_detection_manager.update_game_area(area)
                if status_ref and status_ref.current:
                    status_ref.current.value = f"Area: {coordinates[0]}x{coordinates[1]} → {coordinates[2]}x{coordinates[3]}"
                    status_ref.current.update()
                save_config()
                log_message(f"[info] Screen area selected: {coordinates}")
        except Exception as exc:
            log_message(f"[error] Area selection error: {exc}")
    return callback


def select_merging_points_callback_wrapper(page_ref, status_ref):
    """Wrapper for merging points selection"""
    def callback(e):
        try:
            selector = MergingPointsSelector(merge_count - 1)
            points = selector.get_points()
            if points:
                global merging_points
                merging_points = points
                if status_ref and status_ref.current:
                    status_ref.current.value = f"Selected {len(points)} merging points"
                    status_ref.current.update()
                save_config()
                log_message(f"[info] Selected {len(points)} merging points")
        except Exception as exc:
            log_message(f"[error] Merging points selection error: {exc}")
    return callback


def start_button_callback_wrapper(page_ref, status_ref):
    """Wrapper for start button - sets up hotkey monitoring"""
    def callback(e):
        try:
            global hotkey, start_hotkey_handle, is_merge_running
            if is_merge_running:
                log_message("[warn] Monitoring already enabled.")
                return
            
            log_message("[info] Monitoring enabled. Press = to start/stop instantly.")
            
            # Remove existing hotkey if any
            if start_hotkey_handle is not None:
                try:
                    keyboard.remove_hotkey(start_hotkey_handle)
                except KeyError:
                    pass
            
            # Set up hotkey to toggle merge process
            start_hotkey_handle = keyboard.add_hotkey("+".join(sorted(hotkey)), toggle_merge_process)
            is_merge_running = True
            
            if status_ref and status_ref.current:
                status_ref.current.value = "Monitoring - Press = to start"
                status_ref.current.color = WARNING_ORANGE
                status_ref.current.update()
                
        except Exception as exc:
            log_message(f"[error] Start button error: {exc}")
            if status_ref and status_ref.current:
                status_ref.current.value = f"Error: {str(exc)[:50]}"
                status_ref.current.color = DANGER_RED
                status_ref.current.update()
    return callback


def stop_button_callback_wrapper(page_ref, status_ref):
    """Wrapper for stop button - stops monitoring and merge process"""
    def callback(e):
        try:
            global start_hotkey_handle, is_merge_running
            log_message("[info] Monitoring disabled.")
            
            # Terminate any running merge process
            terminate_merge_process()
            is_merge_running = False
            
            # Remove hotkey
            if start_hotkey_handle is not None:
                try:
                    keyboard.remove_hotkey(start_hotkey_handle)
                except KeyError:
                    pass
                start_hotkey_handle = None
            
            if status_ref and status_ref.current:
                status_ref.current.value = "Stopped"
                status_ref.current.color = DANGER_RED
                status_ref.current.update()
                
        except Exception as exc:
            log_message(f"[error] Stop button error: {exc}")
            if status_ref and status_ref.current:
                status_ref.current.value = f"Error: {str(exc)[:50]}"
                status_ref.current.color = DANGER_RED
                status_ref.current.update()
    return callback


def update_merge_count_handler(e, status_ref):
    """Handle merge count radio button change"""
    try:
        global merge_count
        merge_count = int(e.control.value)
        save_config()
        if status_ref and status_ref.current:
            status_ref.current.value = f"Merge count set to {merge_count}"
            status_ref.current.update()
        log_message(f"[info] Merge count updated to {merge_count}")
    except Exception as exc:
        log_message(f"[error] Merge count handler error: {exc}")


def record_hotkey_simple(text_ref, status_ref, is_stop=False):
    """Simple hotkey recording"""
    def callback(e):
        try:
            global hotkey, stop_hotkey
            if status_ref and status_ref.current:
                status_ref.current.value = "Press keys for hotkey..."
                status_ref.current.color = WARNING_ORANGE
                status_ref.current.update()
            
            # Simple implementation - just set to =
            target_set = stop_hotkey if is_stop else hotkey
            target_set.clear()
            target_set.add("=")
            
            if text_ref and text_ref.current:
                text_ref.current.value = format_hotkey_label(target_set)
                text_ref.current.update()
            
            if status_ref and status_ref.current:
                status_ref.current.value = f"Hotkey set to {format_hotkey_label(target_set)}"
                status_ref.current.color = SUCCESS_GREEN
                status_ref.current.update()
            
            save_config()
            log_message(f"[info] Hotkey {'pause' if is_stop else 'start'} set to {format_hotkey_label(target_set)}")
        except Exception as exc:
            log_message(f"[error] Hotkey recording error: {exc}")
    return callback


def launch_template_collector(category, crop_size, status_queue: "thread_queue.Queue | None" = None):
    """Launch the template collector tool in a separate thread (non-blocking)"""
    def run_collector():
        try:
            if status_queue:
                status_queue.put(("start", category))
            log_message(f"[info] Launching template collector for {category}...")
            log_message(f"[info] Left-click items to capture, Right-click or ESC to exit")

            collector = TemplateCollector(category, crop_size)
            collector.start_capture_mode()

            if status_queue:
                status_queue.put(
                    (
                        "complete",
                        category,
                        collector.click_count,
                        [{"name": t["name"], "path": t["path"]} for t in collector.captured_templates],
                    )
                )
            log_message(f"[info] Template collection complete for {category}")
        except Exception as exc:
            if status_queue:
                status_queue.put(("error", category, str(exc)))
            log_message(f"[error] Template collector error: {exc}")
    
    # Run in separate thread so it doesn't block the main UI
    collector_thread = threading.Thread(target=run_collector, daemon=True)
    collector_thread.start()


# ============================================================================
# Scan and Detection Callbacks
# ============================================================================

# Global refs for detection UI
detection_items_container_ref = None
detection_total_ref = None
detection_types_ref = None
detected_count_text_ref = None
overlay_switch_ref = None
live_scan_switch_ref = None
detection_lock = threading.Lock()


def perform_detection_scan(silent: bool = False, skip_lock: bool = False):
    """Run the image scan and return detection data."""
    global last_detection_results, detection_lock
    
    # Only use lock for UI scans, not background live scans
    if not skip_lock:
        if detection_lock.locked():
            if not silent:
                log_message("[warn] Detection already in progress.")
            return None, 0
        detection_lock.acquire()
    
    try:
        if len(area) != 4:
            if not silent:
                log_message("[error] Set screen area first before scanning")
            last_detection_results = {}
            return None, 0
        
        img_folder = "./img"
        if not os.path.exists(img_folder):
            if not silent:
                log_message(f"[error] Image folder not found: {img_folder}")
            last_detection_results = {}
            return None, 0
        
        template_paths = get_image_file_paths(img_folder)
        if not template_paths:
            if not silent:
                log_message("[warn] No template images found in img/ folder")
            last_detection_results = {}
            return {}, 0
        
        detection_results = {}
        total_detected = 0
        
        # OPTIMIZED: Use batched processing with shared screenshot (5-10x faster!)
        try:
            # Use find_multiple_images_batched for massive speed improvement
            batch_results = ImageFinder.find_multiple_images_batched(
                template_paths,
                area[0],
                area[1],
                area[2],
                area[3],
                resize_factor=resize_factor,
                threshold=global_threshold,
                detection_mode=detection_mode,
                batch_size=10,  # OPTIMIZED: Process 10 templates in parallel (was 5)
                fast_mode=False,  # FIXED: Disabled for accuracy (was causing misdetections)
            )
            
            # Convert batch results to expected format
            for template_name, points in batch_results.items():
                if points:
                    # Find the full template path
                    template_path = next((p for p in template_paths if os.path.basename(p) == template_name), None)
                    detection_results[template_name] = {
                        "count": len(points),
                        "points": points,
                        "template_path": template_path,
                    }
                    total_detected += len(points)
        
        except Exception as batch_exc:
            if not silent:
                log_message(f"[warn] Batch processing failed, falling back to sequential: {batch_exc}")
            
            # Fallback to sequential processing if batch fails
            for template_path in template_paths:
                try:
                    template_name = os.path.basename(template_path)
                    points, _ = ImageFinder.find_image_on_screen(
                        template_path,
                        area[0],
                        area[1],
                        area[2],
                        area[3],
                        resize_factor,
                        threshold=global_threshold,
                        detection_mode=detection_mode,
                    )
                    
                    if points:
                        detection_results[template_name] = {
                            "count": len(points),
                            "points": points,
                            "template_path": template_path,
                        }
                        total_detected += len(points)
                except Exception as template_exc:
                    if not silent:
                        log_message(f"[warn] Error scanning {os.path.basename(template_path)}: {template_exc}")
                    continue
        
        last_detection_results = detection_results
        return detection_results, total_detected
    finally:
        if not skip_lock:
            detection_lock.release()


def _draw_boxes_on_screenshot(detection_results, game_area):
    """Draw green boxes and labels on screenshot of game area."""
    if len(game_area) != 4:
        return None
    
    try:
        # Take screenshot of game area
        start_x, start_y, end_x, end_y = game_area
        width = end_x - start_x
        height = end_y - start_y
        
        screenshot = pyautogui.screenshot(region=(start_x, start_y, width, height))
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Draw boxes and labels for each detection
        for template_name, data in detection_results.items():
            points = data.get('points', [])
            item_name = os.path.splitext(template_name)[0]
            
            for point in points:
                # Convert screen coordinates to relative coordinates
                rel_x = point[0] - start_x
                rel_y = point[1] - start_y
                
                # Box size
                box_size = 50
                half_size = box_size // 2
                
                # Draw green rectangle
                top_left = (rel_x - half_size, rel_y - half_size)
                bottom_right = (rel_x + half_size, rel_y + half_size)
                cv2.rectangle(screenshot_cv, top_left, bottom_right, (0, 255, 0), 2)
                
                # Draw label background and text
                label_text = item_name
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                thickness = 1
                
                # Get text size
                (text_width, text_height), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)
                
                # Label position (below box)
                label_y = rel_y + half_size + 15
                label_x = rel_x - text_width // 2
                
                # Draw label background
                cv2.rectangle(
                    screenshot_cv,
                    (label_x - 2, label_y - text_height - 2),
                    (label_x + text_width + 2, label_y + baseline + 2),
                    (0, 0, 0),
                    -1  # Filled rectangle
                )
                
                # Draw label text
                cv2.putText(
                    screenshot_cv,
                    label_text,
                    (label_x, label_y),
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness,
                    cv2.LINE_AA
                )
        
        # Convert back to RGB for PIL
        screenshot_rgb = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(screenshot_rgb)
        
        # Resize if too large (max 800px width for display)
        max_width = 800
        if pil_image.width > max_width:
            ratio = max_width / pil_image.width
            new_height = int(pil_image.height * ratio)
            pil_image = pil_image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to base64
        import io
        import base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode()
        
        return img_base64
        
    except Exception as e:
        log_message(f"[error] Failed to draw boxes on screenshot: {e}", "error")
        import traceback
        log_message(f"[error] {traceback.format_exc()}", "error")
        return None

def _scan_and_preview_impl(page_ref=None):
    """Scan current game area and display detected items with PNG previews"""
    global last_detection_results, detection_items_container_ref, detection_total_ref, detection_types_ref, detected_count_text_ref, detection_image_ref
    
    try:
        log_message("[info] Scanning for items...")
        
        # Update UI to show scanning state
        if detection_items_container_ref and detection_items_container_ref.current:
            detection_items_container_ref.current.controls = [
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.ProgressRing(width=40, height=40, color=PURPLE),
                            ft.Text("Scanning for items...", size=16, color=TEXT_MUTED),
                        ],
                        spacing=16,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=40,
                )
            ]
            detection_items_container_ref.current.update()
        
        detection_results, total_detected = perform_detection_scan(silent=False)
        if detection_results is None:
            if detection_items_container_ref and detection_items_container_ref.current:
                detection_items_container_ref.current.controls = [
                    ft.Container(
                        content=ft.Text(
                            "Set your game area and ensure template images exist before scanning.",
                            color=TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        padding=24,
                    )
                ]
                detection_items_container_ref.current.update()
            if detection_total_ref and detection_total_ref.current:
                detection_total_ref.current.value = "0 items"
                detection_total_ref.current.update()
            if detection_types_ref and detection_types_ref.current:
                detection_types_ref.current.value = "0 types"
                detection_types_ref.current.update()
            if detected_count_text_ref and detected_count_text_ref.current:
                detected_count_text_ref.current.value = "0 items"
                detected_count_text_ref.current.update()
            return
        
        log_message(f"[info] Scan complete: {total_detected} items ({len(detection_results)} types)")
        
        # Draw boxes on screenshot and display in GUI
        annotated_screenshot = None
        if detection_results and len(area) == 4:
            annotated_screenshot = _draw_boxes_on_screenshot(detection_results, area)
        
        if LIVE_DETECTION_AVAILABLE:
            manager = _ensure_live_detection_manager()
            if manager and manager.is_overlay_running():
                manager.update_detections_from_scan(detection_results, area, resize_factor)
        
        # Update UI with detected items
        if detection_items_container_ref and detection_items_container_ref.current:
            items_controls = []
            
            # Add annotated screenshot at the top if available
            if annotated_screenshot:
                items_controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "Detection Preview with Boxes",
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=ACCENT_BLUE,
                                ),
                                ft.Container(
                                    content=ft.Image(
                                        src_base64=annotated_screenshot,
                                        fit=ft.ImageFit.CONTAIN,
                                        width=800,
                                        border_radius=8,
                                    ),
                                    padding=8,
                                    bgcolor=hex_with_opacity("#000000", 0.3),
                                    border=ft.border.all(2, SUCCESS_GREEN),
                                    border_radius=12,
                                ),
                                ft.Text(
                                    "Green boxes show detected items with labels",
                                    size=11,
                                    color=TEXT_SUBTLE,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            spacing=8,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        margin=ft.margin.only(bottom=24),
                    )
                )
            
            if detection_results:
                # Sort by count (most detected first)
                sorted_results = sorted(detection_results.items(), key=lambda x: x[1]['count'], reverse=True)
                
                for template_name, data in sorted_results:
                    count = data['count']
                    template_path = data['template_path']
                    
                    # Create item card with image preview
                    try:
                        # Load image for preview
                        from PIL import Image as PILImage
                        pil_image = PILImage.open(template_path)
                        
                        # Resize for preview (max 80x80)
                        pil_image.thumbnail((80, 80), PILImage.Resampling.LANCZOS)
                        
                        # Convert to base64 for Flet
                        import io
                        import base64
                        buffer = io.BytesIO()
                        pil_image.save(buffer, format='PNG')
                        img_bytes = buffer.getvalue()
                        img_base64 = base64.b64encode(img_bytes).decode()
                        
                        item_card = ft.Container(
                            content=ft.Row(
                                controls=[
                                    # Image preview
                                    ft.Container(
                                        content=ft.Image(
                                            src_base64=img_base64,
                                            width=80,
                                            height=80,
                                            fit=ft.ImageFit.CONTAIN,
                                        ),
                                        padding=8,
                                        bgcolor=hex_with_opacity("#FFFFFF", 0.2),
                                        border_radius=8,
                                    ),
                                    # Item info
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                template_name.replace('.png', '').replace('_', ' ').title(),
                                                size=16,
                                                weight=ft.FontWeight.W_600,
                                                color=TEXT_PRIMARY,
                                            ),
                                            ft.Text(
                                                f"Count: {count}",
                                                size=14,
                                                color=SUCCESS_GREEN,
                                                weight=ft.FontWeight.W_500,
                                            ),
                                        ],
                                        spacing=4,
                                        expand=True,
                                    ),
                                ],
                                spacing=16,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            padding=16,
                            margin=ft.margin.only(bottom=12),
                            bgcolor=GLASS_BG,
                            border=ft.border.all(1, GLASS_BORDER),
                            border_radius=12,
                        )
                        items_controls.append(item_card)
                    except Exception as img_exc:
                        # Fallback if image loading fails
                        item_card = ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        template_name,
                                        size=14,
                                        weight=ft.FontWeight.W_600,
                                        color=TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        f"Count: {count}",
                                        size=12,
                                        color=SUCCESS_GREEN,
                                    ),
                                ],
                                spacing=4,
                            ),
                            padding=12,
                            margin=ft.margin.only(bottom=8),
                            bgcolor=GLASS_BG,
                            border=ft.border.all(1, GLASS_BORDER),
                            border_radius=8,
                        )
                        items_controls.append(item_card)
            else:
                # No items detected
                items_controls.append(
                    ft.Container(
                        content=ft.Text(
                            "No items detected",
                            size=16,
                            color=TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        padding=40,
                        alignment=ft.alignment.center,
                    )
                )
            
            detection_items_container_ref.current.controls = items_controls
            detection_items_container_ref.current.update()
        
        # Update totals
        total_label = f"{total_detected} item{'s' if total_detected != 1 else ''}"
        type_label = f"{len(detection_results)} type{'s' if len(detection_results) != 1 else ''}"

        if detection_total_ref and detection_total_ref.current:
            detection_total_ref.current.value = total_label
            detection_total_ref.current.update()
        
        if detection_types_ref and detection_types_ref.current:
            detection_types_ref.current.value = type_label
            detection_types_ref.current.update()

        if detected_count_text_ref and detected_count_text_ref.current:
            detected_count_text_ref.current.value = total_label
            detected_count_text_ref.current.update()
        
    except Exception as exc:
        log_message(f"[error] Scan error: {exc}")
        if detection_items_container_ref and detection_items_container_ref.current:
            detection_items_container_ref.current.controls = [
                ft.Container(
                    content=ft.Text(
                        f"Error: {str(exc)[:100]}",
                        size=14,
                        color=DANGER_RED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=20,
                )
            ]
            detection_items_container_ref.current.update()
        
        if detection_total_ref and detection_total_ref.current:
            detection_total_ref.current.value = "0 items"
            detection_total_ref.current.update()
        
        if detection_types_ref and detection_types_ref.current:
            detection_types_ref.current.value = "0 types"
            detection_types_ref.current.update()
        
        if detected_count_text_ref and detected_count_text_ref.current:
            detected_count_text_ref.current.value = "0 items"
            detected_count_text_ref.current.update()


def scan_and_preview_callback(page_ref=None):
    """Thread-safe wrapper around the detection scan."""
    global detection_lock
    
    if detection_lock.locked():
        log_message("[warn] Detection already in progress.")
        return
    
    detection_lock.acquire()
    try:
        _scan_and_preview_impl(page_ref=page_ref)
    finally:
        detection_lock.release()

# Live detection overlay callbacks
live_detection_manager = None

def _ensure_live_detection_manager():
    """Create the overlay manager if needed and sync core settings."""
    global live_detection_manager
    
    if not LIVE_DETECTION_AVAILABLE:
        return None
    
    if live_detection_manager is None:
        live_detection_manager = LiveDetectionManager(log_callback=log_message)
    
    if len(area) == 4:
        live_detection_manager.update_game_area(area)
    live_detection_manager.set_resize_factor(resize_factor)
    return live_detection_manager


_live_scan_frame_count = 0

def _live_scan_callable():
    """Background-safe scan callable used for live scanning with frame skipping."""
    global _live_scan_frame_count
    
    # OPTIMIZATION: Frame skipping - only scan every 2nd frame for live detection
    _live_scan_frame_count += 1
    if _live_scan_frame_count % 2 != 0:
        return None, 0  # Skip this frame
    
    # Don't use the UI lock for live scanning - it runs in background
    # Use skip_lock=True to avoid blocking on manual scans
    try:
        return perform_detection_scan(silent=True, skip_lock=True)
    except Exception as e:
        # Silent errors for live scanning to avoid spam
        return None, 0


def toggle_overlay_switch(e, page_ref):
    """Toggle overlay from switch"""
    manager = _ensure_live_detection_manager()
    
    if not LIVE_DETECTION_AVAILABLE or manager is None:
        log_message("[error] Live detection not available", "error")
        e.control.value = False
        e.control.update()
        return
    
    if len(area) != 4:
        log_message("[error] Set screen area first before enabling overlay", "error")
        e.control.value = False
        e.control.update()
        return
    
    if e.control.value:
        if manager.start_overlay(game_area=area):
            log_message(f"[info] Detection overlay enabled at area {area}", "success")
            if last_detection_results:
                manager.update_detections_from_scan(last_detection_results, area, resize_factor)
        else:
            e.control.value = False
            e.control.update()
    else:
        manager.stop_live_detection()
        manager.stop_overlay()
        if live_scan_switch_ref and live_scan_switch_ref.current and live_scan_switch_ref.current.value:
            live_scan_switch_ref.current.value = False
            live_scan_switch_ref.current.update()
        log_message("[info] Detection overlay disabled", "info")


def set_detection_mode(mode: str, page_ref, mode_ref, status_ref, tuning_ref):
    """Set detection mode (cpu/gpu/hybrid/express) and update UI."""
    global detection_mode
    
    detection_mode = mode
    save_config()
    
    # Update status text
    mode_names = {"cpu": "CPU", "gpu": "GPU", "hybrid": "Hybrid", "express": "Express"}
    status_texts = {
        "cpu": "CPU Mode - Most Accurate",
        "gpu": "GPU Mode - Fast (AMD Optimized)",
        "hybrid": "Hybrid Mode - Fast + Accurate",
        "express": "Express Mode - ULTRA FAST (GPU only, no verification)"
    }
    
    if mode_ref and mode_ref.current:
        mode_ref.current.value = f"Current: {mode_names.get(mode, mode.upper())} Mode"
        mode_ref.current.update()
    
    if status_ref and status_ref.current:
        status_ref.current.value = status_texts.get(mode, f"{mode.upper()} Mode")
        status_ref.current.update()
    
    # Show/hide advanced tuning panel
    if tuning_ref and tuning_ref.current:
        tuning_ref.current.visible = (mode in ["gpu", "hybrid", "express"])
        tuning_ref.current.update()
    
    log_message(f"[info] Detection mode set to: {mode_names.get(mode, mode.upper())}", "info")
    
    # Update page
    try:
        page_ref.update()
    except:
        pass

def update_global_threshold(e, page_ref):
    """Update global threshold and auto-save."""
    global global_threshold
    
    global_threshold = float(e.control.value)
    
    # Update catalog default threshold
    from item_finder import TEMPLATE_CATALOG
    TEMPLATE_CATALOG.set_default_threshold(global_threshold)
    
    # Auto-save config
    save_config()
    
    log_message(f"[info] Global threshold updated to {global_threshold:.2f} and saved", "info")

def create_advanced_gpu_tuning_panel(templates: List[str], page_ref, container_ref):
    """Create advanced GPU tuning panel with per-template threshold sliders."""
    from item_finder import TEMPLATE_CATALOG
    
    template_rows = []
    
    for template_name in templates:
        # Get current threshold for this template
        current_threshold = TEMPLATE_CATALOG.threshold_for(template_name, global_threshold)
        
        # Create slider ref for this template
        slider_ref = ft.Ref[ft.Slider]()
        value_ref = ft.Ref[ft.Text]()
        auto_refresh_ref = ft.Ref[ft.Switch]()
        
        def make_template_callback(tmpl_name, slider_r, value_r, auto_r):
            def on_slider_change(e):
                new_threshold = float(e.control.value)
                # Update display
                if value_r and value_r.current:
                    value_r.current.value = f"{new_threshold:.2f}"
                    value_r.current.update()
                # Save to catalog
                TEMPLATE_CATALOG.set_threshold(tmpl_name, new_threshold)
                log_message(f"[info] {tmpl_name} threshold set to {new_threshold:.2f} and saved", "info")
                
                # Auto-refresh if enabled
                if auto_r and auto_r.current and auto_r.current.value:
                    # Trigger a new scan
                    try:
                        scan_and_preview_callback(page_ref)
                    except:
                        pass
            
            return on_slider_change
        
        def make_auto_refresh_callback(tmpl_name, slider_r):
            def on_switch_change(e):
                if e.control.value:
                    # Auto-refresh enabled - trigger scan
                    try:
                        scan_and_preview_callback(page_ref)
                    except:
                        pass
            return on_switch_change
        
        template_row = create_glass_card(
            ft.Row(
                controls=[
                    # Template name
                    ft.Column(
                        controls=[
                            ft.Text(
                                template_name.replace('.png', '').replace('_', ' ').title(),
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=TEXT_PRIMARY,
                            ),
                            ft.Text(
                                f"Threshold: {current_threshold:.2f}",
                                size=11,
                                color=TEXT_SUBTLE,
                                ref=value_ref,
                            ),
                        ],
                        spacing=4,
                        expand=2,
                    ),
                    # Threshold slider
                    ft.Slider(
                        min=0.50,
                        max=0.95,
                        divisions=45,
                        value=current_threshold,
                        label="{value}",
                        on_change=make_template_callback(template_name, slider_ref, value_ref, auto_refresh_ref),
                        ref=slider_ref,
                        expand=3,
                    ),
                    # Auto-refresh toggle
                    ft.Switch(
                        label="Auto",
                        value=False,
                        on_change=make_auto_refresh_callback(template_name, slider_ref),
                        ref=auto_refresh_ref,
                        label_style=ft.TextStyle(size=11, color=TEXT_PRIMARY),
                    ),
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=12,
            margin=4,
        )
        
        template_rows.append(template_row)
    
    return ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text(
                        "Advanced GPU Tuning",
                        size=18,
                        weight=ft.FontWeight.W_600,
                        color=ACCENT_BLUE,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.SETTINGS, color=ACCENT_BLUE, size=20),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Text(
                "Fine-tune detection threshold for each template. Changes auto-save to catalog.json",
                size=11,
                color=TEXT_SUBTLE,
            ),
            ft.Container(height=12),
            ft.Container(
                content=ft.Column(
                    controls=template_rows,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
                height=400,  # Fixed height with scroll
                border=ft.border.all(1, GLASS_BORDER),
                border_radius=12,
                padding=12,
                bgcolor=hex_with_opacity("#FFFFFF", 0.1),
            ),
        ],
        spacing=8,
    )

def toggle_live_detection_button(e, page_ref):
    """Toggle live detection with single button (on/off)"""
    manager = _ensure_live_detection_manager()
    
    if not LIVE_DETECTION_AVAILABLE or manager is None:
        log_message("[error] Live detection not available", "error")
        return
    
    if len(area) != 4:
        log_message("[error] Set screen area first", "error")
        return
    
    # Check if already running
    is_running = manager.is_overlay_running() or (
        hasattr(manager, 'detection_thread') and 
        manager.detection_thread and 
        manager.detection_thread.is_alive()
    )
    
    if is_running:
        # Stop live detection and motion detection
        manager.stop_live_detection()
        manager.stop_overlay()
        ImageFinder.enable_motion_detection(False)
        log_message("[info] Live detection stopped", "info")
    else:
        # Enable motion detection for live scanning
        ImageFinder.enable_motion_detection(True)
        
        # Start live detection
        if not manager.start_overlay(game_area=area):
            log_message("[error] Failed to start overlay", "error")
            return
        
        manager.start_live_detection(
            scan_callable=_live_scan_callable,
            scan_interval=0.2,  # Faster - 200ms updates (with frame skipping = 400ms effective)
            resize_factor=resize_factor,
        )
        log_message("[info] Live detection started - optimized with motion detection & frame skipping", "success")


def scan_board_button_callback():
    """Scan board layout and detect slots"""
    global board_slots, sort_plan
    
    try:
        if len(area) != 4:
            log_message("[error] Set the screen area before scanning the board.")
            return
        
        log_message("[info] Auto-scanning board layout...")
        board_slots = detect_board_layout(area, board_rows, board_cols, resize_factor)
        apply_slot_overrides()
        
        if last_detected_grid_summary:
            log_message(f"[info] {last_detected_grid_summary}")
        
        occupied = sum(1 for slot in board_slots if slot.get("type"))
        total = len(board_slots)
        log_message(f"[info] Auto scan complete: {occupied} occupied / {total} total slots")
    except Exception as exc:
        log_message(f"[error] Board scan error: {exc}")


def hex_with_opacity(hex_color, opacity):
    """Convert hex color to rgba string with opacity (0-1)"""
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    # Convert to RGB
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    else:
        r, g, b = 255, 255, 255
    a = int(opacity * 255)
    # Return rgba(r, g, b, a) format which Flet supports
    return f"rgba({r}, {g}, {b}, {opacity})"


def create_glass_button(text, on_click=None, width=None, height=50, color=ACCENT_BLUE, icon=None):
    """Create a glassmorphism button with blur effect"""
    # Use smaller padding and font when no width specified (flexible buttons)
    h_padding = 12 if width is None else 24
    font_size = 13 if width is None else 16
    icon_size = 16 if width is None else 20
    
    button = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(icon, color=TEXT_PRIMARY, size=icon_size) if icon else ft.Container(width=0),
                ft.Text(text, color=TEXT_PRIMARY, size=font_size, weight=ft.FontWeight.W_600),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        ),
        width=width,
        height=height,
        bgcolor=hex_with_opacity("#FFFFFF", 0.3),
        border=ft.border.all(2, hex_with_opacity("#58B2FF", 0.3)),
        border_radius=ft.border_radius.all(16),
        padding=ft.padding.symmetric(horizontal=h_padding, vertical=10),
        on_click=on_click,
        expand=width is None,  # Expand when flexible
    )
    
    def on_hover(e):
        try:
            if e.data == "true":
                button.bgcolor = hex_with_opacity("#FFFFFF", 0.5)
                button.border = ft.border.all(2, hex_with_opacity("#78C8FF", 0.6))
            else:
                button.bgcolor = hex_with_opacity("#FFFFFF", 0.3)
                button.border = ft.border.all(2, hex_with_opacity("#58B2FF", 0.3))
            if button:
                button.update()
        except:
            pass
    
    if on_click is not None:  # Only set hover if button is interactive
        button.on_hover = on_hover
    return button


def create_glass_card(content, padding=16, margin=8):
    """Create a glassmorphism card container"""
    return ft.Container(
        content=content,
        padding=padding,
        margin=margin,
        bgcolor=hex_with_opacity("#FFFFFF", 0.4),
        border=ft.border.all(1, hex_with_opacity("#58B2FF", 0.2)),
        border_radius=ft.border_radius.all(20),
        
    )


def create_glass_badge(text, color=ACCENT_BLUE):
    """Create a glassmorphism badge"""
    return ft.Container(
        content=ft.Text(text, color=TEXT_PRIMARY, size=12, weight=ft.FontWeight.W_500),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=hex_with_opacity("#FFFFFF", 0.3),
        border=ft.border.all(1, hex_with_opacity(color, 0.3)),
        border_radius=ft.border_radius.all(12),
        
    )


def create_glass_tab(text, on_click, is_active=False):
    """Create a glassmorphism tab button"""
    return ft.Container(
        content=ft.Text(text, color=TEXT_PRIMARY, size=16, weight=ft.FontWeight.W_600),
        padding=ft.padding.symmetric(horizontal=24, vertical=12),
        bgcolor=hex_with_opacity("#FFFFFF", 0.5 if is_active else 0.3),
        border=ft.border.all(2 if is_active else 1, ACCENT_BLUE if is_active else GLASS_BORDER),
        border_radius=ft.border_radius.all(12),
        on_click=on_click,
        
    )


# Placeholder for callbacks - will be set after import
manual_save_callback = None
manual_load_callback = None
select_area_callback = None
select_merging_points_callback = None
select_box_button_callback = None
start_button_callback = None
stop_button_callback = None
# Scan callbacks are defined below
manual_select_slots_callback = None
generate_sort_plan_callback = None
run_sort_plan_callback = None
# These are defined above in this file, not imported from gui.py

# Global for detection results
last_detection_results = {}
# update_merge_count = None
# record_hotkey = None
# record_stop_hotkey = None
# load_config = None  # Defined above
# save_config = None  # Defined above
# log_message = None  # Defined above
# format_hotkey_label = None  # Defined above


def create_flet_gui(page: ft.Page):
    """Create the main Flet GUI with glassmorphism design"""
    
    # Configure page
    page.title = "Kishor Farm Merger Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.spacing = 0
    page.scroll = ft.ScrollMode.AUTO  # Allow page-level scrolling
    
    # State management
    status_text = ft.Ref[ft.Text]()
    box_count_text = ft.Ref[ft.Text]()
    detected_count_text = ft.Ref[ft.Text]()
    global detected_count_text_ref
    detected_count_text_ref = detected_count_text
    log_view = ft.Ref[ft.Column]()
    hotkey_text_ref = ft.Ref[ft.Text]()
    pause_hotkey_text_ref = ft.Ref[ft.Text]()
    coins_value_ref = ft.Ref[ft.Text]()
    gems_value_ref = ft.Ref[ft.Text]()
    thunder_value_ref = ft.Ref[ft.Text]()
    
    def update_status(text, color=SUCCESS_GREEN):
        if status_text.current:
            status_text.current.value = text
            status_text.current.color = color
            status_text.current.update()
    
    def update_log(message, level="info"):
        if not log_view.current:
            return
        level_colors = {
            "info": TEXT_MUTED,
            "debug": TEXT_SUBTLE,
            "warn": WARNING_ORANGE,
            "warning": WARNING_ORANGE,
            "error": DANGER_RED,
            "success": SUCCESS_GREEN,
        }
        text_color = level_colors.get(level, TEXT_MUTED)
        log_view.current.controls.insert(
            0,
            ft.Text(
                message,
                color=text_color,
                size=12,
                selectable=True,
            )
        )
        # Keep only last 100 entries
        if len(log_view.current.controls) > 100:
            log_view.current.controls.pop()
        try:
            log_view.current.update()
        except AssertionError:
            # Control not yet attached to the page; ignore and wait for initial render
            pass
    
    # Template collector overlay & status handling
    collector_state = {
        "queue": thread_queue.Queue(),
        "auto_close": None,
        "category": "",
    }
    collector_dialog = None

    collector_title_text = ft.Text(
        "Template Collector",
        size=20,
        weight=ft.FontWeight.W_600,
        color=TEXT_PRIMARY,
    )
    collector_status_text = ft.Text(
        "Launching capture overlay...",
        size=14,
        color=TEXT_MUTED,
    )
    collector_details_text = ft.Text(
        "Left-click items to capture.\nRight-click or press ESC to finish.",
        size=12,
        color=TEXT_SUBTLE,
    )
    collector_progress_ring = ft.ProgressRing(width=36, height=36, color=PURPLE)
    collector_close_button = ft.TextButton("Dismiss")

    def close_collector_dialog(e=None):
        collector_state["auto_close"] = None
        # Note: Polling thread will continue but will check collector_state
        if collector_dialog and collector_dialog.open:
            collector_dialog.open = False
            try:
                page.update()
            except Exception:
                pass  # Page may have been closed

    collector_close_button.on_click = close_collector_dialog

    collector_dialog = ft.AlertDialog(
        modal=True,
        title=collector_title_text,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        collector_progress_ring,
                        ft.Column(
                            controls=[
                                collector_status_text,
                                collector_details_text,
                            ],
                            spacing=6,
                        ),
                    ],
                    spacing=16,
                    alignment=ft.MainAxisAlignment.START,
                ),
            ],
            spacing=16,
            width=360,
        ),
        actions=[collector_close_button],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def on_collector_timer_tick(e):
        updated = False
        queue_obj = collector_state["queue"]
        while True:
            try:
                event = queue_obj.get_nowait()
            except thread_queue.Empty:
                break

            kind = event[0]
            if kind == "start":
                collector_status_text.value = "Collector running..."
                collector_status_text.color = TEXT_MUTED
                collector_details_text.value = "Left-click items to capture.\nRight-click or press ESC to finish."
                collector_progress_ring.visible = True
                collector_close_button.disabled = False
                updated = True

            elif kind == "complete":
                _, category, captured_count, _templates = event
                collector_status_text.value = "Capture finished"
                collector_status_text.color = SUCCESS_GREEN
                collector_details_text.value = (
                    f"Saved {captured_count} template{'s' if captured_count != 1 else ''} to img/{category}/"
                )
                collector_progress_ring.visible = False
                collector_close_button.disabled = False
                collector_state["auto_close"] = time.time() + 1.5
                update_status(f"Template collector finished ({captured_count} captured)", SUCCESS_GREEN)
                if captured_count:
                    log_message("[info] New templates saved - auto-detecting items now.")
                    run_auto_detection_after_capture()
                else:
                    log_message("[info] Collector closed without new templates.")
                updated = True

            elif kind == "error":
                _, _category, message = event
                collector_status_text.value = "Collector error"
                collector_status_text.color = DANGER_RED
                collector_details_text.value = message
                collector_progress_ring.visible = False
                collector_close_button.disabled = False
                collector_state["auto_close"] = None
                update_status("Template collector error", DANGER_RED)
                updated = True

        if collector_state["auto_close"] and time.time() >= collector_state["auto_close"]:
            collector_state["auto_close"] = None
            close_collector_dialog()

        if updated and collector_dialog and collector_dialog.open:
            try:
                page.update()
            except Exception:
                pass  # Page may have been closed

    # Use threading for periodic queue polling instead of ft.Timer (which doesn't exist)
    collector_poll_thread = None
    collector_poll_active = threading.Event()
    
    def poll_collector_queue():
        """Periodically poll the collector queue and update UI"""
        while collector_poll_active.is_set():
            try:
                on_collector_timer_tick(None)  # Pass None as event parameter
                time.sleep(0.5)  # Poll every 500ms
            except Exception as exc:
                # Only log if it's a real error, not just queue empty
                if "queue" not in str(exc).lower():
                    log_message(f"[warn] Collector queue poll error: {exc}")
                time.sleep(0.5)

    def handle_template_collect(category, crop_size):
        nonlocal collector_poll_thread, collector_poll_active
        
        try:
            if collector_dialog and hasattr(collector_dialog, 'open') and collector_dialog.open:
                update_status("Template collector already running.", WARNING_ORANGE)
                return
        except Exception:
            pass  # Dialog may not be initialized yet

        collector_state["queue"] = thread_queue.Queue()
        collector_state["auto_close"] = None
        collector_state["category"] = category

        collector_title_text.value = f"Template Collector · {category.replace('_', ' ').title()}"
        collector_status_text.value = "Launching capture overlay..."
        collector_status_text.color = TEXT_MUTED
        collector_details_text.value = "Left-click items to capture.\nRight-click or press ESC to finish."
        collector_progress_ring.visible = True
        collector_close_button.disabled = False

        collector_dialog.open = True
        page.dialog = collector_dialog
        page.update()

        # Start polling thread if not already running
        if collector_poll_thread is None or not collector_poll_thread.is_alive():
            collector_poll_active.set()
            collector_poll_thread = threading.Thread(target=poll_collector_queue, daemon=True)
            collector_poll_thread.start()
        
        launch_template_collector(category, crop_size, status_queue=collector_state["queue"])
    
    # Template collection preview dialog
    template_preview_dialog = None
    template_preview_opening = False  # Flag to prevent multiple simultaneous opens
    
    def safe_show_template_preview(category):
        """Wrapper to safely call show_template_preview with error handling"""
        nonlocal template_preview_opening
        
        # Prevent multiple simultaneous opens
        if template_preview_opening:
            log_message("[warn] Template preview dialog is already opening, please wait...")
            return
        
        try:
            template_preview_opening = True
            show_template_preview(category)
        except Exception as exc:
            import traceback
            error_msg = f"[error] Button click error for {category}: {exc}\n{traceback.format_exc()}"
            log_message(error_msg)
            update_status(f"Error opening template preview: {exc}", DANGER_RED)
        finally:
            template_preview_opening = False
    
    def run_auto_detection_after_capture():
        """Trigger detection so newly captured templates are picked up."""
        if len(area) != 4:
            log_message("[warn] Auto-detect skipped: set screen area first.")
            return
        log_message("[info] Auto-detecting items with new templates...")
        try:
            scan_and_preview_callback()
        except Exception as exc:
            log_message(f"[error] Auto-detect error: {exc}")
    
    def start_quick_collection(category):
        """Start template collection without opening the preview dialog."""
        crop_size = 60 if category == "ui_elements" else 50
        try:
            log_message(f"[info] Starting quick collection for {category}.")
            handle_template_collect(category, crop_size)
        except Exception as exc:
            log_message(f"[error] Quick collection error for {category}: {exc}")
            update_status(f"Quick collection failed: {exc}", DANGER_RED)
    
    def show_template_preview(category):
        """Show preview of existing templates in category"""
        nonlocal template_preview_dialog
        
        # Close any existing dialog first and clear it completely
        if template_preview_dialog:
            try:
                template_preview_dialog.open = False
            except:
                pass
            template_preview_dialog = None
        
        if hasattr(page, 'dialog') and page.dialog:
            try:
                page.dialog.open = False
                page.dialog = None
                page.update()
            except:
                pass
        
        try:
            log_message(f"[info] Opening template preview for category: {category}")
            category_folder = os.path.join("./img", category)
            if not os.path.exists(category_folder):
                os.makedirs(category_folder, exist_ok=True)
            
            # Get existing templates (sorted, most recent first)
            existing_templates = []
            template_count = 0
            if os.path.exists(category_folder):
                template_files = []
                for file in os.listdir(category_folder):
                    if file.endswith(('.png', '.jpg', '.jpeg')):
                        file_path = os.path.join(category_folder, file)
                        # Get modification time for sorting
                        try:
                            mtime = os.path.getmtime(file_path)
                            template_files.append((mtime, file_path, file))
                        except:
                            template_files.append((0, file_path, file))
                
                # Sort by modification time (newest first)
                template_files.sort(reverse=True)
                existing_templates = [item[1] for item in template_files[:20]]  # Show up to 20 most recent
                template_count = len(existing_templates)
            
            # Create preview cards in a grid
            preview_controls = []
            if existing_templates:
                # Show templates in a scrollable grid (4 per row)
                rows = []
                for i in range(0, len(existing_templates), 4):
                    row_templates = existing_templates[i:i+4]
                    row_controls = []
                    for template_path in row_templates:
                        try:
                            from PIL import Image as PILImage
                            import base64
                            import io
                            
                            pil_image = PILImage.open(template_path)
                            pil_image.thumbnail((80, 80), PILImage.Resampling.LANCZOS)
                            
                            buffer = io.BytesIO()
                            pil_image.save(buffer, format='PNG')
                            img_base64 = base64.b64encode(buffer.getvalue()).decode()
                            
                            template_name = os.path.basename(template_path)
                            # Truncate long names
                            if len(template_name) > 15:
                                template_name = template_name[:12] + "..."
                            
                            row_controls.append(
                                ft.Container(
                                    content=ft.Column(
                                        controls=[
                                            ft.Container(
                                                content=ft.Image(
                                                    src_base64=img_base64,
                                                    width=80,
                                                    height=80,
                                                    fit=ft.ImageFit.CONTAIN,
                                                ),
                                                border=ft.border.all(2, GLASS_BORDER),
                                                border_radius=8,
                                                padding=4,
                                                bgcolor=hex_with_opacity("#FFFFFF", 0.05),
                                            ),
                                            ft.Text(
                                                template_name,
                                                size=9,
                                                color=TEXT_MUTED,
                                                text_align=ft.TextAlign.CENTER,
                                                max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                        ],
                                        spacing=4,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        tight=True,
                                    ),
                                    padding=4,
                                    width=100,
                                )
                            )
                        except Exception:
                            continue
                    
                    if row_controls:
                        rows.append(
                            ft.Row(
                                controls=row_controls + [ft.Container(width=100)] * (4 - len(row_controls)),
                                spacing=8,
                                wrap=False,
                            )
                        )
                
                if rows:
                    preview_controls = rows
                else:
                    preview_controls = [
                        ft.Text(f"No valid templates found", color=TEXT_MUTED)
                    ]
            else:
                preview_controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=48, color=TEXT_SUBTLE),
                                ft.Text(
                                    f"No templates in {category}/ yet",
                                    size=14,
                                    color=TEXT_MUTED,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(
                                    "Start capturing to create templates!",
                                    size=12,
                                    color=TEXT_SUBTLE,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            spacing=8,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=40,
                    )
                ]
            
            # Close any existing dialog first and clear it
            if hasattr(page, 'dialog') and page.dialog:
                try:
                    page.dialog.open = False
                    page.dialog = None
                    # Don't call update here - we'll do it once after setting new dialog
                except:
                    pass
            template_preview_dialog = None  # Always reset to None before creating new one
            
            # Create dialog
            template_preview_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Template Collection - {category.replace('_', ' ').title()}", size=20, weight=ft.FontWeight.W_600),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        f"Existing Templates ({template_count}):",
                                        size=14,
                                        weight=ft.FontWeight.W_600,
                                        color=ACCENT_BLUE,
                                    ),
                                    ft.Container(expand=True),
                                    ft.Text(
                                        "Most recent first",
                                        size=10,
                                        color=TEXT_SUBTLE,
                                    ),
                                ],
                            ),
                            ft.Container(height=8),
                            ft.Container(
                                content=ft.Column(
                                    controls=preview_controls,
                                    spacing=8,
                                    scroll=ft.ScrollMode.AUTO,
                                ),
                                height=280,
                                padding=8,
                                bgcolor=hex_with_opacity("#FFFFFF", 0.05),
                                border_radius=12,
                                border=ft.border.all(1, GLASS_BORDER),
                            ),
                            ft.Container(height=16),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            "Ready to capture new templates",
                                            size=13,
                                            weight=ft.FontWeight.W_600,
                                            color=TEXT_PRIMARY,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        ft.Text(
                                            "• Left-click items to capture\n• Name dialog will auto-suggest names\n• Press Enter to accept, or type custom name\n• Right-click or ESC to finish",
                                            size=11,
                                            color=TEXT_MUTED,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                    ],
                                    spacing=4,
                                ),
                                padding=12,
                                bgcolor=hex_with_opacity(ACCENT_BLUE, 0.1),
                                border_radius=8,
                            ),
                        ],
                        spacing=8,
                    ),
                    width=550,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e, cat=category: close_preview_dialog()),
                    ft.ElevatedButton(
                        "Start Capture",
                        on_click=lambda e, cat=category: (
                            close_preview_dialog(),
                            handle_template_collect(cat, 50 if cat != "ui_elements" else 60)
                        ),
                        bgcolor=PURPLE,
                        color=TEXT_PRIMARY,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            
            # Set dialog FIRST, then open, then update (matching the working pattern)
            # Ensure no existing dialog is open (already cleared above)
            page.dialog = template_preview_dialog
            template_preview_dialog.open = True
            page.update()  # Single update call after setting everything
            
        except Exception as exc:
            import traceback
            error_msg = f"[error] Preview error: {exc}\n{traceback.format_exc()}"
            log_message(error_msg)
            print(error_msg)  # Also print to console for debugging
            # Fallback to direct collection
            try:
                handle_template_collect(category, 50 if category != "ui_elements" else 60)
            except Exception as fallback_exc:
                error_msg2 = f"[error] Fallback collection also failed: {fallback_exc}\n{traceback.format_exc()}"
                log_message(error_msg2)
                print(error_msg2)
    
    def close_preview_dialog():
        """Close template preview dialog"""
        nonlocal template_preview_dialog
        
        try:
            if template_preview_dialog:
                try:
                    template_preview_dialog.open = False
                except:
                    pass
            
            if hasattr(page, 'dialog') and page.dialog:
                try:
                    page.dialog.open = False
                    page.dialog = None
                    page.update()
                except:
                    pass
            
            template_preview_dialog = None  # Reset to None so it can be recreated
        except Exception as exc:
            log_message(f"[error] Error closing preview dialog: {exc}")
            template_preview_dialog = None
            if hasattr(page, 'dialog') and page.dialog:
                try:
                    page.dialog = None
                    page.update()
                except:
                    pass
    
    # Resource tracking functions
    # Create refs for resource selection buttons
    coins_select_button_ref = ft.Ref[ft.Container]()
    gems_select_button_ref = ft.Ref[ft.Container]()
    thunder_select_button_ref = ft.Ref[ft.Container]()
    
    def update_resource_button_labels():
        """Update button labels to show if regions are set"""
        def update_button(ref, resource_type, label_prefix):
            if ref and ref.current:
                has_region = bool(resource_regions.get(resource_type))
                status = "✓" if has_region else ""
                # Update button text via the Row content
                if ref.current.content and isinstance(ref.current.content, ft.Row):
                    for child in ref.current.content.controls:
                        if isinstance(child, ft.Text):
                            child.value = f"{status} {label_prefix}" if status else label_prefix
                            break
                    ref.current.update()
        
        update_button(coins_select_button_ref, "coins", "Select Coin Area")
        update_button(gems_select_button_ref, "gems", "Select Gem Area")
        update_button(thunder_select_button_ref, "thunder", "Select Thunder Area")
    
    def select_resource_area(resource_type):
        """Select screen area for resource (coins/gems/thunder)"""
        global resource_regions
        try:
            log_message(f"[info] Selecting {resource_type} area...")
            log_message(f"[info] Drag to select area (hold mouse button, drag, release), then click 'Confirm' in preview window")
            
            # Run selector in a try-except to catch any crashes
            selector = None
            coordinates = None
            try:
                selector = ScreenAreaSelector()
                coordinates = selector.get_coordinates()
            except KeyboardInterrupt:
                log_message(f"[info] {resource_type.title()} selection cancelled by user")
                return
            except Exception as selector_error:
                log_message(f"[error] Selector error: {selector_error}")
                import traceback
                log_message(f"[error] Selector traceback: {traceback.format_exc()}")
                return
            
            log_message(f"[debug] Received coordinates: {coordinates}")
            
            if coordinates is None:
                log_message(f"[info] {resource_type.title()} selection was cancelled or preview closed without confirming")
                return
            
            if not isinstance(coordinates, (tuple, list)) or len(coordinates) != 4:
                log_message(f"[warn] Invalid coordinates format: {coordinates}. Expected 4 values (x1, y1, x2, y2)")
                return
            
            # Safely extract coordinates
            try:
                x, y, ex, ey = [float(c) for c in coordinates[:4]]
            except (ValueError, TypeError) as ve:
                log_message(f"[error] Invalid coordinate values: {coordinates}, error: {ve}")
                return
                
            # Coordinates from ScreenAreaSelector are already (x1, y1, x2, y2) format
            # Convert to (x, y, width, height) format for resource_regions
            x1 = int(min(x, ex))
            y1 = int(min(y, ey))
            x2 = int(max(x, ex))
            y2 = int(max(y, ey))
            
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            if width < 20 or height < 20:
                log_message(f"[warn] Selected area too small: {width}x{height}. Minimum 20x20 pixels required.")
                return
            
            resource_regions[resource_type] = (x1, y1, width, height)
            log_message(f"[info] {resource_type.title()} region saved: x={x1}, y={y1}, width={width}, height={height}")
            
            # Save config immediately
            try:
                save_config()
                log_message(f"[info] {resource_type.title()} region saved to config")
            except Exception as save_err:
                log_message(f"[warn] Failed to save config: {save_err}")
            
            # Update UI to show region is set
            update_resource_button_labels()
            
            # Test read immediately
            log_message(f"[info] Testing OCR read for {resource_type}...")
            update_resource_display(resource_type)
            
        except Exception as exc:
            log_message(f"[error] Failed to select {resource_type} area: {exc}")
            import traceback
            log_message(f"[error] Traceback: {traceback.format_exc()}")

    def update_resource_display(resource_type):
        """Update resource value from OCR"""
        global resource_values
        try:
            region = resource_regions.get(resource_type)
            if not region:
                log_message(f"[debug] No region set for {resource_type}")
                return
            
            # Check OCR availability first
            available, message = is_tesseract_ready_inline()
            if not available:
                # Only log once per resource type to avoid spam
                if not hasattr(update_resource_display, f"_ocr_warned_{resource_type}"):
                    log_message(f"[warn] {resource_type.title()} OCR unavailable: {message}")
                    log_message(f"[info] Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
                    setattr(update_resource_display, f"_ocr_warned_{resource_type}", True)
                return
            
            log_message(f"[debug] Updating {resource_type} display...")
            value = read_resource_value(region)
            if value is not None:
                resource_values[resource_type] = value
                log_message(f"[info] {resource_type.title()} detected: {value:,}")
                
                if resource_type == "coins" and coins_value_ref.current:
                    coins_value_ref.current.value = f"{value:,}"
                    coins_value_ref.current.update()
                elif resource_type == "gems" and gems_value_ref.current:
                    gems_value_ref.current.value = f"{value:,}"
                    gems_value_ref.current.update()
                elif resource_type == "thunder" and thunder_value_ref.current:
                    thunder_value_ref.current.value = f"{value:,}"
                    thunder_value_ref.current.update()
            else:
                # Don't spam logs if OCR is failing repeatedly
                if not hasattr(update_resource_display, f"_read_failed_{resource_type}"):
                    log_message(f"[warn] Could not read {resource_type} value. Check region selection and screen contrast.")
                    setattr(update_resource_display, f"_read_failed_{resource_type}", True)
        except Exception as exc:
            log_message(f"[error] Failed to update {resource_type} display: {exc}")
            import traceback
            log_message(f"[error] Traceback: {traceback.format_exc()}")

    resource_poll_thread = None
    
    def toggle_resource_tracking(enabled):
        """Enable/disable continuous resource tracking"""
        global resource_tracking_enabled
        nonlocal resource_poll_thread
        resource_tracking_enabled = enabled
        
        if enabled:
            # Check OCR availability first
            available, message = is_tesseract_ready_inline()
            if not available:
                log_message(f"[warn] Cannot enable tracking: {message}")
                log_message(f"[info] Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
                resource_tracking_enabled = False
                # Note: We can't easily update the switch UI here, so user will see it's off
                return
            
            log_message("[info] Starting resource tracking...")
            # Check if any regions are set
            has_regions = any(resource_regions.get(key) for key in ["coins", "gems", "thunder"])
            if not has_regions:
                log_message("[warn] No resource regions set. Select areas first.")
                resource_tracking_enabled = False
                return
            
            def poll_resources():
                poll_count = 0
                while resource_tracking_enabled:
                    try:
                        poll_count += 1
                        if poll_count % 10 == 0:  # Log every 10 polls (every 15 seconds)
                            log_message(f"[debug] Resource polling active (poll #{poll_count})")
                        
                        if resource_regions.get("coins"):
                            update_resource_display("coins")
                        if resource_regions.get("gems"):
                            update_resource_display("gems")
                        if resource_regions.get("thunder"):
                            update_resource_display("thunder")
                        time.sleep(1.5)
                    except Exception as exc:
                        log_message(f"[error] Resource polling error: {exc}")
                        import traceback
                        log_message(f"[error] Traceback: {traceback.format_exc()}")
                        time.sleep(2.0)
            
            resource_poll_thread = threading.Thread(target=poll_resources, daemon=True)
            resource_poll_thread.start()
            log_message("[info] Resource tracking enabled - values will update every 1.5s")
        else:
            resource_tracking_enabled = False
            log_message("[info] Resource tracking disabled")
    
    # Tab switching function
    tab_containers = []
    tab_buttons = []
    
    def switch_tab(e, index):
        for i, tab_container in enumerate(tab_containers):
            if i == index:
                tab_container.visible = True
                if i < len(tab_buttons):
                    tab_buttons[i].bgcolor = hex_with_opacity("#FFFFFF", 0.5)
                    tab_buttons[i].border = ft.border.all(2, ACCENT_BLUE)
            else:
                tab_container.visible = False
                if i < len(tab_buttons):
                    tab_buttons[i].bgcolor = hex_with_opacity("#FFFFFF", 0.3)
                    tab_buttons[i].border = ft.border.all(1, GLASS_BORDER)
        page.update()
    
    # Header Section
    header = create_glass_card(
        ft.Column(
            controls=[
                ft.Text(
                    "Kishor Farm Merger Pro",
                    size=32,
                    weight=ft.FontWeight.W_700,
                    color=PURPLE,
                ),
                ft.Text(
                    "Glassmorphism Edition - Smooth, Fast & Beautiful",
                    size=14,
                    color=TEXT_MUTED,
                ),
                ft.Row(
                    controls=[
                        ft.Text("Status: ", color=TEXT_PRIMARY, size=14),
                        ft.Text("Ready", color=SUCCESS_GREEN, size=14, ref=status_text, weight=ft.FontWeight.W_600),
                        ft.Text(" • ", color=TEXT_SUBTLE),
                        ft.Text("Boxes: ", color=TEXT_PRIMARY, size=14),
                        ft.Text(str(box_amount), color=ACCENT_BLUE, size=14, ref=box_count_text, weight=ft.FontWeight.W_600),
                        ft.Text(" • ", color=TEXT_SUBTLE),
                        ft.Text("Detected: ", color=TEXT_PRIMARY, size=14),
                        ft.Text("0 items", color=TEXT_MUTED, size=14, ref=detected_count_text),
                    ],
                    spacing=8,
                ),
            ],
            spacing=8,
        ),
        padding=20,
        margin=ft.margin.all(16),
    )
    
    # Tab Buttons (will be created before tabs)
    tab_names = ["Quick Start", "Detection", "Settings", "Activity", "Grid View", "Automation", "Tests"]
    for i, name in enumerate(tab_names):
        def make_switch(idx):
            return lambda e: switch_tab(e, idx)
        tab_btn = create_glass_tab(name, make_switch(i), i == 0)
        tab_buttons.append(tab_btn)
    
    tab_bar = ft.Row(
        controls=tab_buttons,
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
    )
    
    # Tab 1: Quick Start
    quick_start_tab = ft.Container(
        content=ft.Row(
            controls=[
                # Left: Essential Setup
                ft.Container(
                    content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.Text("Essential Setup", size=20, weight=ft.FontWeight.W_700, color=PURPLE),
                            ft.Text("Get started in 3 steps", size=12, color=TEXT_MUTED),
                            ft.Divider(height=1, color=GLASS_BORDER),
                            ft.Container(height=16),
                            
                            # Step 1
                            ft.Text("STEP 1: Start/Stop Control", size=15, weight=ft.FontWeight.W_600, color=ACCENT_BLUE),
                            ft.Container(height=8),
                            ft.Row(
                                controls=[
                                    create_glass_button(
                                        "Start",
                                        on_click=start_button_callback_wrapper(page, status_text),
                                        width=None,
                                        color=SUCCESS_GREEN,
                                        icon=ft.Icons.PLAY_ARROW,
                                    ),
                                    create_glass_button(
                                        "Stop",
                                        on_click=stop_button_callback_wrapper(page, status_text),
                                        width=None,
                                        color=DANGER_RED,
                                        icon=ft.Icons.STOP,
                                    ),
                                ],
                                spacing=12,
                                expand=True,
                            ),
                            ft.Text("Press = to instantly start/stop", size=12, color=TEXT_SUBTLE),
                            ft.Container(height=24),
                            ft.Divider(height=1, color=GLASS_BORDER),
                            ft.Container(height=16),
                            
                            # Step 2
                            ft.Text("STEP 2: Configure Basics", size=15, weight=ft.FontWeight.W_600, color=ACCENT_BLUE),
                            ft.Container(height=8),
                            
                            ft.Text("Merge Count", size=14, color=TEXT_PRIMARY),
                            ft.RadioGroup(
                                content=ft.Row(
                                    controls=[
                                        ft.Radio(value=3, label="3"),
                                        ft.Radio(value=5, label="5"),
                                        ft.Radio(value=10, label="10"),
                                    ],
                                    spacing=16,
                                ),
                                value=merge_count,
                                on_change=lambda e: update_merge_count_handler(e, status_text),
                            ),
                            
                            ft.Container(height=16),
                            
                            ft.Text("Screen Area", size=14, color=TEXT_PRIMARY),
                            create_glass_button(
                                "Select Area",
                                on_click=select_area_callback_wrapper(page, status_text),
                                width=None,
                            ),
                            ft.Container(height=16),
                            
                            ft.Text("Merge Slots", size=14, color=TEXT_PRIMARY),
                            create_glass_button(
                                "Select Points",
                                on_click=select_merging_points_callback_wrapper(page, status_text),
                                width=None,
                            ),
                            ft.Container(height=24),
                            ft.Divider(height=1, color=GLASS_BORDER),
                            ft.Container(height=16),
                            
                            # Step 3
                            ft.Text("STEP 3: Set Hotkeys", size=15, weight=ft.FontWeight.W_600, color=ACCENT_BLUE),
                            ft.Container(height=8),
                            ft.Text("Start Hotkey", size=14, color=TEXT_PRIMARY),
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.KEYBOARD, color=TEXT_PRIMARY, size=20),
                                        ft.Text(format_hotkey_label(hotkey) if hotkey else "=", ref=hotkey_text_ref, color=TEXT_PRIMARY, size=16, weight=ft.FontWeight.W_600),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=8,
                                ),
                                width=None,
                                height=50,
                                bgcolor=hex_with_opacity("#FFFFFF", 0.3),
                                border=ft.border.all(2, hex_with_opacity("#58B2FF", 0.3)),
                                border_radius=ft.border_radius.all(16),
                                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                                on_click=lambda e: record_hotkey_simple(hotkey_text_ref, status_text),
                                expand=True,
                            ),
                            ft.Container(height=16),
                            ft.Text("Pause Hotkey", size=14, color=TEXT_PRIMARY),
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.KEYBOARD, color=TEXT_PRIMARY, size=20),
                                        ft.Text(format_hotkey_label(stop_hotkey) if stop_hotkey else "=", ref=pause_hotkey_text_ref, color=TEXT_PRIMARY, size=16, weight=ft.FontWeight.W_600),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=8,
                                ),
                                width=None,
                                height=50,
                                expand=True,
                                bgcolor=hex_with_opacity("#FFFFFF", 0.3),
                                border=ft.border.all(2, hex_with_opacity("#58B2FF", 0.3)),
                                border_radius=ft.border_radius.all(16),
                                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                                on_click=lambda e: record_hotkey_simple(pause_hotkey_text_ref, status_text, is_stop=True),
                                
                            ),
                        ],
                        spacing=8,
                        expand=True,
                    ),
                    expand=1,
                    padding=ft.padding.symmetric(horizontal=12, vertical=16),  # Reduced padding
                    border_radius=20,
                ),
                
                # Right: Quick Actions
                ft.Container(
                    content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.Text("Quick Actions", size=24, weight=ft.FontWeight.W_700, color=PURPLE),
                            ft.Text("Common tasks", size=14, color=TEXT_MUTED),
                            ft.Divider(height=1, color=GLASS_BORDER),
                            ft.Container(height=16),
                            
                            create_glass_button(
                                "Detect Items",
                                on_click=lambda e: scan_and_preview_callback(page),
                                width=None,
                                height=60,
                                color=PURPLE,
                            ),
                            ft.Container(height=16),
                            
                            # Stats Cards
                            ft.Row(
                                controls=[
                                    create_glass_card(
                                        ft.Column(
                                            controls=[
                                                ft.Text("Total Detected", size=12, color=TEXT_MUTED),
                                                ft.Text("0", size=32, color=ACCENT_BLUE, weight=ft.FontWeight.W_700),
                                            ],
                                            spacing=8,
                                        ),
                                        padding=16,
                                        margin=4,
                                    ),
                                    create_glass_card(
                                        ft.Column(
                                            controls=[
                                                ft.Text("Unique Types", size=12, color=TEXT_MUTED),
                                                ft.Text("0", size=32, color=PURPLE, weight=ft.FontWeight.W_700),
                                            ],
                                            spacing=8,
                                        ),
                                        padding=16,
                                        margin=4,
                                    ),
                                ],
                                spacing=12,
                            ),
                        ],
                        spacing=8,
                    ),
                    expand=1,
                    padding=20,
                    border_radius=20,
                ),
            ],
            spacing=20,
            expand=True,
        ),
        visible=True,
    )
    
    # Tab 2: Detection with item preview - 3 MODES + THRESHOLD TUNING
    global detection_items_container_ref, detection_total_ref, detection_types_ref, gpu_status_ref
    global detection_mode_ref, global_threshold_ref, advanced_tuning_container_ref
    detection_items_container_ref = ft.Ref[ft.Column]()
    detection_total_ref = ft.Ref[ft.Text]()
    detection_types_ref = ft.Ref[ft.Text]()
    gpu_status_ref = ft.Ref[ft.Text]()
    detection_mode_ref = ft.Ref[ft.Text]()
    global_threshold_ref = ft.Ref[ft.Slider]()
    advanced_tuning_container_ref = ft.Ref[ft.Container]()
    
    # Check GPU status
    gpu_available = check_gpu_available()
    
    # Get all template files for advanced tuning
    img_folder = "./img"
    all_templates = []
    if os.path.exists(img_folder):
        all_templates = [f for f in os.listdir(img_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        all_templates.sort()
    
    # Get GPU status for display
    gpu_available = check_gpu_available()
    mode_status_texts = {
        "cpu": "CPU Mode - Most Accurate",
        "gpu": "GPU Mode - Fast + Accurate (AMD Optimized with CPU Verify)" if gpu_available else "GPU Mode - GPU Not Available (Using CPU)",
        "hybrid": "Hybrid Mode - Fast + Accurate" if gpu_available else "Hybrid Mode - GPU Not Available (Using CPU)",
        "express": "Express Mode - ULTRA FAST (GPU only, no verification)" if gpu_available else "Express Mode - GPU Not Available (Using CPU)"
    }
    current_status_text = mode_status_texts.get(detection_mode, f"{detection_mode.upper()} Mode")
    
    detection_tab = ft.Container(
        content=ft.Column(
            controls=[
                # Header
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Detection Preview", size=24, weight=ft.FontWeight.W_700, color=PURPLE),
                                ft.Text("Item detection and board scanning", size=14, color=TEXT_MUTED),
                            ],
                            expand=True,
                        ),
                    ],
                ),
                ft.Container(height=12),
                
                # GPU Status Indicator
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.SPEED if gpu_available else ft.Icons.SPEED_OUTLINED,
                                color=ACCENT_BLUE if gpu_available else TEXT_MUTED,
                                size=16,
                            ),
                            ft.Text(
                                current_status_text,
                                size=12,
                                color=ACCENT_BLUE if gpu_available else TEXT_MUTED,
                                weight=ft.FontWeight.W_600,
                                ref=gpu_status_ref,
                            ),
                        ],
                        spacing=6,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=hex_with_opacity(ACCENT_BLUE if gpu_available else TEXT_MUTED, 0.15),
                    border=ft.border.all(1, hex_with_opacity(ACCENT_BLUE if gpu_available else TEXT_MUTED, 0.3)),
                    border_radius=8,
                ),
                ft.Container(height=24),
                
                # Detection Mode Selector (4 buttons)
                ft.Text("Detection Mode", size=16, weight=ft.FontWeight.W_600, color=ACCENT_BLUE),
                ft.Container(height=8),
                ft.Row(
                    controls=[
                        create_glass_button(
                            "CPU",
                            on_click=lambda e: set_detection_mode("cpu", page, detection_mode_ref, gpu_status_ref, advanced_tuning_container_ref),
                            width=140,
                            height=50,
                            color=ACCENT_BLUE if detection_mode == "cpu" else TEXT_MUTED,
                        ),
                        create_glass_button(
                            "GPU",
                            on_click=lambda e: set_detection_mode("gpu", page, detection_mode_ref, gpu_status_ref, advanced_tuning_container_ref),
                            width=140,
                            height=50,
                            color=SUCCESS_GREEN if detection_mode == "gpu" else TEXT_MUTED,
                        ),
                        create_glass_button(
                            "Hybrid",
                            on_click=lambda e: set_detection_mode("hybrid", page, detection_mode_ref, gpu_status_ref, advanced_tuning_container_ref),
                            width=140,
                            height=50,
                            color=PURPLE if detection_mode == "hybrid" else TEXT_MUTED,
                        ),
                        create_glass_button(
                            "Express",
                            on_click=lambda e: set_detection_mode("express", page, detection_mode_ref, gpu_status_ref, advanced_tuning_container_ref),
                            width=140,
                            height=50,
                            color="#FF6B35" if detection_mode == "express" else TEXT_MUTED,
                        ),
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(
                    content=ft.Text(
                        f"Current: {detection_mode.upper()} Mode",
                        size=12,
                        color=TEXT_SUBTLE,
                        ref=detection_mode_ref,
                    ),
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=24),
                
                # Global Threshold Slider
                ft.Text("Global Detection Threshold", size=16, weight=ft.FontWeight.W_600, color=ACCENT_BLUE),
                ft.Container(height=8),
                ft.Row(
                    controls=[
                        ft.Text("0.50", size=12, color=TEXT_MUTED),
                        ft.Slider(
                            min=0.50,
                            max=0.95,
                            divisions=45,
                            value=global_threshold,
                            label="{value}",
                            on_change=lambda e: update_global_threshold(e, page),
                            ref=global_threshold_ref,
                            expand=True,
                        ),
                        ft.Text("0.95", size=12, color=TEXT_MUTED),
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Text(
                    f"Threshold: {global_threshold:.2f} (lower = more sensitive, higher = more strict)",
                    size=11,
                    color=TEXT_SUBTLE,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=24),
                
                # Action Buttons
                ft.Row(
                    controls=[
                        create_glass_button(
                            "Show Preview",
                            on_click=lambda e: scan_and_preview_callback(page),
                            width=200,
                            height=55,
                            color=PURPLE,
                        ),
                        create_glass_button(
                            "Live Detection",
                            on_click=lambda e: toggle_live_detection_button(e, page),
                            width=200,
                            height=55,
                            color=ACCENT_BLUE,
                        ),
                    ],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=24),
                
                # Advanced GPU Tuning Panel (only visible in GPU/Hybrid modes)
                ft.Container(
                    content=create_advanced_gpu_tuning_panel(all_templates, page, advanced_tuning_container_ref),
                    ref=advanced_tuning_container_ref,
                    visible=(detection_mode in ["gpu", "hybrid"]),
                ),
                ft.Container(height=24),
                
                # Stats Row
                ft.Row(
                    controls=[
                        create_glass_card(
                            ft.Column(
                                controls=[
                                    ft.Text("Total Detected", size=12, color=TEXT_MUTED),
                                    ft.Text("0 items", size=24, color=ACCENT_BLUE, weight=ft.FontWeight.W_600, ref=detection_total_ref),
                                ],
                                spacing=8,
                            ),
                            padding=16,
                            margin=4,
                        ),
                        create_glass_card(
                            ft.Column(
                                controls=[
                                    ft.Text("Unique Types", size=12, color=TEXT_MUTED),
                                    ft.Text("0 types", size=24, color=PURPLE, weight=ft.FontWeight.W_600, ref=detection_types_ref),
                                ],
                                spacing=8,
                            ),
                            padding=16,
                            margin=4,
                        ),
                    ],
                    spacing=12,
                ),
                ft.Container(height=24),
                
                # Detected Items List
                ft.Text("Detected Items", size=18, weight=ft.FontWeight.W_600, color=ACCENT_BLUE),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Column(
                        controls=[],
                        spacing=8,
                        ref=detection_items_container_ref,
                    ),
                    expand=True,
                    padding=12,
                    border_radius=12,
                    bgcolor=hex_with_opacity("#FFFFFF", 0.1),
                    border=ft.border.all(1, GLASS_BORDER),
                ),
                ft.Container(height=24),
                
                # Resource tracking section
                ft.Divider(height=1, color=GLASS_BORDER),
                ft.Container(height=16),
                ft.Text("Resource Tracking", size=18, weight=ft.FontWeight.W_600, color=ACCENT_BLUE),
                ft.Container(height=12),
                
                ft.Row(
                    controls=[
                        create_glass_card(
                            ft.Column(
                                controls=[
                                    ft.Text("Coins", size=12, color=TEXT_MUTED),
                                    ft.Text("0", size=24, color=WARNING_ORANGE, weight=ft.FontWeight.W_600, ref=coins_value_ref),
                                ],
                                spacing=8,
                            ),
                            padding=16,
                        ),
                        create_glass_card(
                            ft.Column(
                                controls=[
                                    ft.Text("Gems", size=12, color=TEXT_MUTED),
                                    ft.Text("0", size=24, color=PURPLE, weight=ft.FontWeight.W_600, ref=gems_value_ref),
                                ],
                                spacing=8,
                            ),
                            padding=16,
                        ),
                        create_glass_card(
                            ft.Column(
                                controls=[
                                    ft.Text("Thunder", size=12, color=TEXT_MUTED),
                                    ft.Text("0", size=24, color=ACCENT_BLUE, weight=ft.FontWeight.W_600, ref=thunder_value_ref),
                                ],
                                spacing=8,
                            ),
                            padding=16,
                        ),
                    ],
                    spacing=12,
                ),
                ft.Container(height=12),
                
                ft.Row(
                    controls=[
                        create_glass_button(
                            "Select Coin Area",
                            on_click=lambda e: select_resource_area("coins"),
                            width=None,
                            color=WARNING_ORANGE,
                        ),
                        create_glass_button(
                            "Select Gem Area",
                            on_click=lambda e: select_resource_area("gems"),
                            width=None,
                            color=PURPLE,
                        ),
                        create_glass_button(
                            "Select Thunder Area",
                            on_click=lambda e: select_resource_area("thunder"),
                            width=None,
                            color=ACCENT_BLUE,
                        ),
                    ],
                    spacing=12,
                ),
                ft.Container(height=12),
                
                ft.Row(
                    controls=[
                        ft.Switch(
                            label="Auto-track resources",
                            value=False,
                            on_change=lambda e: toggle_resource_tracking(e.control.value),
                        ),
                    ],
                ),
                ft.Container(height=12),
                
                # OCR status message
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "Note: Resource tracking requires Tesseract OCR",
                                size=11,
                                color=TEXT_SUBTLE,
                            ),
                            ft.Text(
                                "Download: https://github.com/UB-Mannheim/tesseract/wiki",
                                size=10,
                                color=ACCENT_BLUE,
                                selectable=True,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=12,
                    bgcolor=hex_with_opacity("#FFFFFF", 0.1),
                    border_radius=8,
                ),
                ft.Container(height=24),
                
                # Board scanning section
                ft.Divider(height=1, color=GLASS_BORDER),
                ft.Container(height=16),
                ft.Text("Board Detection", size=18, weight=ft.FontWeight.W_600, color=PURPLE),
                ft.Container(height=12),
                create_glass_button(
                    "Scan Board Layout",
                    on_click=lambda e: scan_board_button_callback(),
                    width=None,
                    color=PURPLE,
                ),
            ],
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        visible=False,
        expand=True,
    )
    
    # Grid View Helper Functions
    def create_game_grid_view(detection_results, game_area, grid_size=(10, 10)):
        """
        Create a 2D grid visualization of detected objects.
        
        Args:
            detection_results: Dict with template names and detected points
            game_area: Tuple (start_x, start_y, end_x, end_y) of game area
            grid_size: Tuple (rows, cols) for the grid
        """
        if not game_area or len(game_area) != 4:
            return ft.Container(
                content=ft.Text("Game area not set. Please select your game area first.", color=DANGER_RED, size=14),
                padding=20,
                alignment=ft.alignment.center
            )
        
        start_x, start_y, end_x, end_y = game_area
        width = end_x - start_x
        height = end_y - start_y
        rows, cols = grid_size
        
        cell_width = width / cols
        cell_height = height / rows
        
        # Create a grid map: (row, col) -> list of items
        grid_map = {}
        for r in range(rows):
            for c in range(cols):
                grid_map[(r, c)] = []
        
        # Map detected objects to grid cells
        total_items = 0
        for template_name, data in detection_results.items():
            points = data.get('points', [])
            item_name = os.path.splitext(template_name)[0]
            template_path = data.get('template_path', '')
            
            for point in points:
                px, py = point
                # Convert to relative coordinates
                rel_x = px - start_x
                rel_y = py - start_y
                
                # Calculate grid position
                col = min(cols - 1, max(0, int(rel_x / cell_width)))
                row = min(rows - 1, max(0, int(rel_y / cell_height)))
                
                grid_map[(row, col)].append({
                    "name": item_name,
                    "pos": (px, py),
                    "template": template_name,
                    "template_path": template_path
                })
                total_items += 1
        
        # Build row-by-row
        grid_rows = []
        empty_count = 0
        filled_count = 0
        
        for r in range(rows):
            grid_cols = []
            for c in range(cols):
                items = grid_map[(r, c)]
                
                # Create cell widget
                if items:
                    filled_count += 1
                    # Get the first item
                    first_item = items[0]
                    item_name = first_item["name"]
                    template_path = first_item.get("template_path", "")
                    
                    # Determine cell color based on item count
                    if len(items) > 1:
                        cell_bg = ft.Colors.with_opacity(0.4, ft.Colors.ORANGE)
                        border_color = ft.Colors.ORANGE_400
                    else:
                        cell_bg = ft.Colors.with_opacity(0.3, ft.Colors.GREEN)
                        border_color = ft.Colors.GREEN_400
                    
                    # Create cell content
                    cell_content_items = []
                    
                    # Try to show item image if exists
                    if template_path and os.path.exists(template_path):
                        cell_content_items.append(
                            ft.Image(
                                src=template_path,
                                width=35,
                                height=35,
                                fit=ft.ImageFit.CONTAIN,
                                error_content=ft.Text(item_name[:4], size=9, color=ft.Colors.WHITE)
                            )
                        )
                    else:
                        cell_content_items.append(
                            ft.Text(item_name[:6], size=9, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600)
                        )
                    
                    # Show count if multiple items
                    if len(items) > 1:
                        cell_content_items.append(
                            ft.Container(
                                content=ft.Text(f"×{len(items)}", size=8, color=ft.Colors.YELLOW, weight=ft.FontWeight.BOLD),
                                bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
                                padding=ft.padding.symmetric(horizontal=4, vertical=2),
                                border_radius=4
                            )
                        )
                    
                    # Build tooltip text
                    tooltip_text = f"Cell ({r},{c}): {item_name}"
                    if len(items) > 1:
                        other_items = [item["name"] for item in items[1:]]
                        tooltip_text += f"\n+ {', '.join(other_items[:3])}"
                        if len(items) > 4:
                            tooltip_text += f"\n... and {len(items) - 4} more"
                    
                    cell = ft.Container(
                        content=ft.Column(
                            controls=cell_content_items,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2
                        ),
                        width=50,
                        height=50,
                        bgcolor=cell_bg,
                        border=ft.border.all(1, border_color),
                        border_radius=5,
                        tooltip=tooltip_text,
                        padding=4
                    )
                else:
                    empty_count += 1
                    # Empty cell
                    cell = ft.Container(
                        content=ft.Text(f"{r},{c}", size=7, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
                        width=50,
                        height=50,
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                        border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                        border_radius=5,
                        alignment=ft.alignment.center
                    )
                
                grid_cols.append(cell)
            
            grid_rows.append(
                ft.Row(
                    controls=grid_cols,
                    spacing=2,
                    alignment=ft.MainAxisAlignment.START
                )
            )
        
        # Create stats row
        stats_row = ft.Row(
            controls=[
                ft.Text(f"Grid: {rows}×{cols}", size=12, color=TEXT_PRIMARY),
                ft.Text("•", size=12, color=TEXT_SUBTLE),
                ft.Text(f"Filled: {filled_count}", size=12, color=SUCCESS_GREEN),
                ft.Text("•", size=12, color=TEXT_SUBTLE),
                ft.Text(f"Empty: {empty_count}", size=12, color=TEXT_MUTED),
                ft.Text("•", size=12, color=TEXT_SUBTLE),
                ft.Text(f"Total Items: {total_items}", size=12, color=ACCENT_BLUE),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        return ft.Column(
            controls=[
                stats_row,
                ft.Divider(height=1, color=GLASS_BORDER),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Column(
                        controls=grid_rows,
                        spacing=2,
                        scroll=ft.ScrollMode.AUTO
                    ),
                    expand=True
                )
            ],
            spacing=8,
            expand=True
        )
    
    # Tab 3: Settings (placeholder)
    settings_tab = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Settings", size=24, weight=ft.FontWeight.W_700, color=PURPLE),
                ft.Text("Configure automation parameters", size=14, color=TEXT_MUTED),
                ft.Container(height=24),
                ft.Row(
                    controls=[
                        create_glass_button(
                            "Save Settings",
                            on_click=lambda e: manual_save_callback_wrapper(),
                            width=None,
                            color=ACCENT_BLUE,
                        ),
                        create_glass_button(
                            "Load Settings",
                            on_click=lambda e: manual_load_callback_wrapper(),
                            width=None,
                            color=PURPLE,
                        ),
                    ],
                    spacing=12,
                    expand=True,
                ),
                ft.Container(height=24),
                ft.Text("Quick Collection", size=18, weight=ft.FontWeight.W_600, color=ACCENT_BLUE),
                ft.Row(
                    controls=[
                        create_glass_button(
                            "Collect",
                            on_click=lambda e: start_quick_collection("items"),
                            width=None,
                            height=50,
                        ),
                        create_glass_button(
                            "Game UI",
                            on_click=lambda e: start_quick_collection("ui_elements"),
                            width=None,
                            height=50,
                        ),
                        create_glass_button(
                            "Cut Items",
                            on_click=lambda e: start_quick_collection("producers"),
                            width=None,
                            height=50,
                        ),
                    ],
                    spacing=12,
                    expand=True,
                ),
                ft.Row(
                    controls=[
                        ft.TextButton(
                            "View item templates",
                            on_click=lambda e: safe_show_template_preview("items"),
                        ),
                        ft.TextButton(
                            "View UI templates",
                            on_click=lambda e: safe_show_template_preview("ui_elements"),
                        ),
                        ft.TextButton(
                            "View producer templates",
                            on_click=lambda e: safe_show_template_preview("producers"),
                        ),
                    ],
                    spacing=8,
                ),
            ],
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        visible=False,
        expand=True,
    )
    
    # Tab 4: Activity Log (placeholder)
    activity_tab = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Activity Log", size=24, weight=ft.FontWeight.W_700, color=PURPLE),
                ft.Text("Full automation history", size=14, color=TEXT_MUTED),
                ft.Container(height=24),
                ft.Container(
                    content=ft.Column(
                        controls=[],
                        spacing=4,
                        ref=log_view,
                    ),
                    expand=True,
                    padding=16,
                    border_radius=12,
                    bgcolor=hex_with_opacity("#FFFFFF", 0.2),
                    border=ft.border.all(1, GLASS_BORDER),
                ),
            ],
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        visible=False,
        expand=True,
    )
    
    # Tab 5: Grid View (2D Visualization)
    grid_view_ref = ft.Ref[ft.Container]()
    grid_size_rows_ref = ft.Ref[ft.TextField]()
    grid_size_cols_ref = ft.Ref[ft.TextField]()
    
    def update_grid_view():
        """Refresh the grid visualization with current detection results"""
        global last_detection_results, area, board_rows, board_cols
        
        try:
            if not last_detection_results:
                grid_view_ref.current.content = create_glass_card(
                    ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=WARNING_ORANGE, size=48),
                            ft.Container(height=16),
                            ft.Text("No detection data available", size=16, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600),
                            ft.Text("Run a scan from the Detection tab first", size=13, color=TEXT_MUTED),
                            ft.Container(height=16),
                            create_glass_button(
                                "Go to Detection Tab",
                                on_click=lambda e: switch_tab(e, 1),  # Switch to Detection tab
                                width=None,
                                color=ACCENT_BLUE
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8
                    ),
                    padding=40
                )
                grid_view_ref.current.update()
                return
            
            rows = int(grid_size_rows_ref.current.value or board_rows)
            cols = int(grid_size_cols_ref.current.value or board_cols)
            
            # Validate grid size
            if rows <= 0 or cols <= 0 or rows > 20 or cols > 20:
                grid_view_ref.current.content = create_glass_card(
                    ft.Text("Invalid grid size. Please enter values between 1 and 20.", color=DANGER_RED, size=14),
                    padding=20
                )
                grid_view_ref.current.update()
                return
            
            # Create the grid widget
            grid_widget = create_game_grid_view(
                last_detection_results, 
                area, 
                grid_size=(rows, cols)
            )
            
            grid_view_ref.current.content = create_glass_card(grid_widget, padding=16)
            grid_view_ref.current.update()
            
            update_log(f"[info] Grid view updated: {rows}×{cols} grid")
        except Exception as ex:
            update_log(f"[error] Failed to update grid view: {ex}")
            grid_view_ref.current.content = create_glass_card(
                ft.Text(f"Error: {str(ex)}", color=DANGER_RED, size=12),
                padding=20
            )
            grid_view_ref.current.update()
    
    def scan_and_update_grid(e):
        """Run detection scan and update grid view"""
        update_log("[info] Running detection scan for grid view...")
        # Trigger detection scan
        scan_and_preview_callback(page)
        # Wait a moment for scan to complete, then update grid
        import threading
        def delayed_update():
            time.sleep(0.5)
            update_grid_view()
        threading.Thread(target=delayed_update, daemon=True).start()
    
    grid_view_tab = ft.Container(
        content=ft.Column(
            controls=[
                # Header
                ft.Row(
                    controls=[
                        ft.Text("2D Game Grid", size=24, weight=ft.FontWeight.W_700, color=PURPLE),
                        ft.Icon(ft.Icons.GRID_VIEW, color=PURPLE, size=32),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12
                ),
                ft.Text(
                    "Visual representation of detected objects in grid coordinates",
                    size=13,
                    color=TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Divider(height=1, color=GLASS_BORDER),
                ft.Container(height=8),
                
                # Controls
                create_glass_card(
                    ft.Column(
                        controls=[
                            ft.Text("Grid Configuration", size=16, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Container(height=8),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                ft.Text("Rows", size=12, color=TEXT_MUTED),
                                                ft.TextField(
                                                    ref=grid_size_rows_ref,
                                                    value=str(board_rows),
                                                    width=80,
                                                    text_align=ft.TextAlign.CENTER,
                                                    bgcolor=hex_with_opacity("#FFFFFF", 0.1),
                                                    border_color=GLASS_BORDER,
                                                    focused_border_color=ACCENT_BLUE,
                                                    text_size=14,
                                                    height=45
                                                ),
                                            ],
                                            spacing=4,
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                        ),
                                        expand=False
                                    ),
                                    ft.Text("×", size=20, color=TEXT_SUBTLE),
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                ft.Text("Columns", size=12, color=TEXT_MUTED),
                                                ft.TextField(
                                                    ref=grid_size_cols_ref,
                                                    value=str(board_cols),
                                                    width=80,
                                                    text_align=ft.TextAlign.CENTER,
                                                    bgcolor=hex_with_opacity("#FFFFFF", 0.1),
                                                    border_color=GLASS_BORDER,
                                                    focused_border_color=ACCENT_BLUE,
                                                    text_size=14,
                                                    height=45
                                                ),
                                            ],
                                            spacing=4,
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                        ),
                                        expand=False
                                    ),
                                    ft.Container(width=16),
                                    create_glass_button(
                                        "Update Grid",
                                        on_click=lambda e: update_grid_view(),
                                        width=140,
                                        icon=ft.Icons.REFRESH,
                                        color=ACCENT_BLUE
                                    ),
                                    create_glass_button(
                                        "Scan & Update",
                                        on_click=scan_and_update_grid,
                                        width=140,
                                        icon=ft.Icons.SEARCH,
                                        color=SUCCESS_GREEN
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=12,
                                wrap=True
                            ),
                        ],
                        spacing=8
                    ),
                    padding=16
                ),
                
                ft.Container(height=8),
                
                # Grid view container
                ft.Container(
                    ref=grid_view_ref,
                    content=create_glass_card(
                        ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.GRID_ON, color=TEXT_SUBTLE, size=64),
                                ft.Container(height=16),
                                ft.Text("Click 'Update Grid' to visualize detected objects", size=14, color=TEXT_MUTED),
                                ft.Text("or 'Scan & Update' to run a fresh detection scan", size=12, color=TEXT_SUBTLE),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8
                        ),
                        padding=40
                    ),
                    expand=True
                ),
                
                # Legend
                ft.Container(height=8),
                create_glass_card(
                    ft.Row(
                        controls=[
                            ft.Text("Legend:", size=12, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600),
                            ft.Container(
                                content=ft.Text("Green", size=10, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.GREEN),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4,
                                border=ft.border.all(1, ft.Colors.GREEN_400)
                            ),
                            ft.Text("= Single item", size=11, color=TEXT_MUTED),
                            ft.Container(width=8),
                            ft.Container(
                                content=ft.Text("Orange", size=10, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.ORANGE),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4,
                                border=ft.border.all(1, ft.Colors.ORANGE_400)
                            ),
                            ft.Text("= Multiple items", size=11, color=TEXT_MUTED),
                            ft.Container(width=8),
                            ft.Container(
                                content=ft.Text("Gray", size=10, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
                                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4,
                                border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE))
                            ),
                            ft.Text("= Empty cell", size=11, color=TEXT_MUTED),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        wrap=True
                    ),
                    padding=12
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        ),
        padding=20,
        visible=False,
        expand=True,
    )
    
    # Add tabs to containers list (must be after tabs are defined)
    tab_containers.extend([quick_start_tab, detection_tab, settings_tab, activity_tab, grid_view_tab])
    
    # Add Automation and Tests tabs if available
    automation_orchestrator_ref = [None]  # Use list to allow modification
    
    def get_area():
        return area if area else tuple()
    
    def get_config():
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    if UNIFIED_INTEGRATION_AVAILABLE and add_automation_and_tests_tabs:
        try:
            automation_orchestrator_ref[0] = add_automation_and_tests_tabs(
                page=page,
                tab_containers=tab_containers,
                tab_names=tab_names,
                status_ref=status_text,
                log_callback=update_log,
                area_getter=get_area,
                config_getter=get_config
            )
            update_log("[info] Automation and Tests tabs added successfully")
        except Exception as e:
            update_log(f"[error] Failed to add automation tabs: {e}")
            import traceback
            update_log(f"[error] Traceback: {traceback.format_exc()}")
    
    # Main Layout
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Container(
                        content=tab_bar,
                        padding=ft.padding.symmetric(horizontal=16),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=tab_containers,
                            spacing=0,
                            expand=True,
                        ),
                        expand=True,
                        padding=16,
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Press = key to start/stop instantly",
                            size=12,
                            color=TEXT_SUBTLE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        padding=12,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            padding=0,
        )
    )

    global _log_callback
    _log_callback = update_log
    if _pending_log_messages:
        for pending_message, pending_level in list(_pending_log_messages):
            update_log(pending_message, pending_level)
        _pending_log_messages.clear()

    # Load config on startup
    if load_config:
        load_config()
        # Initialize saved resource regions
        log_message("[info] Loading saved resource regions...")
        for res_type in ["coins", "gems", "thunder"]:
            if resource_regions.get(res_type):
                log_message(f"[info] Found saved {res_type} region: {resource_regions[res_type]}")
                # Try to read value immediately
                try:
                    update_resource_display(res_type)
                except:
                    pass
    
    # Initialize live detection manager (will be initialized with game area when needed)
    global live_detection_manager
    live_detection_manager = None
    if LIVE_DETECTION_AVAILABLE:
        update_log("[info] Live detection overlay available")
    
    # Initialize log
    update_log("Farm Merger Pro initialized")
    update_status("Ready", SUCCESS_GREEN)


def main():
    """Entry point for Flet GUI"""
    multiprocessing.freeze_support()
    ft.app(target=create_flet_gui, view=ft.AppView.FLET_APP, assets_dir="assets")


if __name__ == "__main__":
    main()
