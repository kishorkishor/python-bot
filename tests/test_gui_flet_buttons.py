"""
Lightweight regression checks for the Flet GUI.

The test spins up the UI tree in a stubbed environment (no global hooks,
no OS-level hotkeys) and exercises every click handler once to ensure we
don't raise on user interaction. This gives us a quick way to validate
button wiring without requiring a graphical session.
"""

from __future__ import annotations

import sys
import types
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Iterable, List, Optional

import numpy as np
from PIL import Image


# -----------------------------------------------------------------------------
# Prepare import path and stub modules _before_ importing the GUI
# -----------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
FARM_MERGER_DIR = REPO_ROOT / "farm_merger"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(FARM_MERGER_DIR))

# Keyboard stub (no global hooks)
keyboard_stub = types.ModuleType("keyboard")
keyboard_stub.add_hotkey = lambda *args, **kwargs: None
keyboard_stub.remove_hotkey = lambda *args, **kwargs: None
keyboard_stub.is_pressed = lambda *args, **kwargs: False
sys.modules["keyboard"] = keyboard_stub


def _dummy_image(*args, **kwargs):
    """Return a tiny black image that behaves like PyAutoGUI screenshots."""
    return Image.fromarray(np.zeros((10, 10, 3), dtype=np.uint8))


# PyAutoGUI stub (avoid real mouse movement)
pyautogui_stub = types.ModuleType("pyautogui")
pyautogui_stub.moveTo = lambda *args, **kwargs: None
pyautogui_stub.mouseUp = lambda *args, **kwargs: None
pyautogui_stub.mouseDown = lambda *args, **kwargs: None
pyautogui_stub.click = lambda *args, **kwargs: None
pyautogui_stub.screenshot = _dummy_image
sys.modules["pyautogui"] = pyautogui_stub


# Pytesseract stub (avoid OCR dependency)
pytesseract_stub = types.ModuleType("pytesseract")


class _DummyPytesseract:
    pytesseract = None
    tesseract_cmd = ""

    @staticmethod
    def get_tesseract_version():
        class _Version:
            def __str__(self) -> str:
                return "0.0"

        return _Version()

    @staticmethod
    def image_to_string(*args, **kwargs):
        return "0"


pytesseract_stub.pytesseract = _DummyPytesseract()
pytesseract_stub.get_tesseract_version = _DummyPytesseract.get_tesseract_version
pytesseract_stub.image_to_string = _DummyPytesseract.image_to_string
sys.modules["pytesseract"] = pytesseract_stub


# Image finder stub (avoid OpenCV work during tests)
item_finder_stub = types.ModuleType("item_finder")


class _StubImageFinder:
    @staticmethod
    def find_image_on_screen(*args, **kwargs):
        return [], None


item_finder_stub.ImageFinder = _StubImageFinder
sys.modules["item_finder"] = item_finder_stub


# Selector stubs (avoid tkinter dependency)
merging_points_selector_stub = types.ModuleType("merging_points_selector")


class _StubMergingPointsSelector:
    def __init__(self, *args, **kwargs):
        pass

    def get_points(self):
        return [(0, 0)]


merging_points_selector_stub.MergingPointsSelector = _StubMergingPointsSelector
sys.modules["merging_points_selector"] = merging_points_selector_stub


screen_area_selector_stub = types.ModuleType("screen_area_selector")


class _StubScreenAreaSelector:
    def __init__(self, *args, **kwargs):
        pass

    def get_coordinates(self):
        return (0, 0, 100, 100)


screen_area_selector_stub.ScreenAreaSelector = _StubScreenAreaSelector
sys.modules["screen_area_selector"] = screen_area_selector_stub


# Template collector stub (avoid launching overlays)
template_collector_stub = types.ModuleType("template_collector")


class _StubTemplateCollector:
    def __init__(self, category, crop_size):
        self.category = category
        self.crop_size = crop_size
        self.click_count = 1
        self.captured_templates = [{"name": "stub", "path": f"./img/{category}/stub.png"}]

    def start_capture_mode(self):
        return None


template_collector_stub.TemplateCollector = _StubTemplateCollector
sys.modules["template_collector"] = template_collector_stub


import flet as ft
import flet.core.control as control_module

# Neutralise Control.update() so we can exercise handlers without a live session
control_module.Control.update = lambda self: None  # type: ignore[assignment]

import farm_merger.gui_flet as gui_flet


# -----------------------------------------------------------------------------
# Helper structures
# -----------------------------------------------------------------------------


class _DummyPage:
    """Very small stand-in for ft.Page used during handler collection."""

    def __init__(self):
        self.added: List[ft.Control] = []
        self.dialog: Optional[ft.AlertDialog] = None
        self.title = ""
        self.theme_mode = None
        self.bgcolor = None
        self.padding = None
        self.spacing = None
        self.scroll = None

    def add(self, *controls: ft.Control) -> None:
        self.added.extend(controls)

    def update(self) -> None:  # pragma: no cover - Nothing to do in headless mode
        return None


@dataclass
class ClickHandlerInfo:
    label: str
    handler: Callable[[SimpleNamespace], None]
    control: ft.Control
    path: str


def _iter_controls(control: ft.Control, path: str = "root") -> Iterable[tuple[ft.Control, str]]:
    yield control, path
    if hasattr(control, "content") and getattr(control, "content") is not None:
        yield from _iter_controls(control.content, f"{path}.content")
    if hasattr(control, "controls") and getattr(control, "controls"):
        for idx, child in enumerate(control.controls):
            yield from _iter_controls(child, f"{path}.controls[{idx}]")


def _collect_click_handlers(page: _DummyPage) -> List[ClickHandlerInfo]:
    handlers: List[ClickHandlerInfo] = []
    for root in page.added:
        for control, path in _iter_controls(root):
            handler = getattr(control, "on_click", None)
            if not callable(handler):
                continue

            label = "<unnamed>"
            if isinstance(control, ft.Container) and isinstance(control.content, ft.Row):
                text_values = [
                    getattr(child, "value", None)
                    for child in control.content.controls
                    if isinstance(child, ft.Text)
                ]
                label = next((value for value in text_values if value), label)
            elif isinstance(control, (ft.TextButton, ft.ElevatedButton)):
                label = getattr(control, "text", label)
            elif isinstance(control, ft.IconButton):
                label = getattr(control, "icon", label)

            handlers.append(ClickHandlerInfo(label=label, handler=handler, control=control, path=path))
    return handlers


# -----------------------------------------------------------------------------
# Test case
# -----------------------------------------------------------------------------


class TestGuiFletButtonHandlers(unittest.TestCase):
    """Ensure each clickable control executes without raising exceptions."""

    @classmethod
    def setUpClass(cls) -> None:
        # Keep filesystem clean during tests
        gui_flet.save_config = lambda: None
        gui_flet.terminate_merge_process = lambda force=False: None
        gui_flet.start_merge_process = lambda: None
        gui_flet.log_message = lambda msg: None
        gui_flet._log_callback = None

        page = _DummyPage()
        gui_flet.create_flet_gui(page)
        cls.handlers = _collect_click_handlers(page)

    def test_all_click_handlers(self) -> None:
        self.assertGreater(len(self.handlers), 0)
        for click_info in self.handlers:
            with self.subTest(label=click_info.label, path=click_info.path):
                event = SimpleNamespace(control=click_info.control)
                click_info.handler(event)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
