"""Robust pyautogui import helper with a lightweight stub fallback.

This allows test suites (and headless environments) to import modules that
expect pyautogui without pulling in the real dependency or requiring a GUI
driver.  When the actual pyautogui package is available it is returned as-is;
otherwise we provide a minimal stub that covers the subset of functionality
used by Farm Merger (mouse position helpers, screenshots, and presses).
"""

from __future__ import annotations

import importlib
import sys
import time
from dataclasses import dataclass
from typing import Tuple

import numpy as np


def _try_import_real() -> object | None:
    """Attempt to import the real pyautogui module."""
    try:
        return importlib.import_module("pyautogui")
    except ModuleNotFoundError:
        return None
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[pyautogui_safe] Failed to import real pyautogui: {exc}")
        return None


@dataclass
class _FakeScreenshot:
    width: int
    height: int

    def __post_init__(self) -> None:
        self.size = (self.width, self.height)
        self._array = np.zeros((self.height, self.width, 3), dtype=np.uint8)

    def __array__(self, dtype=None):  # pragma: no cover - numpy hook
        return self._array.astype(dtype) if dtype else self._array

    def copy(self) -> "_FakeScreenshot":
        dup = _FakeScreenshot(self.width, self.height)
        dup._array[:] = self._array
        return dup


class _StubPyAutoGUI:
    """Very small subset of pyautogui used during tests."""

    FAILSAFE = False
    PAUSE = 0.0

    def __init__(self) -> None:
        self._screen_size = (1280, 720)
        self._position = (self._screen_size[0] // 2, self._screen_size[1] // 2)

    # ------------------------------------------------------------------ helpers
    def size(self) -> Tuple[int, int]:
        return self._screen_size

    def position(self) -> Tuple[int, int]:
        return self._position

    # ------------------------------------------------------------------ actions
    def moveTo(self, x: float, y: float, duration: float = 0) -> None:  # noqa: N802
        self._position = (int(x), int(y))

    def click(self, x: float | None = None, y: float | None = None, button: str = "left") -> None:
        if x is not None and y is not None:
            self.moveTo(x, y)

    def doubleClick(self, x: float | None = None, y: float | None = None) -> None:  # noqa: N802
        self.click(x, y)
        self.click(x, y)

    def mouseDown(self, x: float | None = None, y: float | None = None) -> None:  # noqa: N802
        if x is not None and y is not None:
            self.moveTo(x, y)

    def mouseUp(self, x: float | None = None, y: float | None = None) -> None:  # noqa: N802
        if x is not None and y is not None:
            self.moveTo(x, y)

    def press(self, key: str) -> None:
        print(f"[pyautogui_stub] press({key})")

    def screenshot(self, region=None) -> _FakeScreenshot:
        if region and len(region) == 4:
            width = max(1, int(region[2]))
            height = max(1, int(region[3]))
        else:
            width, height = self._screen_size
        return _FakeScreenshot(width, height)

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


_real_module = _try_import_real()

if _real_module is not None:
    pyautogui = _real_module
    PY_AUTO_GUI_STUB = False
else:
    pyautogui = _StubPyAutoGUI()
    PY_AUTO_GUI_STUB = True

__all__ = ["pyautogui", "PY_AUTO_GUI_STUB"]

