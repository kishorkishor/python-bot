"""Live detection overlay implemented via a dedicated Tk subprocess."""

from __future__ import annotations

import multiprocessing as mp
import queue
from typing import Dict, List, Tuple

try:
    import tkinter as tk  # noqa: F401

    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False
    tk = None

__all__ = ["OverlayBridge", "OVERLAY_AVAILABLE"]

OVERLAY_AVAILABLE = TK_AVAILABLE


def _overlay_process(
    game_area: Tuple[int, int, int, int],
    command_queue: mp.Queue,
    detection_queue: mp.Queue,
    initial_config: Dict,
):
    """Child process entry point that owns the Tk event loop."""
    if not TK_AVAILABLE:
        return

    import tkinter as tk  # type: ignore

    class OverlayApp:
        def __init__(self, root: tk.Tk, area: Tuple[int, int, int, int], config: Dict):
            self.root = root
            self.config = dict(config)
            self.game_area = area
            self.detections: List[Dict] = []
            self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self._apply_window_geometry()

        def _apply_window_geometry(self):
            if not self.game_area or len(self.game_area) != 4:
                width = self.root.winfo_screenwidth()
                height = self.root.winfo_screenheight()
                x_pos = 0
                y_pos = 0
            else:
                x1, y1, x2, y2 = self.game_area
                width = max(50, int(x2 - x1))
                height = max(50, int(y2 - y1))
                x_pos = int(x1)
                y_pos = int(y1)

            self.root.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
            self.canvas.config(width=width, height=height)
            try:
                self.root.attributes("-topmost", True)
                self.root.attributes("-alpha", self.config.get("opacity", 0.95))  # Less transparent - more visible
                self.root.attributes("-transparentcolor", "black")
                self.root.overrideredirect(True)
            except Exception:
                pass

        def set_game_area(self, area: Tuple[int, int, int, int]):
            self.game_area = area
            self._apply_window_geometry()

        def set_config(self, **kwargs):
            self.config.update(kwargs)
            try:
                self.root.attributes("-alpha", self.config.get("opacity", 0.95))  # Less transparent - more visible
            except Exception:
                pass

        def set_detections(self, detections: List[Dict]):
            self.detections = detections

        def draw(self):
            self.canvas.delete("all")
            for det in self.detections:
                bbox = det.get("bbox")
                if not bbox or len(bbox) != 4:
                    continue
                x1, y1, x2, y2 = bbox
                if self.game_area and len(self.game_area) == 4:
                    gx1, gy1, _, _ = self.game_area
                    x1 -= gx1
                    y1 -= gy1
                    x2 -= gx1
                    y2 -= gy1
                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    outline=self.config.get("box_color", "#00FF00"),
                    width=self.config.get("box_thickness", 2),
                )
                if self.config.get("show_labels", True):
                    label = det.get("label", "Item")
                    confidence = det.get("confidence", 0.0)
                    if confidence:
                        label = f"{label} ({confidence:.0%})"
                    center = (x1 + x2) / 2
                    text_id = self.canvas.create_text(
                        center,
                        y2 + 12,
                        text=label,
                        fill=self.config.get("label_fg", "#FFFFFF"),
                        font=("Segoe UI", self.config.get("label_font_size", 10), "bold"),
                    )
                    bbox_text = self.canvas.bbox(text_id)
                    if bbox_text:
                        self.canvas.create_rectangle(
                            bbox_text[0] - 3,
                            bbox_text[1] - 2,
                            bbox_text[2] + 3,
                            bbox_text[3] + 2,
                            fill=self.config.get("label_bg", "#000000"),
                            outline=self.config.get("label_bg", "#000000"),
                        )
                        self.canvas.tag_raise(text_id)

    root = tk.Tk()
    app = OverlayApp(root, game_area, initial_config)

    def pump():
        try:
            while True:
                cmd = command_queue.get_nowait()
                action = cmd.get("cmd")
                if action == "stop":
                    root.destroy()
                    return
                if action == "config":
                    app.set_config(**cmd.get("data", {}))
                if action == "area":
                    app.set_game_area(cmd.get("data"))
        except queue.Empty:
            pass

        try:
            latest = None
            while True:
                latest = detection_queue.get_nowait()
        except queue.Empty:
            if latest is not None:
                app.set_detections(latest)
        else:
            if latest is not None:
                app.set_detections(latest)

        app.draw()
        root.after(33, pump)  # Faster - 33ms = ~30 FPS for smoother updates

    root.after(0, pump)
    root.mainloop()


class OverlayBridge:
    """Parent-process controller for the overlay subprocess."""

    def __init__(self, game_area: Tuple[int, int, int, int] | None = None):
        self.game_area = game_area
        self._process: mp.Process | None = None
        self._command_queue: mp.Queue | None = None
        self._detection_queue: mp.Queue | None = None
        self._config = {
            "box_color": "#00FF00",
            "box_thickness": 2,
            "label_bg": "#000000",
            "label_fg": "#FFFFFF",
            "label_font_size": 10,
            "show_labels": True,
            "opacity": 0.95,  # Less transparent - more visible
        }

    def start(self, game_area: Tuple[int, int, int, int] | None = None) -> bool:
        if not OVERLAY_AVAILABLE:
            return False

        if game_area:
            self.game_area = game_area

        if not self.game_area or len(self.game_area) != 4:
            return False

        if self.is_running():
            return True

        self._command_queue = mp.Queue()
        self._detection_queue = mp.Queue()
        self._process = mp.Process(
            target=_overlay_process,
            args=(self.game_area, self._command_queue, self._detection_queue, self._config),
            daemon=True,
        )
        self._process.start()
        return True

    def stop(self):
        if not self.is_running():
            return
        try:
            if self._command_queue:
                self._command_queue.put({"cmd": "stop"})
        except Exception:
            pass
        if self._process:
            self._process.join(timeout=1.5)
            if self._process.is_alive():
                self._process.terminate()
        self._process = None
        self._command_queue = None
        self._detection_queue = None

    def is_running(self) -> bool:
        return self._process is not None and self._process.is_alive()

    def update_detections(self, detections: List[Dict]):
        if not self.is_running() or not self._detection_queue:
            return
        # CRITICAL FIX: Flush ALL pending updates and replace with new complete result
        # This ensures only the latest complete detection result is shown, preventing "two waves"
        try:
            # Remove all pending updates from queue (keep only the latest)
            while True:
                self._detection_queue.get_nowait()
        except queue.Empty:
            pass
        except Exception:
            pass
        # Now add the complete final result (all detections together)
        try:
            self._detection_queue.put_nowait(detections)
        except Exception:
            pass

    def configure(self, **kwargs):
        self._config.update(kwargs)
        if self._command_queue:
            try:
                self._command_queue.put({"cmd": "config", "data": kwargs})
            except Exception:
                pass

    def set_game_area(self, game_area: Tuple[int, int, int, int]):
        self.game_area = game_area
        if self._command_queue and self.is_running():
            try:
                self._command_queue.put({"cmd": "area", "data": game_area})
            except Exception:
                pass

