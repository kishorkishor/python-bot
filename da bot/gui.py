"""Kishor Farm Merger Pro GUI module."""

import json
import multiprocessing
import os
import re
import time
from datetime import datetime
from multiprocessing import Process, Queue

import cv2
import dearpygui.dearpygui as dpg
import keyboard
import numpy as np
from pyautogui_safe import pyautogui



from item_finder import ImageFinder

from merging_points_selector import MergingPointsSelector

from screen_area_selector import ScreenAreaSelector

from template_collector import TemplateCollector





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

box_amount = 6  # >= 0

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
box_counter_refresh_active = False



# Ultra-Modern Glassmorphism Theme - Smooth & Professional
ACCENT_COLOR = (88, 178, 255, 255)      # Vibrant Blue
ACCENT_DARK = (52, 144, 220, 255)       # Deep Blue
ACCENT_LIGHT = (120, 200, 255, 255)     # Sky Blue
SECONDARY_ACCENT = (160, 90, 255, 255)  # Purple
PURPLE_ACCENT = (180, 110, 255, 255)    # Light Purple

SUCCESS_COLOR = (76, 217, 100, 255)     # Fresh Green
WARNING_COLOR = (255, 184, 0, 255)      # Warm Orange
DANGER_COLOR = (255, 90, 95, 255)       # Coral Red

TEXT_PRIMARY = (255, 255, 255, 255)     # Pure White
TEXT_MUTED = (180, 190, 210, 255)       # Light Gray
TEXT_SUBTLE = (130, 140, 160, 255)      # Medium Gray

# Glassmorphism gradient background (frost-like)
WINDOW_BG = (18, 18, 28, 255)           # Deep Dark Blue
PANEL_BG = (36, 40, 56, 200)            # Frosted glass panel (more transparent)
SURFACE_BG = (44, 50, 70, 190)          # Frosted surface layer
CARD_BG = (52, 58, 82, 180)             # Frosted card with higher translucency

GLASS_BORDER = (160, 200, 255, 120)     # Softer, lighter border
GLASS_HIGHLIGHT = (200, 230, 255, 80)   # Brighter subtle glow
SHADOW_COLOR = (0, 0, 0, 200)           # Deep shadow



FONTS = {}

APP_NAME = "Kishor Farm Merger Pro"
APP_VERSION = "v2.4.2"
APP_SUBTITLE = "Glassmorphism Edition - Smooth, Fast & Beautiful"
APP_LOG_MESSAGE = f"[info] {APP_NAME} {APP_VERSION} - Production Ready"
APP_READY_MESSAGE = f"{APP_NAME} ultra-modern edition ready.\n"





class LogQueue:

    def __init__(self):

        self.queue = Queue()



    def get_queue(self):

        return self.queue





queue = LogQueue()



CONFIG_FILE = "farm_merger_config.json"





def load_fonts():

    """Register fonts for larger, polished typography."""

    global FONTS

    FONTS = {}

    windows_font_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")

    regular_path = os.path.join(windows_font_dir, "segoeui.ttf")

    semibold_path = os.path.join(windows_font_dir, "seguisb.ttf")

    bold_path = os.path.join(windows_font_dir, "segoeuib.ttf")



    if not os.path.exists(regular_path):

        return



    with dpg.font_registry():

        FONTS["primary"] = dpg.add_font(regular_path, 18)

        FONTS["header"] = dpg.add_font(semibold_path if os.path.exists(semibold_path) else regular_path, 24)

        FONTS["hero"] = dpg.add_font(bold_path if os.path.exists(bold_path) else regular_path, 34)

        FONTS["button"] = dpg.add_font(semibold_path if os.path.exists(semibold_path) else regular_path, 20)



    dpg.bind_font(FONTS["primary"])





def save_config():

    """Persist the current configuration to disk."""

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

        "advanced_settings": {

            "board_rows": board_rows,

            "board_cols": board_cols,

            "disallowed_slots": list(disallowed_slots),

            "slot_overrides": {slot_id: list(coords) for slot_id, coords in slot_overrides.items()},

            "auto_board_detection": auto_board_detection_enabled,

        },

    }

    try:

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:

            json.dump(config, f, indent=4)

        if dpg.does_item_exist("autosave_status"):

            dpg.set_value("autosave_status", "Last saved just now")

    except Exception as exc:

        log_message(f"[error] Unable to save configuration: {exc}")





def manual_save_callback():

    save_config()

    log_message("[info] Configuration saved.")





def manual_load_callback():

    load_config()

    log_message("[info] Configuration loaded.")





def load_config():

    """Load configuration from disk and update the UI."""

    global merge_count, area, hotkey, stop_hotkey, merging_points, resize_factor

    global drag_duration_seconds, box_button_point, box_amount

    global board_rows, board_cols, disallowed_slots, slot_overrides

    global auto_board_detection_enabled, box_counter_region



    if not os.path.exists(CONFIG_FILE):

        log_message("[warn] No saved configuration found. Using defaults.")

        return



    try:

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:

            config = json.load(f)



        merge_count = config.get("merge_count", 5)

        area = tuple(config.get("area", []))

        hotkey = set(config.get("hotkey", ["="]))

        stop_hotkey = set(config.get("stop_hotkey", ["="]))

        merging_points = config.get("merging_points", [])

        resize_factor = config.get("resize_factor", 1.2)

        drag_duration_seconds = config.get("drag_duration_seconds", 0.55)

        box_button_point = tuple(config.get("box_button_point", []))

        box_amount = config.get("box_amount", 6)

        advanced = config.get("advanced_settings", {})

        board_rows = int(advanced.get("board_rows", board_rows))

        board_cols = int(advanced.get("board_cols", board_cols))

        auto_board_detection_enabled = bool(
            advanced.get("auto_board_detection", auto_board_detection_enabled)
        )

        disallowed_values = advanced.get("disallowed_slots", [])

        disallowed_slots = set(str(v) for v in disallowed_values)

        overrides_raw = advanced.get("slot_overrides", {})

        slot_overrides = {

            str(slot_id): tuple(coords)

            for slot_id, coords in overrides_raw.items()

            if isinstance(coords, (list, tuple)) and len(coords) == 2

        }

        region_raw = config.get("box_counter_region", ())
        if isinstance(region_raw, (list, tuple)) and len(region_raw) == 4:
            try:
                box_counter_region = tuple(int(v) for v in region_raw)
            except (TypeError, ValueError):
                box_counter_region = tuple()
        else:
            box_counter_region = tuple()



        if dpg.does_item_exist("merge_count"):

            dpg.set_value("merge_count", merge_count)

        if dpg.does_item_exist("resize_factor"):

            dpg.set_value("resize_factor", f"{resize_factor}")

        if dpg.does_item_exist("drag_duration"):

            dpg.set_value("drag_duration", drag_duration_seconds)

        update_box_amount_ui(box_amount)
        refresh_box_counter_controls()
        if box_counter_region:
            maybe_update_box_count_from_ocr(force=True)


        if dpg.does_item_exist("hotkey_display"):

            dpg.set_item_label("hotkey_display", format_hotkey_label(hotkey))

        if dpg.does_item_exist("stop_hotkey_display"):

            dpg.set_item_label("stop_hotkey_display", format_hotkey_label(stop_hotkey))

        if area and len(area) == 4 and dpg.does_item_exist("area_info"):

            dpg.set_item_label("area_info", format_selection_label(area))

        if merging_points and dpg.does_item_exist("merging_points"):

            dpg.set_item_label(

                "merging_points", format_selection_label(f"{len(merging_points)} points")

            )

        if box_button_point and dpg.does_item_exist("box_button_info"):

            dpg.set_item_label("box_button_info", format_selection_label(box_button_point))

        if dpg.does_item_exist("board_rows_input"):

            dpg.set_value("board_rows_input", board_rows)

        if dpg.does_item_exist("board_cols_input"):

            dpg.set_value("board_cols_input", board_cols)

        refresh_board_detection_controls()



        log_message("[info] Configuration loaded successfully.")

        apply_slot_overrides()

        refresh_board_slot_table()

        refresh_sort_plan_table()

        update_run_sort_plan_button_state()

        # Startup validation
        log_message(APP_LOG_MESSAGE)
        log_message("[info] Press = key to instantly start/stop merging")
        
        if not os.path.exists("./img"):
            log_message("[warn] img folder not found. Please add image files.")
        elif not any(f.endswith((".png", ".jpg", ".jpeg")) for f in os.listdir("./img")):
            log_message("[warn] No image files found in img folder.")
        else:
            image_count = len([f for f in os.listdir("./img") if f.endswith((".png", ".jpg", ".jpeg"))])
            log_message(f"[info] Found {image_count} image files ready for detection")

    except Exception as exc:

        log_message(f"[error] Unable to load configuration: {exc}")





def setup_app_theme():
    """Configure an ultra-modern glassmorphism theme with smooth animations."""

    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, WINDOW_BG)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, PANEL_BG)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, SURFACE_BG)
            dpg.add_theme_color(dpg.mvThemeCol_Border, GLASS_BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT_PRIMARY)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, TEXT_SUBTLE)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, CARD_BG)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (48, 56, 78, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (62, 72, 98, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Button, ACCENT_COLOR)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, ACCENT_LIGHT)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, ACCENT_DARK)
            dpg.add_theme_color(dpg.mvThemeCol_Header, PURPLE_ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, SECONDARY_ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (140, 70, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, ACCENT_COLOR)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, SECONDARY_ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, PURPLE_ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_Separator, GLASS_BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (35, 40, 58, 200))
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (52, 60, 82, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (62, 72, 98, 255))
            
            # Ultra-smooth rounded corners and perfect spacing
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 24, 20)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 18, 14)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 10, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 16, 14)
            dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 10, 8)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 24)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 14)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 18)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 18)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 14)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 12)

        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, PANEL_BG)
            dpg.add_theme_color(dpg.mvThemeCol_Border, GLASS_BORDER)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 16, 12)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 12, 8)

        with dpg.theme_component(dpg.mvInputText):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, CARD_BG)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (45, 50, 70, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (55, 60, 80, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT_PRIMARY)
            dpg.add_theme_color(dpg.mvThemeCol_Border, GLASS_BORDER)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1.5)

        with dpg.theme_component(dpg.mvButton, enabled_state=True):
            dpg.add_theme_color(dpg.mvThemeCol_Border, GLASS_BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_Button, ACCENT_COLOR)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, ACCENT_LIGHT)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, ACCENT_DARK)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 2.5)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 14)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 18, 14)

        with dpg.theme_component(dpg.mvButton, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Border, (60, 70, 90, 140))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 45, 60, 200))
            dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT_SUBTLE)

    dpg.bind_theme(global_theme)





def create_button_theme(base_color, hover_color, active_color, text_color=TEXT_PRIMARY):
    """Create an ultra-smooth glassmorphism button theme."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, base_color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover_color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color)
            dpg.add_theme_color(dpg.mvThemeCol_Text, text_color)
            dpg.add_theme_color(dpg.mvThemeCol_Border, GLASS_BORDER)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 20, 16)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 14, 10)
            dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 10, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 16)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 2.5)
    return theme





def format_hotkey_label(keys):

    if not keys:

        return "Select hotkey"

    return "+".join(sorted(keys))





def format_selection_label(value):

    return f"{value}"





def add_section_header(label, description=None):
    """Modern section header with neon accent."""
    header_id = dpg.add_text(label, color=SECONDARY_ACCENT)
    if FONTS.get("header"):
        dpg.bind_item_font(header_id, FONTS["header"])
    if description:
        subtitle_id = dpg.add_text(description, color=TEXT_SUBTLE)
        if FONTS.get("primary"):
            dpg.bind_item_font(subtitle_id, FONTS["primary"])
    dpg.add_spacer(height=8)
    dpg.add_separator()
    dpg.add_spacer(height=14)





def add_config_buttons():
    add_section_header("Configuration", "Manage stored profiles and quick saves.")
    
    save_theme = create_button_theme(ACCENT_COLOR, ACCENT_LIGHT, ACCENT_DARK, TEXT_PRIMARY)
    load_theme = create_button_theme(SECONDARY_ACCENT, PURPLE_ACCENT, (140, 60, 255, 255), TEXT_PRIMARY)
    
    with dpg.group(horizontal=True, horizontal_spacing=12):
        dpg.add_button(
            label="Save Settings",
            width=180,
            height=50,
            callback=manual_save_callback,
            tag="save_config_btn",
        )
        dpg.bind_item_theme("save_config_btn", save_theme)
        if FONTS.get("button"):
            dpg.bind_item_font("save_config_btn", FONTS["button"])
            
        dpg.add_button(
            label="Load Settings",
            width=180,
            height=50,
            callback=manual_load_callback,
            tag="load_config_btn",
        )
        dpg.bind_item_theme("load_config_btn", load_theme)
        if FONTS.get("button"):
            dpg.bind_item_font("load_config_btn", FONTS["button"])
    
    dpg.add_text("Auto-saves after every change.", color=TEXT_MUTED, tag="autosave_status")
    dpg.add_spacer(height=14)





def add_merge_count_selector():

    dpg.add_text("Merge Count", color=TEXT_PRIMARY)

    dpg.add_radio_button(

        items=[3, 5, 10],

        tag="merge_count",

        default_value=merge_count,

        horizontal=True,

        callback=update_merge_count,

    )

    dpg.add_spacer(height=16)





def add_hotkey_selectors():

    add_hotkey_selector("Start hotkey", "hotkey_display", record_hotkey, hotkey)

    add_hotkey_selector("Pause hotkey", "stop_hotkey_display", record_stop_hotkey, stop_hotkey)





def add_hotkey_selector(label, tag, callback, keys):

    dpg.add_text(label, color=TEXT_PRIMARY)

    with dpg.group(horizontal=True, horizontal_spacing=8):

        dpg.add_button(label=format_hotkey_label(keys), tag=tag, width=140, callback=callback)

        dpg.add_text("Click to record new combination.", color=TEXT_MUTED)

    dpg.add_spacer(height=14)





def add_screen_area_selector():

    dpg.add_text("Screen capture area", color=TEXT_PRIMARY)

    with dpg.group(horizontal=True, horizontal_spacing=8):

        dpg.add_button(label="Select area", tag="area_info", width=140, callback=select_area_callback)

        dpg.add_text("Define the Farm Merge Valley region.", color=TEXT_MUTED)

    dpg.add_spacer(height=14)





def add_merging_slots_selector():

    dpg.add_text("Merge slots", color=TEXT_PRIMARY)

    with dpg.group(horizontal=True, horizontal_spacing=8):

        dpg.add_button(

            label="Select points",

            tag="merging_points",

            width=140,

            callback=select_merging_points_callback,

        )

        dpg.add_text("Record target drop positions.", color=TEXT_MUTED)

    dpg.add_spacer(height=14)





def add_zoom_level_selector():

    dpg.add_text("Image scale override", color=TEXT_PRIMARY)

    with dpg.group(horizontal=True, horizontal_spacing=8):

        dpg.add_input_text(

            tag="resize_factor",

            default_value=str(resize_factor),

            width=100,

            callback=input_resize_factor_callback,

        )

        dpg.add_button(

            label="Auto calculate",

            width=130,

            tag="calculate_resize_factor_button",

            callback=calculate_resize_factor_callback,

        )

    dpg.add_text("Match the in-game zoom level.", color=TEXT_MUTED)

    dpg.add_spacer(height=14)





def add_drag_speed_selector():

    dpg.add_text("Drag duration (seconds)", color=TEXT_PRIMARY)

    dpg.add_input_float(

        tag="drag_duration",

        default_value=drag_duration_seconds,

        min_value=0.05,

        max_value=2.0,

        format="%.2f",

        width=100,

        callback=input_drag_duration_callback,

    )

    dpg.add_spacer(height=14)





def add_box_button_selector():

    dpg.add_text("Box button position", color=TEXT_PRIMARY)

    with dpg.group(horizontal=True, horizontal_spacing=8):

        dpg.add_button(

            label="Select button",

            tag="box_button_info",

            width=140,

            callback=select_box_button_callback,

        )

        dpg.add_text("Used when requesting new boxes.", color=TEXT_MUTED)

    dpg.add_spacer(height=14)





def add_box_amount_input():
    dpg.add_text("Available boxes", color=TEXT_PRIMARY)
    with dpg.group(horizontal=True, horizontal_spacing=12):
        dpg.add_input_int(
            tag="box_amount_input",
            default_value=box_amount,
            min_value=0,
            width=100,
            callback=input_box_amount_callback,
        )
        with dpg.group(horizontal=False):
            dpg.add_text("Boxes Remaining:", color=TEXT_MUTED)
            box_display = dpg.add_text(str(box_amount), color=SUCCESS_COLOR, tag="box_count_display")
            if FONTS.get("header"):
                dpg.bind_item_font(box_display, FONTS["header"])
            dpg.add_text("", tag="box_status_text", color=TEXT_SUBTLE)

    with dpg.group(horizontal=True, horizontal_spacing=12):
        dpg.add_button(
            label="Select counter area",
            tag="box_counter_region_button",
            width=180,
            callback=select_box_counter_region_callback,
        )
        dpg.add_button(
            label="Clear counter area",
            tag="box_counter_clear_button",
            width=150,
            callback=clear_box_counter_region_callback,
        )

    dpg.add_text("", tag="box_counter_mode", color=TEXT_SUBTLE)
    dpg.add_spacer(height=6)

    dpg.add_text("System works with any box count (0+). Uses 1-5 boxes per click when available.", color=TEXT_SUBTLE)
    dpg.add_spacer(height=14)

    update_box_amount_ui(box_amount)
    refresh_box_counter_controls()






def add_advanced_features_panel():

    add_section_header("Advanced", "Auto-sort and board management")

    with dpg.collapsing_header(label="Auto Sort Planner", tag="auto_sort_header", default_open=False):

        # Step 1: Grid Configuration
        dpg.add_text("Step 1: Configure Grid", color=ACCENT_LIGHT)
        dpg.add_checkbox(
            label="Auto-discover grid",
            tag="auto_board_detection_checkbox",
            default_value=auto_board_detection_enabled,
            callback=toggle_auto_board_detection_callback,
        )
        dpg.add_text("", tag="board_detection_status", color=TEXT_MUTED)
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True, horizontal_spacing=12):
            dpg.add_input_int(
                label="Rows",
                tag="board_rows_input",
                default_value=board_rows,
                min_value=1,
                max_value=20,
                callback=update_board_rows_callback,
                width=100,
            )
            dpg.add_input_int(
                label="Cols",
                tag="board_cols_input",
                default_value=board_cols,
                min_value=1,
                max_value=20,
                callback=update_board_cols_callback,
                width=100,
            )
        dpg.add_spacer(height=10)

        # Step 2: Detection Methods
        dpg.add_text("Step 2: Detect Slots", color=ACCENT_LIGHT)
        scan_theme = create_button_theme(
            SECONDARY_ACCENT,
            (0, 210, 190, 235),
            (0, 158, 140, 235),
            TEXT_PRIMARY,
        )
        manual_theme = create_button_theme(
            (180, 120, 255, 235),
            (200, 150, 255, 235),
            (160, 100, 235, 235),
            TEXT_PRIMARY,
        )
        
        with dpg.group(horizontal=True, horizontal_spacing=12):
            dpg.add_button(
                label="Auto Scan",
                tag="scan_board_button",
                width=180,
                height=48,
                callback=scan_board_button_callback,
            )
            dpg.bind_item_theme("scan_board_button", scan_theme)
            if FONTS.get("button"):
                dpg.bind_item_font("scan_board_button", FONTS["button"])
            
            dpg.add_button(
                label="Manual Select",
                tag="manual_select_slots_button",
                width=180,
                height=48,
                callback=manual_select_slots_callback,
            )
            dpg.bind_item_theme("manual_select_slots_button", manual_theme)
            if FONTS.get("button"):
                dpg.bind_item_font("manual_select_slots_button", FONTS["button"])
        
        dpg.add_text("Auto: Detects items automatically  |  Manual: Click each slot yourself", 
                    color=TEXT_SUBTLE, wrap=380)
        dpg.add_spacer(height=12)

        # Step 3: Review & Configure
        dpg.add_text("Step 3: Review Detected Slots", color=ACCENT_LIGHT)
        dpg.add_text(tag="slot_count_summary", default_value="No slots detected yet", color=TEXT_MUTED)
        dpg.add_spacer(height=6)
        
        with dpg.table(
            header_row=True,
            row_background=True,
            borders_innerH=True,
            borders_innerV=True,
            borders_outerH=True,
            borders_outerV=True,
            policy=dpg.mvTable_SizingStretchProp,
            tag="slot_table",
            scrollY=True,
            height=200,
        ):
            dpg.add_table_column(label="Slot", width_fixed=True, init_width_or_weight=50)
            dpg.add_table_column(label="Item", width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column(label="Status", width_fixed=True, init_width_or_weight=70)
            dpg.add_table_column(label="Actions")
        refresh_board_slot_table()

        dpg.add_spacer(height=12)

        # Step 4: Generate & Run Sort Plan
        dpg.add_text("Step 4: Auto Sort", color=ACCENT_LIGHT)

        plan_generate_theme = create_button_theme(
            ACCENT_COLOR,
            ACCENT_LIGHT,
            ACCENT_DARK,
            TEXT_PRIMARY,
        )
        plan_run_theme = create_button_theme(
            (80, 110, 255, 235),
            (100, 130, 255, 235),
            (60, 90, 220, 235),
            TEXT_PRIMARY,
        )
        
        with dpg.group(horizontal=True, horizontal_spacing=12):
            dpg.add_button(
                label="Generate Plan",
                tag="generate_sort_plan_button",
                width=180,
                height=48,
                callback=generate_sort_plan_callback,
            )
            dpg.bind_item_theme("generate_sort_plan_button", plan_generate_theme)
            if FONTS.get("button"):
                dpg.bind_item_font("generate_sort_plan_button", FONTS["button"])
            
            dpg.add_button(
                label="Execute Sort",
                tag="run_sort_plan_button",
                width=180,
                height=48,
                callback=run_sort_plan_callback,
            )
            dpg.bind_item_theme("run_sort_plan_button", plan_run_theme)
            if FONTS.get("button"):
                dpg.bind_item_font("run_sort_plan_button", FONTS["button"])
            dpg.disable_item("run_sort_plan_button")
        
        dpg.add_text("Generate: Creates sorting plan  |  Execute: Runs the automated sorting", 
                    color=TEXT_SUBTLE, wrap=380)
        dpg.add_spacer(height=8)
        
        dpg.add_text(tag="plan_summary", default_value="No plan generated", color=TEXT_MUTED)
        with dpg.table(
            header_row=True,
            row_background=True,
            borders_innerH=True,
            borders_innerV=True,
            borders_outerH=True,
            borders_outerV=True,
            policy=dpg.mvTable_SizingStretchProp,
            tag="plan_table",
            scrollY=True,
            height=150,
        ):
            dpg.add_table_column(label="#", width_fixed=True, init_width_or_weight=30)
            dpg.add_table_column(label="Item", width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column(label="From → To")
        refresh_sort_plan_table()
        update_run_sort_plan_button_state()

    dpg.add_spacer(height=14)

    refresh_board_detection_controls()





def add_advanced_shortcut_button():

    advanced_theme = create_button_theme(

        SECONDARY_ACCENT,

        (0, 210, 190, 235),

        (0, 160, 142, 235),

        TEXT_PRIMARY,

    )

    dpg.add_button(

        label="Advanced Features",

        tag="advanced_toggle_button",

        width=220,

        height=52,

        callback=toggle_advanced_features_callback,

    )

    dpg.bind_item_theme("advanced_toggle_button", advanced_theme)

    if FONTS.get("button"):

        dpg.bind_item_font("advanced_toggle_button", FONTS["button"])

    dpg.add_spacer(height=10)





def add_start_stop_buttons():
    start_theme = create_button_theme(ACCENT_COLOR, ACCENT_LIGHT, ACCENT_DARK, TEXT_PRIMARY)
    stop_theme = create_button_theme(DANGER_COLOR, (255, 130, 170, 255), (255, 80, 130, 255), TEXT_PRIMARY)
    
    with dpg.group(horizontal=True, horizontal_spacing=12):
        dpg.add_button(
            label="▶ Enable = Toggle",
            tag="start_button",
            width=220,
            height=56,
            callback=start_button_callback,
        )
        dpg.bind_item_theme("start_button", start_theme)
        if FONTS.get("button"):
            dpg.bind_item_font("start_button", FONTS["button"])
        
        dpg.add_button(
            label="⏹ Disable",
            tag="stop_button",
            width=220,
            height=56,
            callback=stop_button_callback,
            show=False,
        )
        dpg.bind_item_theme("stop_button", stop_theme)
        if FONTS.get("button"):
            dpg.bind_item_font("stop_button", FONTS["button"])
    
    dpg.add_text("Press = to instantly start/stop merge process", color=TEXT_SUBTLE)
    dpg.add_spacer(height=10)





def add_quick_start_tab():
    """TAB 1: Quick Start - Everything you need to get started"""
    
    with dpg.group(horizontal=True, horizontal_spacing=20):
        # LEFT: Essential Setup
        with dpg.child_window(width=580, height=640):
            add_section_header("Essential Setup", "Get started in 3 steps")
            
            # Step 1: Controls
            dpg.add_text("STEP 1: Start/Stop Control", color=ACCENT_COLOR)
            if FONTS.get("header"):
                dpg.bind_item_font(dpg.last_item(), FONTS["header"])
            dpg.add_spacer(height=8)
            add_start_stop_buttons()
            dpg.add_spacer(height=16)
            dpg.add_separator()
            dpg.add_spacer(height=16)
            
            # Step 2: Basic Settings
            dpg.add_text("STEP 2: Configure Basics", color=ACCENT_COLOR)
            if FONTS.get("header"):
                dpg.bind_item_font(dpg.last_item(), FONTS["header"])
            dpg.add_spacer(height=8)
            add_merge_count_selector()
            add_screen_area_selector()
            add_merging_slots_selector()
            dpg.add_spacer(height=16)
            dpg.add_separator()
            dpg.add_spacer(height=16)
            
            # Step 3: Hotkeys
            dpg.add_text("STEP 3: Set Hotkeys", color=ACCENT_COLOR)
            if FONTS.get("header"):
                dpg.bind_item_font(dpg.last_item(), FONTS["header"])
            dpg.add_spacer(height=8)
            add_hotkey_selectors()
        
        # RIGHT: Quick Actions & Status
        with dpg.child_window(width=580, height=640):
            add_section_header("Quick Actions", "Common tasks")
            
            # Quick scan button
            scan_theme = create_button_theme(SECONDARY_ACCENT, PURPLE_ACCENT, (140, 60, 255, 255), TEXT_PRIMARY)
            dpg.add_button(
                label="🔄 Scan for Items Now",
                width=-1,
                height=60,
                callback=scan_and_preview_callback,
                tag="quick_scan_button"
            )
            dpg.bind_item_theme("quick_scan_button", scan_theme)
            if FONTS.get("button"):
                dpg.bind_item_font("quick_scan_button", FONTS["button"])
            
            dpg.add_spacer(height=16)
            
            # Stats cards
            with dpg.group(horizontal=True, horizontal_spacing=12):
                with dpg.child_window(width=280, height=120, border=True):
                    dpg.add_spacer(height=10)
                    dpg.add_text("Total Detected", color=TEXT_MUTED)
                    dpg.add_spacer(height=8)
                    total_text = dpg.add_text("0", color=ACCENT_COLOR, tag="quick_total_count")
                    if FONTS.get("hero"):
                        dpg.bind_item_font(total_text, FONTS["hero"])
                
                with dpg.child_window(width=280, height=120, border=True):
                    dpg.add_spacer(height=10)
                    dpg.add_text("Unique Types", color=TEXT_MUTED)
                    dpg.add_spacer(height=8)
                    types_text = dpg.add_text("0", color=SECONDARY_ACCENT, tag="quick_types_count")
                    if FONTS.get("hero"):
                        dpg.bind_item_font(types_text, FONTS["hero"])
            
            dpg.add_spacer(height=16)
            dpg.add_separator()
            dpg.add_spacer(height=16)
            
            # Activity preview
            dpg.add_text("Recent Activity", color=TEXT_PRIMARY)
            if FONTS.get("header"):
                dpg.bind_item_font(dpg.last_item(), FONTS["header"])
            dpg.add_spacer(height=8)
            
            dpg.add_input_text(
                tag="quick_log_output",
                multiline=True,
                readonly=True,
                height=340,
                width=-1,
                default_value=APP_READY_MESSAGE,
            )


def add_detection_tab():
    """TAB 2: Detection Preview - Visual feedback"""
    
    with dpg.group(horizontal=False):
        # Controls
        with dpg.group(horizontal=True, horizontal_spacing=16):
            scan_btn = dpg.add_button(
                label="🔄 Scan Now",
                width=200,
                height=50,
                callback=scan_and_preview_callback,
                tag="scan_preview_button"
            )
            
            dpg.add_checkbox(
                label="Auto-refresh (3s)",
                tag="auto_refresh_preview",
                default_value=False,
                callback=toggle_auto_refresh_callback
            )
            
            dpg.add_spacer(width=200)
            
            # Stats inline
            dpg.add_text("Total:", color=TEXT_MUTED)
            dpg.add_text("0", color=ACCENT_COLOR, tag="preview_total_count")
            dpg.add_text("•", color=TEXT_SUBTLE)
            dpg.add_text("Types:", color=TEXT_MUTED)
            dpg.add_text("0", color=SECONDARY_ACCENT, tag="preview_types_count")
            dpg.add_text("•", color=TEXT_SUBTLE)
            dpg.add_text("Last:", color=TEXT_MUTED)
            dpg.add_text("Not scanned", color=TEXT_SUBTLE, tag="preview_last_scan")
        
        dpg.add_spacer(height=16)
        dpg.add_separator()
        dpg.add_spacer(height=16)
        
        # Detection Grid - No scroll, clean layout
        with dpg.child_window(height=600):
            with dpg.group(tag="detection_items_container"):
                dpg.add_text("Click 'Scan Now' to detect items", color=TEXT_SUBTLE)


def add_settings_tab():
    """TAB 3: All Settings - Everything organized"""
    
    with dpg.group(horizontal=True, horizontal_spacing=20):
        # LEFT: Core Settings
        with dpg.child_window(width=580, height=640):
            add_section_header("Core Settings", "Fine-tune automation")
            
            add_zoom_level_selector()
            add_drag_speed_selector()
            add_box_button_selector()
            add_box_amount_input()
            
            dpg.add_spacer(height=16)
            dpg.add_separator()
            dpg.add_spacer(height=16)
            
            # Quick Collection Tools
            dpg.add_text("Quick Collection", color=SECONDARY_ACCENT)
            if FONTS.get("header"):
                dpg.bind_item_font(dpg.last_item(), FONTS["header"])
            dpg.add_spacer(height=4)
            dpg.add_text("One-click template capture tools", color=TEXT_SUBTLE)
            dpg.add_spacer(height=10)
            
            with dpg.group(horizontal=True, horizontal_spacing=12):
                dpg.add_button(
                    label="Collect",
                    width=180,
                    height=50,
                    callback=lambda: launch_template_collector("items", 50)
                )
                dpg.add_button(
                    label="Game UI",
                    width=180,
                    height=50,
                    callback=lambda: launch_template_collector("ui_elements", 60)
                )
                dpg.add_button(
                    label="Cut Items",
                    width=180,
                    height=50,
                    callback=lambda: launch_template_collector("producers", 50)
                )
        
        # RIGHT: Advanced Features
        with dpg.child_window(width=580, height=640):
            add_section_header("Advanced", "Auto-sort and more")
            add_advanced_features_panel()
            
            dpg.add_spacer(height=16)
            dpg.add_separator()
            dpg.add_spacer(height=16)
            
            # Config management
            add_config_buttons()


def add_activity_tab():
    """TAB 4: Full Activity Log"""
    
    with dpg.child_window(height=640):
        add_section_header("Activity Log", "Full automation history")
        
        dpg.add_input_text(
            tag="log_output",
            multiline=True,
            readonly=True,
            height=580,
            width=-1,
            default_value=APP_READY_MESSAGE,
        )





def create_gui():

    dpg.create_context()

    load_fonts()

    setup_app_theme()



    with dpg.window(

        label=APP_NAME,

        tag="primary_window",

        no_title_bar=True,

        no_move=True,

        no_resize=True,

    ):

        # Top Header Bar with gradient
        with dpg.child_window(height=90, border=False):
            dpg.add_spacer(height=8)
            title_id = dpg.add_text(APP_NAME, color=SECONDARY_ACCENT)
            if FONTS.get("hero"):
                dpg.bind_item_font(title_id, FONTS["hero"])
            
            subtitle_id = dpg.add_text(APP_SUBTITLE, color=TEXT_MUTED)
            if FONTS.get("header"):
                dpg.bind_item_font(subtitle_id, FONTS["header"])
            
            dpg.add_spacer(height=4)



        dpg.add_separator()
        dpg.add_spacer(height=8)
        
        # Status Bar
        with dpg.group(horizontal=True, horizontal_spacing=30):
            dpg.add_text("Status:", color=TEXT_PRIMARY)
            dpg.add_text("Ready", color=SUCCESS_COLOR, tag="status_indicator")
            dpg.add_text("•", color=TEXT_SUBTLE)
            dpg.add_text("Boxes:", color=TEXT_PRIMARY)
            dpg.add_text(str(box_amount), color=ACCENT_COLOR, tag="header_box_count")
            dpg.add_text("•", color=TEXT_SUBTLE)
            dpg.add_text("Detected:", color=TEXT_PRIMARY)
            dpg.add_text("0 items", color=TEXT_MUTED, tag="header_detected_count")
        
        dpg.add_spacer(height=8)
        dpg.add_separator()
        dpg.add_spacer(height=8)

        # Tab Bar for main navigation
        with dpg.tab_bar(tag="main_tabs"):
            
            # TAB 1: Quick Setup
            with dpg.tab(label="Quick Start", tag="tab_quick"):
                add_quick_start_tab()
            
            # TAB 2: Detection Preview
            with dpg.tab(label="Detection", tag="tab_detection"):
                add_detection_tab()
            
            # TAB 3: Advanced Settings
            with dpg.tab(label="Settings", tag="tab_settings"):
                add_settings_tab()
            
            # TAB 4: Activity Log
            with dpg.tab(label="Activity", tag="tab_activity"):
                add_activity_tab()



        dpg.add_spacer(height=8)

        dpg.add_text(

            "Press = key to start/stop instantly",

            color=TEXT_SUBTLE,

            wrap=1200,

        )



    load_config()

    setup_viewport()





def setup_viewport():

    dpg.create_viewport(

        title=APP_NAME,

        width=1250,

        height=850,

        resizable=True,

        min_width=1200,

        min_height=800,

    )

    dpg.setup_dearpygui()

    dpg.show_viewport()

    dpg.set_primary_window("primary_window", True)

    dpg.start_dearpygui()

    dpg.destroy_context()





def get_image_file_paths(folder):

    image_files = [

        os.path.join(folder, name)

        for name in os.listdir(folder)

        if name.endswith((".png", ".jpg", ".jpeg"))

    ]

    return sorted(image_files, reverse=True)



def detect_board_layout(area_rect, rows, cols, resize):
    global board_rows, board_cols, last_detected_grid_summary, last_detected_grid_color

    if len(area_rect) != 4:
        update_board_detection_status("Set the screen area before scanning the board.", WARNING_COLOR)
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
            start_x,
            start_y,
            end_x,
            end_y,
            resize,
        )
        template_points[template_name] = points
        aggregated_points.extend(points)

    detection_summary = ""
    detection_color = TEXT_MUTED
    detection_updated = False

    if auto_board_detection_enabled:
        geometry = auto_detect_board_geometry(area_rect, aggregated_points)
        if geometry:
            rows = geometry["rows"]
            cols = geometry["cols"]
            detection_summary = f"Auto detected {rows}x{cols} grid ({len(aggregated_points)} matches)"
            detection_color = SUCCESS_COLOR
            if board_rows != rows or board_cols != cols:
                board_rows = rows
                board_cols = cols
                detection_updated = True
        else:
            detection_summary = "Auto detection failed - using manual grid."
            detection_color = WARNING_COLOR
    else:
        detection_summary = f"Manual grid: {rows}x{cols}"
        detection_color = TEXT_MUTED

    rows = int(rows)
    cols = int(cols)

    if rows <= 0 or cols <= 0:
        update_board_detection_status(
            "Unable to determine grid. Toggle auto-detect or set manual values.",
            WARNING_COLOR,
        )
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

    update_board_detection_status(detection_summary, detection_color)
    refresh_board_detection_controls()

    if detection_updated:
        save_config()

    return [
        {
            **slot,
            "allowed": slot["id"] not in disallowed_slots,
        }
        for slot in slot_map.values()
    ]





def auto_detect_board_geometry(area_rect, detection_points):
    if len(area_rect) != 4 or not detection_points or len(detection_points) < 4:
        return None

    start_x, start_y, end_x, end_y = area_rect
    width = max(1, end_x - start_x)
    height = max(1, end_y - start_y)

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



def update_board_detection_status(summary, color=None):
    global last_detected_grid_summary, last_detected_grid_color

    if summary is None:
        summary = ""

    last_detected_grid_summary = summary
    if color is not None:
        last_detected_grid_color = color

    if dpg.does_item_exist("board_detection_status"):
        dpg.set_value("board_detection_status", last_detected_grid_summary)
        dpg.configure_item("board_detection_status", color=last_detected_grid_color)



def refresh_board_detection_controls():
    summary = last_detected_grid_summary
    color = last_detected_grid_color

    if dpg.does_item_exist("auto_board_detection_checkbox"):
        dpg.set_value("auto_board_detection_checkbox", auto_board_detection_enabled)

    if dpg.does_item_exist("board_rows_input"):
        dpg.set_value("board_rows_input", board_rows)
        if auto_board_detection_enabled:
            dpg.disable_item("board_rows_input")
        else:
            dpg.enable_item("board_rows_input")

    if dpg.does_item_exist("board_cols_input"):
        dpg.set_value("board_cols_input", board_cols)
        if auto_board_detection_enabled:
            dpg.disable_item("board_cols_input")
        else:
            dpg.enable_item("board_cols_input")

    if not summary:
        if auto_board_detection_enabled:
            summary = "Auto detection pending. Run Auto Scan to capture grid."
            color = TEXT_MUTED
        else:
            summary = f"Manual grid: {board_rows}x{board_cols}"
            color = TEXT_MUTED

    update_board_detection_status(summary, color)



def select_box_counter_region_callback():
    global box_counter_region, box_counter_last_value, box_counter_failure_logged

    if dpg.does_item_exist("box_counter_region_button"):
        dpg.set_item_label("box_counter_region_button", "Selecting...")

    selector = ScreenAreaSelector()
    coordinates = selector.get_coordinates()

    if not coordinates or len(coordinates) != 4:
        log_message("[warn] Counter selection cancelled.")
        refresh_box_counter_controls()
        return

    start_x, start_y, end_x, end_y = coordinates
    x = int(min(start_x, end_x))
    y = int(min(start_y, end_y))
    width = int(max(1, abs(end_x - start_x)))
    height = int(max(1, abs(end_y - start_y)))

    box_counter_region = (x, y, width, height)
    box_counter_last_value = None
    box_counter_failure_logged = False

    log_message(f"[info] Box counter region captured at {box_counter_region}.")

    refresh_box_counter_controls()
    maybe_update_box_count_from_ocr(force=True)
    save_config()



def clear_box_counter_region_callback():
    global box_counter_region, box_counter_last_value, box_counter_failure_logged

    if not box_counter_region:
        log_message("[info] Box counter region already cleared.")
    else:
        box_counter_region = tuple()
        box_counter_last_value = None
        box_counter_failure_logged = False
        log_message("[info] Box counter region cleared. Manual entry enabled.")

    refresh_box_counter_controls()
    update_box_amount_ui(box_amount)
    save_config()



def is_tesseract_ready(force=False):
    global tesseract_status

    now = time.time()
    cached = tesseract_status.get("available")
    if not force and cached is not None and now - tesseract_status.get("checked_at", 0.0) < 30.0:
        return tesseract_status["available"], tesseract_status.get("message", "")

    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        available = True
        message = ""
    except ImportError:
        available = False
        message = "Install pytesseract (pip install pytesseract)."
    except pytesseract.pytesseract.TesseractNotFoundError:
        available = False
        message = "Install Tesseract OCR and ensure it is on PATH."

    tesseract_status["available"] = available
    tesseract_status["message"] = message
    tesseract_status["checked_at"] = now
    return available, message



def read_box_count_from_region(region):
    global tesseract_status
    if not region or len(region) != 4:
        return None

    available, _ = is_tesseract_ready()
    if not available:
        return None

    x, y, width, height = region
    if width <= 0 or height <= 0:
        return None

    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    frame = cv2.resize(frame, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    frame = cv2.GaussianBlur(frame, (3, 3), 0)
    _, thresh = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    try:
        import pytesseract
        text = pytesseract.image_to_string(thresh, config="--psm 7 digits")
    except pytesseract.pytesseract.TesseractNotFoundError:
        tesseract_status["available"] = False
        tesseract_status["message"] = "Install Tesseract OCR and ensure it is on PATH."
        tesseract_status["checked_at"] = time.time()
        return None

    digits = re.findall(r"\d+", text)
    if digits:
        try:
            return int(digits[0])
        except ValueError:
            return None
    return None


def update_box_amount_ui(value, source="manual"):
    global box_amount

    try:
        int_value = int(value)
    except (TypeError, ValueError):
        int_value = 0

    box_amount = max(0, int_value)

    if dpg.does_item_exist("box_amount_input"):
        dpg.set_value("box_amount_input", box_amount)

    if dpg.does_item_exist("box_count_display"):
        dpg.set_value("box_count_display", str(box_amount))
        if box_amount == 0:
            dpg.configure_item("box_count_display", color=DANGER_COLOR)
        elif box_amount <= 3:
            dpg.configure_item("box_count_display", color=WARNING_COLOR)
        else:
            dpg.configure_item("box_count_display", color=SUCCESS_COLOR)

    if dpg.does_item_exist("box_status_text"):
        if box_amount == 0:
            status_color = DANGER_COLOR
            base_message = "No boxes - will continue without clicking"
        elif box_amount <= 3:
            status_color = WARNING_COLOR
            base_message = "Low boxes - will use all available"
        else:
            status_color = SUCCESS_COLOR
            base_message = "Ready - will use 1-5 per cycle"

        if source == "ocr":
            base_message = f"OCR detected {box_amount} box(es)"
            if box_amount > 0:
                status_color = SECONDARY_ACCENT

        dpg.set_value("box_status_text", base_message)
        dpg.configure_item("box_status_text", color=status_color)



def refresh_box_counter_controls():
    global box_counter_refresh_active

    if box_counter_refresh_active:
        return

    box_counter_refresh_active = True
    try:
        has_region = isinstance(box_counter_region, (tuple, list)) and len(box_counter_region) == 4
        available, message = is_tesseract_ready() if has_region else (False, "")

        if dpg.does_item_exist("box_counter_region_button"):
            dpg.set_item_label(
                "box_counter_region_button",
                "Re-select counter area" if has_region else "Select counter area",
            )

        if dpg.does_item_exist("box_counter_mode"):
            if has_region and available:
                dpg.set_value("box_counter_mode", "OCR active - value syncs automatically")
                dpg.configure_item("box_counter_mode", color=SECONDARY_ACCENT)
            elif has_region and not available:
                warning_text = message or "OCR unavailable - install Tesseract OCR."
                dpg.set_value("box_counter_mode", warning_text)
                dpg.configure_item("box_counter_mode", color=WARNING_COLOR)
            else:
                dpg.set_value("box_counter_mode", "Manual entry - set boxes or capture OCR region.")
                dpg.configure_item("box_counter_mode", color=TEXT_MUTED)

        if dpg.does_item_exist("box_amount_input"):
            if has_region and available:
                dpg.disable_item("box_amount_input")
            else:
                dpg.enable_item("box_amount_input")
    finally:
        box_counter_refresh_active = False



def maybe_update_box_count_from_ocr(force=False):
    global last_box_counter_read_time, box_counter_last_value, box_counter_failure_logged

    has_region = isinstance(box_counter_region, (tuple, list)) and len(box_counter_region) == 4
    if not has_region:
        return None

    available, message = is_tesseract_ready()
    if not available:
        if message and not box_counter_failure_logged:
            log_message(f"[warn] {message}")
            box_counter_failure_logged = True
        refresh_box_counter_controls()
        return None

    now = time.time()
    if not force and now - last_box_counter_read_time < 1.0:
        return box_counter_last_value

    value = read_box_count_from_region(box_counter_region)
    last_box_counter_read_time = now

    if value is None:
        if not box_counter_failure_logged:
            log_message("[warn] Unable to read box counter from screen. Verify region and contrast.")
            box_counter_failure_logged = True
        return None

    box_counter_failure_logged = False
    box_counter_last_value = value
    update_box_amount_ui(value, source="ocr")
    refresh_box_counter_controls()
    return value
def start_merge(

    log_queue,

    area_rect,

    scale,

    count,

    points,

    cancel_keys,

    box_point,

    drag_duration,

    stop_signal,

    initial_box_amount,

):

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
    
    # Self-healing: track consecutive failed cycles
    consecutive_failures = 0
    max_failures_before_rescan = 2
    
    while not stop_flag["active"] and (stop_signal is None or not stop_signal.is_set()):
        merge_success = perform_merge_cycle(image_files, area_rect, scale, count, points, queue_log, drag_duration)
        
        if merge_success:
            consecutive_failures = 0  # Reset failure counter on success
            continue
        else:
            consecutive_failures += 1
            
            # Self-healing: rescan board after consecutive failures
            if consecutive_failures >= max_failures_before_rescan:
                queue_log("[info] 🔄 Self-healing: Rescanning board after failed cycles...")
                time.sleep(1.0)  # Brief pause before rescan
                consecutive_failures = 0  # Reset counter after rescan
                
                # Try one more cycle after rescan
                if perform_merge_cycle(image_files, area_rect, scale, count, points, queue_log, drag_duration):
                    continue
        
        if local_box_amount <= 0:
            queue_log("[info] No boxes available. Continuing without box clicks...")
            time.sleep(2.0)  # Wait 2 seconds before checking again
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





def validate_merge_parameters(area_rect, scale, count, points):

    if len(area_rect) != 4:

        log_message("[error] ❌ Screen area not configured.")

        return False

    if scale <= 0:

        log_message("[error] ❌ Resize factor must be greater than zero.")

        return False

    if len(points) < count - 1:

        log_message(f"[error] ❌ Not enough merge points. Expected {count - 1}, received {len(points)}.")

        return False

    if not os.path.exists("./img"):

        log_message("[error] ❌ img folder not found. Please ensure image files are present.")

        return False

    if not any(f.endswith(('.png', '.jpg', '.jpeg')) for f in os.listdir("./img")):

        log_message("[error] ❌ No image files found in img folder.")

        return False

    return True





def perform_merge_cycle(image_files, area_rect, scale, count, points, queue_log, drag_duration):
    """
    Enhanced merge cycle with priority-based merging.
    
    Prioritizes producer items (animals, crops) for resource generation,
    then merges other items based on availability.
    """
    # Categorize templates by priority
    producer_templates = []
    regular_templates = []
    
    for target_image in image_files:
        basename = os.path.basename(target_image).lower()
        # Identify producer items (customize based on your templates)
        if any(keyword in basename for keyword in ['chicken', 'cow', 'sheep', 'wheat', 'corn', 'producer']):
            producer_templates.append(target_image)
        else:
            regular_templates.append(target_image)
    
    # Try producer templates first (higher priority)
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





def perform_merge_operations(template_centers, points, count, queue_log, drag_duration):
    for idx in range(count):
        start_x, start_y = template_centers[idx]
        end_x, end_y = points[idx % (count - 1)]
        
        pyautogui.mouseUp()
        pyautogui.moveTo(start_x, start_y)
        pyautogui.mouseDown()
        pyautogui.moveTo(end_x, end_y, duration=drag_duration)
        pyautogui.mouseUp()
        time.sleep(0.05)  # Reduced delay for faster execution





def perform_box_clicks_at_point(point, queue_log, num_clicks=5):
    if not point or len(point) != 2:
        queue_log("[error] Box button point not configured.")
        return

    x, y = point
    num_clicks = max(1, min(num_clicks, 5))
    interval = 0.3  # Fixed fast interval for production
    
    for _ in range(num_clicks):
        pyautogui.moveTo(x, y, duration=0.05)  # Faster movement
        pyautogui.click()
        time.sleep(interval)





def input_resize_factor_callback(sender, app_data, user_data):

    global resize_factor

    if app_data == "":

        return

    try:

        value = float(app_data)

        if value <= 0:

            log_message("[error] Resize factor must be positive.")

            return

    except ValueError:

        log_message("[error] Invalid resize factor entered.")

        return

    resize_factor = value

    save_config()





def input_box_amount_callback(sender, app_data, user_data):

    try:

        value = int(app_data)

    except (TypeError, ValueError):

        return

    if value < 0:

        return

    update_box_amount_ui(value, source="manual")
    refresh_box_counter_controls()
    save_config()





def input_drag_duration_callback(sender, app_data, user_data):

    global drag_duration_seconds

    try:

        value = float(app_data)

    except (TypeError, ValueError):

        return

    if value <= 0:

        return

    drag_duration_seconds = value

    save_config()





def update_merge_count(sender, app_data, user_data):

    global merge_count, merging_points

    merge_count = int(app_data)

    if merge_count - 1 > len(merging_points):

        merging_points = []

        if dpg.does_item_exist("merging_points"):

            dpg.set_item_label("merging_points", "Select points")

    save_config()





def log_message(message):

    if not dpg.does_item_exist("log_output"):

        return

    current = dpg.get_value("log_output")

    dpg.set_value("log_output", f"{message}\n{current}")





def apply_slot_overrides():

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





def refresh_board_slot_table():
    if not dpg.does_item_exist("slot_table"):
        return
    
    existing_rows = dpg.get_item_children("slot_table", 1) or []
    for row_id in existing_rows:
        dpg.delete_item(row_id)
    
    if not board_slots:
        with dpg.table_row(parent="slot_table"):
            dpg.add_text("No slots detected", color=TEXT_SUBTLE)
        if dpg.does_item_exist("slot_count_summary"):
            dpg.set_value("slot_count_summary", "No slots detected yet")
        return

    sorted_slots = sorted(board_slots, key=lambda s: (s["row"], s["col"]))
    occupied_count = sum(1 for slot in sorted_slots if slot.get("type"))
    enabled_count = sum(1 for slot in sorted_slots if slot["id"] not in disallowed_slots)
    
    if dpg.does_item_exist("slot_count_summary"):
        dpg.set_value("slot_count_summary", 
                     f"Total: {len(sorted_slots)} slots  |  Occupied: {occupied_count}  |  Enabled: {enabled_count}")
        dpg.configure_item("slot_count_summary", color=SUCCESS_COLOR if enabled_count > 0 else WARNING_COLOR)
    
    for slot in sorted_slots:
        slot_id = slot["id"]
        allowed = slot_id not in disallowed_slots
        status_icon = "OK" if allowed else "X"
        status_color = SUCCESS_COLOR if allowed else DANGER_COLOR
        item_type = slot.get("type")
        
        if item_type:
            item_display = item_type.replace(".png", "").replace("1", "★").replace("2", "★★").replace("3", "★★★")
            item_color = TEXT_PRIMARY
        else:
            item_display = "empty"
            item_color = TEXT_SUBTLE
        
        with dpg.table_row(parent="slot_table"):
            dpg.add_text(f"{slot['row']+1},{slot['col']+1}", color=TEXT_MUTED)
            dpg.add_text(item_display, color=item_color)
            dpg.add_text(status_icon, color=status_color)
            
            with dpg.group(horizontal=True, horizontal_spacing=4):
                dpg.add_button(
                    label="Reset" if allowed else "OK",
                    width=40,
                    callback=toggle_slot_allowed,
                    user_data=slot_id,
                )
                if slot_id in slot_overrides:
                    dpg.add_button(
                        label="↺",
                        width=40,
                        callback=reset_slot_position_callback,
                        user_data=slot_id,
                    )
                else:
                    dpg.add_button(
                        label="📍",
                        width=40,
                        callback=adjust_slot_position_callback,
                        user_data=slot_id,
                    )





def adjust_slot_position_callback(sender, app_data, user_data):

    global slot_overrides

    slot_id = str(user_data)

    selector = MergingPointsSelector(1)

    points = selector.get_points()

    if not points:

        return

    slot_overrides[slot_id] = tuple(points[0])

    apply_slot_overrides()

    refresh_board_slot_table()

    if dpg.does_item_exist("auto_sort_header") and dpg.get_value("auto_sort_header"):

        generate_auto_sort_plan()

    else:

        refresh_sort_plan_table()

        update_run_sort_plan_button_state()

    log_message(f"[info] Slot {slot_id} center updated.")

    save_config()





def reset_slot_position_callback(sender, app_data, user_data):

    slot_id = str(user_data)

    if slot_id in slot_overrides:

        slot_overrides.pop(slot_id, None)

        apply_slot_overrides()

        refresh_board_slot_table()

        if dpg.does_item_exist("auto_sort_header") and dpg.get_value("auto_sort_header"):

            generate_auto_sort_plan()

        else:

            refresh_sort_plan_table()

            update_run_sort_plan_button_state()

        log_message(f"[info] Slot {slot_id} center reset to default.")

        save_config()





def refresh_sort_plan_table():
    if not dpg.does_item_exist("plan_table"):
        return
    
    existing_rows = dpg.get_item_children("plan_table", 1) or []
    for row_id in existing_rows:
        dpg.delete_item(row_id)
    
    if not sort_plan:
        with dpg.table_row(parent="plan_table"):
            dpg.add_text("No plan yet", color=TEXT_SUBTLE)
        if dpg.does_item_exist("plan_summary"):
            dpg.set_value("plan_summary", "No plan generated")
            dpg.configure_item("plan_summary", color=TEXT_MUTED)
        return

    if dpg.does_item_exist("plan_summary"):
        dpg.set_value("plan_summary", f"{len(sort_plan)} moves planned - Ready to execute")
        dpg.configure_item("plan_summary", color=SUCCESS_COLOR)

    for idx, move in enumerate(sort_plan, start=1):
        item_display = move["item"].replace(".png", "").replace("1", "★").replace("2", "★★").replace("3", "★★★")
        with dpg.table_row(parent="plan_table"):
            dpg.add_text(str(idx), color=TEXT_MUTED)
            dpg.add_text(item_display, color=TEXT_PRIMARY)
            dpg.add_text(f"{move['source_slot']} → {move['target_slot']}", color=ACCENT_LIGHT)





def update_run_sort_plan_button_state():

    if not dpg.does_item_exist("run_sort_plan_button"):

        return

    if sort_plan:

        dpg.enable_item("run_sort_plan_button")

    else:

        dpg.disable_item("run_sort_plan_button")





def toggle_slot_allowed(sender, app_data, user_data):

    slot_id = str(user_data)

    if slot_id in disallowed_slots:

        disallowed_slots.remove(slot_id)

        log_message(f"[info] Slot {slot_id} enabled for sorting.")

    else:

        disallowed_slots.add(slot_id)

        log_message(f"[info] Slot {slot_id} blocked from sorting.")

    for slot in board_slots:

        if slot["id"] == slot_id:

            slot["allowed"] = slot_id not in disallowed_slots

    refresh_board_slot_table()

    if dpg.does_item_exist("auto_sort_header") and dpg.get_value("auto_sort_header"):

        generate_auto_sort_plan()

    else:

        sort_plan.clear()

        refresh_sort_plan_table()

        update_run_sort_plan_button_state()

    save_config()





def toggle_advanced_features_callback():

    global sort_plan

    if not dpg.does_item_exist("auto_sort_header"):

        return

    current_state = dpg.get_value("auto_sort_header")

    dpg.set_value("auto_sort_header", not current_state)

    status = "opened" if not current_state else "collapsed"

    log_message(f"[info] Advanced Features {status}.")

    if not current_state:

        scan_board_button_callback()

    else:

        sort_plan.clear()

        refresh_sort_plan_table()

        update_run_sort_plan_button_state()





def scan_board_button_callback():
    global board_slots, sort_plan
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
    
    refresh_board_slot_table()
    if dpg.does_item_exist("auto_sort_header") and dpg.get_value("auto_sort_header"):
        generate_auto_sort_plan()
    else:
        sort_plan.clear()
        refresh_sort_plan_table()
        update_run_sort_plan_button_state()


def manual_select_slots_callback():
    global board_slots, sort_plan
    if len(area) != 4:
        log_message("[error] Set the screen area first before selecting slots.")
        return
    
    total_slots = board_rows * board_cols
    log_message(f"[info] Manual selection mode: Click on {total_slots} slot positions")
    log_message(f"[info] Expected grid: {board_rows} rows × {board_cols} columns")
    
    selector = MergingPointsSelector(total_slots)
    selected_points = selector.get_points()
    
    if not selected_points or len(selected_points) != total_slots:
        log_message(f"[warn] Expected {total_slots} points, got {len(selected_points)}. Selection cancelled.")
        return
    
    # Create board_slots from manually selected points
    board_slots = []
    point_index = 0
    
    for r in range(board_rows):
        for c in range(board_cols):
            if point_index < len(selected_points):
                slot_id = f"{r}-{c}"
                center = selected_points[point_index]
                
                board_slots.append({
                    "id": slot_id,
                    "row": r,
                    "col": c,
                    "default_center": center,
                    "center": center,
                    "type": None,
                    "template": None,
                    "detected_center": None,
                    "allowed": slot_id not in disallowed_slots,
                })
                point_index += 1
    
    # Now try to detect what's in each slot
    log_message("[info] Detecting items in manually selected slots...")
    img_folder = "./img"
    template_paths = get_image_file_paths(img_folder)
    
    for template_path in template_paths:
        template_name = os.path.basename(template_path)
        points, _ = ImageFinder.find_image_on_screen(
            template_path,
            area[0], area[1], area[2], area[3],
            resize_factor,
        )
        
        for point in points:
            px, py = point
            # Find closest slot
            min_dist = float('inf')
            closest_slot = None
            
            for slot in board_slots:
                sx, sy = slot["center"]
                dist = ((px - sx)**2 + (py - sy)**2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_slot = slot
            
            # Assign if close enough (within reasonable distance)
            if closest_slot and min_dist < 100 and closest_slot["type"] is None:
                closest_slot["type"] = template_name
                closest_slot["template"] = template_path
                closest_slot["detected_center"] = point
    
    apply_slot_overrides()
    occupied = sum(1 for slot in board_slots if slot.get("type"))
    log_message(f"[info] Manual selection complete: {occupied} items detected in {len(board_slots)} slots")
    
    refresh_board_slot_table()
    if dpg.does_item_exist("auto_sort_header") and dpg.get_value("auto_sort_header"):
        generate_auto_sort_plan()
    else:
        sort_plan.clear()
        refresh_sort_plan_table()
        update_run_sort_plan_button_state()





def generate_auto_sort_plan():

    global sort_plan

    sort_plan.clear()

    if not board_slots:

        log_message("[warn] Run a board scan before generating a sort plan.")

        refresh_sort_plan_table()

        update_run_sort_plan_button_state()

        return False



    allowed_slots_sorted = sorted(

        (slot for slot in board_slots if slot["allowed"]),

        key=lambda s: (s["row"], s["col"]),

    )

    if not allowed_slots_sorted:

        log_message("[warn] No allowed slots available for sorting.")

        refresh_sort_plan_table()

        update_run_sort_plan_button_state()

        return False



    working_slots = [{**slot} for slot in allowed_slots_sorted]

    current_types = [slot_copy.get("type") for slot_copy in working_slots]

    nonempty_types = [t for t in current_types if t]



    desired_types = sorted(nonempty_types) + [None] * (len(current_types) - len(nonempty_types))



    if current_types == desired_types:

        log_message("[info] Items already grouped by type. No moves required.")

        refresh_sort_plan_table()

        update_run_sort_plan_button_state()

        return True



    empty_indices = sorted(i for i, t in enumerate(current_types) if t is None)

    if not empty_indices:

        log_message("[warn] No empty slot available as a buffer; cannot build an auto sort plan.")

        refresh_sort_plan_table()

        update_run_sort_plan_button_state()

        return False



    plan_moves = []



    def recompute_empty_indices():

        empty_indices.clear()

        empty_indices.extend(sorted(i for i, t in enumerate(current_types) if t is None))



    def append_move(src_idx, dst_idx):

        if src_idx == dst_idx:

            return

        move_type = current_types[src_idx]

        if move_type is None:

            return

        source_slot = working_slots[src_idx]

        target_slot = working_slots[dst_idx]

        source_center = source_slot.get("detected_center") or source_slot["center"]

        target_center = target_slot["center"]

        plan_moves.append(

            {

                "item": move_type,

                "source_slot": source_slot["id"],

                "target_slot": target_slot["id"],

                "source_center": source_center,

                "target_center": target_center,

            }

        )

        current_types[dst_idx] = move_type

        current_types[src_idx] = None

        target_slot["type"] = move_type

        target_slot["detected_center"] = target_center

        source_slot["type"] = None

        source_slot["detected_center"] = None

        recompute_empty_indices()



    def find_mismatch_index():

        for idx, (current, desired) in enumerate(zip(current_types, desired_types)):

            if current != desired:

                return idx

        return None



    while True:

        mismatch_index = find_mismatch_index()

        if mismatch_index is None:

            break

        desired_type = desired_types[mismatch_index]



        if desired_type is None:

            if current_types[mismatch_index] is None:

                continue

            if not empty_indices:

                log_message("[warn] Cannot free up required slot; aborting plan generation.")

                sort_plan.clear()

                refresh_sort_plan_table()

                update_run_sort_plan_button_state()

                return False

            empty_idx = empty_indices[0]

            if empty_idx == mismatch_index:

                if len(empty_indices) < 2:

                    log_message("[warn] Not enough empty slots to rearrange items.")

                    sort_plan.clear()

                    refresh_sort_plan_table()

                    update_run_sort_plan_button_state()

                    return False

                empty_idx = empty_indices[1]

            append_move(mismatch_index, empty_idx)

            continue



        candidate_indices = [

            idx

            for idx, typ in enumerate(current_types)

            if typ == desired_type and idx != mismatch_index and desired_types[idx] != typ

        ]

        if not candidate_indices:

            candidate_indices = [

                idx

                for idx, typ in enumerate(current_types)

                if typ == desired_type and idx != mismatch_index

            ]

        if not candidate_indices:

            log_message(f"[warn] Could not isolate item '{desired_type}' for sorting.")

            sort_plan.clear()

            refresh_sort_plan_table()

            update_run_sort_plan_button_state()

            return False



        if not empty_indices:

            log_message("[warn] No empty slots available to shuffle items.")

            sort_plan.clear()

            refresh_sort_plan_table()

            update_run_sort_plan_button_state()

            return False



        candidate_idx = candidate_indices[0]

        empty_idx = empty_indices[0]

        if empty_idx == mismatch_index:

            append_move(candidate_idx, mismatch_index)

        else:

            if candidate_idx != empty_idx:

                append_move(candidate_idx, empty_idx)

                candidate_idx = empty_idx

            append_move(candidate_idx, mismatch_index)



    sort_plan = plan_moves

    refresh_sort_plan_table()

    update_run_sort_plan_button_state()

    log_message(f"[info] Generated auto sort plan with {len(sort_plan)} move(s).")

    return True





def generate_sort_plan_callback():

    generate_auto_sort_plan()





def run_sort_plan_callback():

    global sort_plan

    if not sort_plan:

        log_message("[warn] Generate a sort plan before running the sorter.")

        return

    if len(area) != 4:

        log_message("[error] Set the screen area before running the sorter.")

        return

    log_message(f"[info] Executing auto sort plan with {len(sort_plan)} move(s).")

    slot_lookup = {slot["id"]: slot for slot in board_slots}

    for move in sort_plan:

        source_center = move["source_center"]

        target_center = move["target_center"]

        pyautogui.mouseUp()
        pyautogui.moveTo(int(source_center[0]), int(source_center[1]))
        pyautogui.mouseDown()
        pyautogui.moveTo(
            int(target_center[0]),
            int(target_center[1]),
            duration=drag_duration_seconds,
        )
        pyautogui.mouseUp()
        time.sleep(0.05)  # Reduced delay for faster execution

        log_message(

            f"[debug] Moved {move['item']} from {move['source_slot']} to {move['target_slot']}."

        )

        src_slot = slot_lookup.get(move["source_slot"])

        dst_slot = slot_lookup.get(move["target_slot"])

        if src_slot:

            src_slot["type"] = None

            src_slot["detected_center"] = None

        if dst_slot:

            dst_slot["type"] = move["item"]

            dst_slot["detected_center"] = move["target_center"]

    log_message("[info] Auto sort plan completed.")

    sort_plan = []

    refresh_board_slot_table()

    refresh_sort_plan_table()

    update_run_sort_plan_button_state()





def toggle_auto_board_detection_callback(sender, app_data, user_data):
    global auto_board_detection_enabled

    auto_board_detection_enabled = bool(app_data)
    if auto_board_detection_enabled:
        log_message("[info] Auto grid detection enabled.")
        update_board_detection_status(
            "Auto detection enabled. Run Auto Scan to refresh grid.",
            TEXT_MUTED,
        )
    else:
        log_message("[info] Auto grid detection disabled. Using manual rows/cols.")
        update_board_detection_status(
            f"Manual grid: {board_rows}x{board_cols}",
            TEXT_MUTED,
        )

    refresh_board_detection_controls()
    save_config()



def update_board_rows_callback(sender, app_data, user_data):

    global board_rows

    try:

        value = int(app_data)

    except (TypeError, ValueError):

        return

    if auto_board_detection_enabled:
        if dpg.does_item_exist("board_rows_input"):
            dpg.set_value("board_rows_input", board_rows)
        log_message("[warn] Disable auto grid detection to edit rows manually.")
        return

    board_rows = max(1, value)

    update_board_detection_status(f"Manual grid: {board_rows}x{board_cols}", TEXT_MUTED)
    refresh_board_detection_controls()

    save_config()





def update_board_cols_callback(sender, app_data, user_data):

    global board_cols

    try:

        value = int(app_data)

    except (TypeError, ValueError):

        return

    if auto_board_detection_enabled:
        if dpg.does_item_exist("board_cols_input"):
            dpg.set_value("board_cols_input", board_cols)
        log_message("[warn] Disable auto grid detection to edit columns manually.")
        return

    board_cols = max(1, value)

    update_board_detection_status(f"Manual grid: {board_rows}x{board_cols}", TEXT_MUTED)
    refresh_board_detection_controls()

    save_config()





def update_log_message():
    global p, box_amount
    maybe_update_box_count_from_ocr()
    current = dpg.get_value("log_output")

    # Process all messages at once for better performance
    messages = []
    while not queue.get_queue().empty():
        messages.append(queue.get_queue().get())

    counter_updated = False

    for message in messages:
        if message.startswith("BOX_DECREMENT|"):
            try:
                decrement = int(message.split("|")[1])
            except (IndexError, ValueError):
                decrement = 0

            if box_amount is None:
                box_amount = 0

            box_amount = max(0, box_amount - decrement)
            update_box_amount_ui(box_amount, source="manual")
            counter_updated = True

            if box_amount == 0:
                current = f"[warn] No boxes remaining.\n{current}"
                terminate_merge_process()
        else:
            current = f"{message}\n{current}"

    if messages:
        dpg.set_value("log_output", current)
        # Also update quick log if it exists
        if dpg.does_item_exist("quick_log_output"):
            dpg.set_value("quick_log_output", current)
        if counter_updated:
            refresh_box_counter_controls()



def terminate_merge_process(force=False):
    global p, stop_event, is_merge_running
    if p is None:
        return

    pyautogui.mouseUp()
    if stop_event is not None:
        stop_event.set()

    # Instant termination for production
    if p.is_alive():
        p.terminate()
        p.join(timeout=0.5)  # Very short timeout
        if p.is_alive():
            p.kill()  # Force kill if needed
            p.join()

    update_log_message()
    p = None
    is_merge_running = False
    if stop_event is not None:
        stop_event.clear()
        stop_event = None

    maybe_update_box_count_from_ocr(force=True)


def start_merge_process():
    global p, stop_hotkey, area, resize_factor, merge_count, merging_points
    global box_button_point, box_amount, drag_duration_seconds, stop_event

    if p is not None and p.is_alive():
        log_message("[warn] Merge process already running.")
        return

    if len(box_button_point) != 2 or box_amount is None:
        log_message("[error] Configure box button and amount first.")
        return
    if box_amount < 0:
        log_message("[warn] Invalid box amount.")
        return

    maybe_update_box_count_from_ocr(force=True)
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
    
    # Faster polling for instant response
    while process.is_alive():
        update_log_message()
        time.sleep(0.1)  # Reduced from 0.5s to 0.1s for instant response
    
    process.join()
    update_log_message()
    log_message("[info] Merge process stopped.")
    p = None
    is_merge_running = False
    
    if stop_event is not None:
        stop_event.clear()
        stop_event = None





def start_button_callback():
    global hotkey, start_hotkey_handle
    dpg.hide_item("start_button")
    dpg.show_item("stop_button")
    dpg.disable_item("merge_count")
    dpg.disable_item("hotkey_display")
    dpg.disable_item("stop_hotkey_display")
    dpg.disable_item("area_info")
    dpg.disable_item("merging_points")
    dpg.disable_item("resize_factor")
    dpg.disable_item("calculate_resize_factor_button")
    dpg.disable_item("box_button_info")
    dpg.disable_item("box_amount_input")
    log_message("[info] Monitoring enabled. Press = to start/stop instantly.")
    
    if start_hotkey_handle is not None:
        try:
            keyboard.remove_hotkey(start_hotkey_handle)
        except KeyError:
            pass
    
    start_hotkey_handle = keyboard.add_hotkey("+".join(sorted(hotkey)), toggle_merge_process)





def stop_button_callback():
    global start_hotkey_handle
    dpg.hide_item("stop_button")
    dpg.show_item("start_button")
    dpg.enable_item("merge_count")
    dpg.enable_item("hotkey_display")
    dpg.enable_item("stop_hotkey_display")
    dpg.enable_item("area_info")
    dpg.enable_item("merging_points")
    dpg.enable_item("resize_factor")
    dpg.enable_item("calculate_resize_factor_button")
    dpg.enable_item("box_button_info")
    dpg.enable_item("box_amount_input")
    log_message("[info] Monitoring disabled.")
    
    terminate_merge_process()
    if start_hotkey_handle is not None:
        try:
            keyboard.remove_hotkey(start_hotkey_handle)
        except KeyError:
            pass
        start_hotkey_handle = None


def toggle_merge_process():
    """Instant toggle - start if stopped, stop if running."""
    global p, is_merge_running
    if is_merge_running and p is not None and p.is_alive():
        log_message("[info] Stopping...")
        terminate_merge_process()
        is_merge_running = False
    else:
        log_message("[info] Starting...")
        maybe_update_box_count_from_ocr(force=True)
        start_merge_process()
        is_merge_running = True





def select_merging_points_callback():

    global merging_points

    if dpg.does_item_exist("merging_points"):

        dpg.set_item_label("merging_points", "Selecting...")

    selector = MergingPointsSelector(merge_count - 1)

    merging_points = selector.get_points()

    if dpg.does_item_exist("merging_points"):

        dpg.set_item_label(

            "merging_points",

            format_selection_label(f"{len(merging_points)} points"),

        )

    save_config()





def select_box_button_callback():

    global box_button_point

    if dpg.does_item_exist("box_button_info"):

        dpg.set_item_label("box_button_info", "Selecting...")

    selector = MergingPointsSelector(1)

    points = selector.get_points()

    if points and len(points) == 1:

        box_button_point = points[0]

        if dpg.does_item_exist("box_button_info"):

            dpg.set_item_label("box_button_info", format_selection_label(box_button_point))

    else:

        box_button_point = tuple()

        if dpg.does_item_exist("box_button_info"):

            dpg.set_item_label("box_button_info", "Select button")

    save_config()





def record_hotkey():

    record_key("hotkey_display", "hotkey", stop_hotkey)





def record_stop_hotkey():

    record_key("stop_hotkey_display", "stop_hotkey", hotkey)





def record_key(display_tag, key_type, invalid_key):

    def on_key(event):

        if event.event_type == keyboard.KEY_DOWN:

            if "keys" not in on_key.__dict__:

                on_key.keys = set()

            on_key.keys.add(str(event.name))

        elif event.event_type == keyboard.KEY_UP:

            if "keys" in on_key.__dict__ and on_key.keys:

                if on_key.keys.issubset(invalid_key):

                    dpg.set_item_label(display_tag, "")

                else:

                    key_str = format_hotkey_label(on_key.keys)

                    dpg.set_item_label(display_tag, key_str)

                    globals()[key_type] = on_key.keys.copy()

                    on_key.keys.clear()

                    save_config()

            keyboard.unhook(on_key)



    dpg.set_item_label(display_tag, "Press desired keys...")

    keyboard.hook(on_key)





def calculate_resize_factor_callback():

    global resize_factor

    finder = ImageFinder()

    dpg.disable_item("calculate_resize_factor_button")

    dpg.set_value("resize_factor", "Calculating...")

    best_factor = finder.find_best_resize_factor(area)

    resize_factor = best_factor

    dpg.set_value("resize_factor", f"{best_factor:.2f}")

    dpg.enable_item("calculate_resize_factor_button")

    save_config()





auto_refresh_timer = None
last_detection_results = {}


def scan_and_preview_callback():
    """Scan current game area and display detected items with thumbnails"""
    global last_detection_results
    
    if len(area) != 4:
        log_message("[error] Set screen area first before scanning")
        return
    
    log_message("[info] Scanning for items...")
    dpg.set_item_label("scan_preview_button", "⏳ Scanning...")
    dpg.disable_item("scan_preview_button")
    
    # Get all image templates
    img_folder = "./img"
    template_paths = get_image_file_paths(img_folder)
    
    if not template_paths:
        log_message("[warn] No template images found in img/ folder")
        dpg.set_item_label("scan_preview_button", "🔄 Scan Now")
        dpg.enable_item("scan_preview_button")
        return
    
    # Detect items
    detection_results = {}
    total_detected = 0
    
    for template_path in template_paths:
        template_name = os.path.basename(template_path)
        points, _ = ImageFinder.find_image_on_screen(
            template_path,
            area[0], area[1], area[2], area[3],
            resize_factor
        )
        
        if points:
            detection_results[template_name] = {
                'count': len(points),
                'points': points,
                'template_path': template_path
            }
            total_detected += len(points)
    
    last_detection_results = detection_results
    
    # Update preview display
    update_detection_preview(detection_results, total_detected)
    
    # Update header stats
    dpg.set_value("header_detected_count", f"{total_detected} items")
    dpg.configure_item("header_detected_count", 
                       color=SUCCESS_COLOR if total_detected > 0 else TEXT_MUTED)
    
    # Update timestamp
    dpg.set_value("preview_last_scan", datetime.now().strftime("%H:%M:%S"))
    
    log_message(f"[info] Scan complete: {total_detected} items ({len(detection_results)} types)")
    
    dpg.set_item_label("scan_preview_button", "🔄 Scan Now")
    dpg.enable_item("scan_preview_button")


def update_detection_preview(detection_results, total_detected):
    """Update the visual preview panel with detected items"""
    # Clear existing items
    if dpg.does_item_exist("detection_items_container"):
        children = dpg.get_item_children("detection_items_container", 1)
        if children:
            for child in children:
                dpg.delete_item(child)
    
    # Update summary stats
    dpg.set_value("preview_total_count", str(total_detected))
    dpg.set_value("preview_types_count", str(len(detection_results)))
    
    # Also update quick tab stats if they exist
    if dpg.does_item_exist("quick_total_count"):
        dpg.set_value("quick_total_count", str(total_detected))
    if dpg.does_item_exist("quick_types_count"):
        dpg.set_value("quick_types_count", str(len(detection_results)))
    
    if not detection_results:
        dpg.add_text("No items detected", color=TEXT_SUBTLE, parent="detection_items_container")
        return
    
    # Sort by count (most detected first)
    sorted_results = sorted(detection_results.items(), key=lambda x: x[1]['count'], reverse=True)
    
    # Display each detected item type
    for item_name, data in sorted_results:
        count = data['count']
        template_path = data['template_path']
        
        # Create card for each item type
        with dpg.group(horizontal=False, parent="detection_items_container"):
            with dpg.group(horizontal=True, horizontal_spacing=12):
                # Load and display thumbnail
                try:
                    width, height, channels, img_data = dpg.load_image(template_path)
                    
                    # Create texture registry if needed
                    texture_tag = f"texture_{item_name}"
                    if dpg.does_item_exist(texture_tag):
                        dpg.delete_item(texture_tag)
                    
                    with dpg.texture_registry():
                        dpg.add_static_texture(
                            width=width,
                            height=height,
                            default_value=img_data,
                            tag=texture_tag
                        )
                    
                    # Display image
                    dpg.add_image(texture_tag, width=50, height=50)
                    
                except Exception as e:
                    # Fallback if image can't be loaded
                    with dpg.child_window(width=50, height=50, border=True):
                        dpg.add_text("?", color=TEXT_MUTED)
                
                # Item info
                with dpg.group(horizontal=False):
                    # Item name
                    clean_name = item_name.replace(".png", "").replace("_", " ").title()
                    name_text = dpg.add_text(clean_name, color=PURPLE_ACCENT)
                    if FONTS.get("button"):
                        dpg.bind_item_font(name_text, FONTS["button"])
                    
                    # Count badge
                    count_color = SUCCESS_COLOR if count >= 5 else ACCENT_COLOR if count >= 3 else TEXT_MUTED
                    count_text = dpg.add_text(f"× {count} detected", color=count_color)
                    
                    # Show coordinates (first 3)
                    if len(data['points']) > 0:
                        coords_preview = ", ".join([f"({p[0]},{p[1]})" for p in data['points'][:3]])
                        if len(data['points']) > 3:
                            coords_preview += "..."
                        dpg.add_text(coords_preview, color=TEXT_SUBTLE)
            
            dpg.add_spacer(height=8)
            dpg.add_separator()
            dpg.add_spacer(height=8)


def toggle_auto_refresh_callback(sender, app_data):
    """Enable/disable auto-refresh of detection preview"""
    global auto_refresh_timer
    
    if app_data:  # Enabled
        log_message("[info] Auto-refresh enabled (every 3 seconds)")
        schedule_auto_refresh()
    else:  # Disabled
        log_message("[info] Auto-refresh disabled")
        if auto_refresh_timer:
            auto_refresh_timer = None


def schedule_auto_refresh():
    """Schedule next auto-refresh scan"""
    global auto_refresh_timer
    
    if dpg.does_item_exist("auto_refresh_preview") and dpg.get_value("auto_refresh_preview"):
        scan_and_preview_callback()
        # Schedule next refresh in 3 seconds
        # Note: DearPyGUI doesn't have built-in timers, so we'd need to check in the main loop
        # For now, this is a placeholder - we'll check in update_log_message


def launch_template_collector(category, crop_size):
    """Launch the template collector tool in a subprocess"""
    log_message(f"[info] Launching template collector for {category}...")
    log_message(f"[info] Left-click items to capture, Right-click to exit")
    
    try:
        collector = TemplateCollector(category, crop_size)
        collector.start_capture_mode()
        log_message(f"[info] Template collector closed")
    except Exception as e:
        log_message(f"[error] Template collector error: {e}")


def select_area_callback():

    global area

    if dpg.does_item_exist("area_info"):

        dpg.set_item_label("area_info", "Selecting...")

    selector = ScreenAreaSelector()

    coordinates = selector.get_coordinates()

    if coordinates and len(coordinates) == 4:

        area = coordinates

        if dpg.does_item_exist("area_info"):

            dpg.set_item_label("area_info", format_selection_label(coordinates))

    else:

        area = tuple()

        if dpg.does_item_exist("area_info"):

            dpg.set_item_label("area_info", "Select area")

    save_config()





if __name__ == "__main__":

    multiprocessing.freeze_support()

    create_gui()
