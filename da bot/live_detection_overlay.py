"""Live Detection Overlay Integration."""

from __future__ import annotations

import os
import threading
import time
from typing import Dict, Tuple

import cv2

try:
    from detection_overlay import OverlayBridge, OVERLAY_AVAILABLE
except ImportError:
    OverlayBridge = None
    OVERLAY_AVAILABLE = False


class LiveDetectionManager:
    """Manages live detection overlay for real-time visual feedback."""

    def __init__(self, log_callback=None, game_area: Tuple[int, int, int, int] | None = None):
        self.log_callback = log_callback
        self.game_area = game_area
        self.resize_factor = 1.0
        self.overlay = OverlayBridge(game_area=game_area) if OVERLAY_AVAILABLE and OverlayBridge else None
        self.detection_thread: threading.Thread | None = None
        self._stop_detection = threading.Event()
        self._template_cache: Dict[str, Tuple[int, int]] = {}
        self._manual_hold_until = 0.0
        self._manual_hold_duration = 0.8
        self._live_updates_allowed = threading.Event()
        self._live_updates_allowed.set()

    def _log(self, message: str, level: str = "info"):
        if self.log_callback:
            self.log_callback(message, level)

    def update_game_area(self, game_area: Tuple[int, int, int, int]):
        self.game_area = game_area
        if self.overlay:
            self.overlay.set_game_area(game_area)

    def set_resize_factor(self, value: float):
        self.resize_factor = value

    def configure_overlay(self, **kwargs):
        if self.overlay:
            self.overlay.configure(**kwargs)

    def _ensure_overlay(self) -> bool:
        if not OVERLAY_AVAILABLE or not self.overlay:
            self._log("Detection overlay module not available", "error")
            return False
        if not self.game_area or len(self.game_area) != 4:
            self._log("Set the screen area before enabling the overlay", "error")
            return False
        if not self.overlay.is_running():
            return self.overlay.start(game_area=self.game_area)
        return True

    def start_overlay(self, game_area: Tuple[int, int, int, int] | None = None) -> bool:
        if game_area:
            self.update_game_area(game_area)
        if not self._ensure_overlay():
            return False
        self._log("Detection overlay started", "success")
        return True

    def stop_overlay(self):
        self.stop_live_detection()
        if self.overlay and self.overlay.is_running():
            self.overlay.stop()
            self._log("Detection overlay stopped", "info")

    def is_overlay_running(self) -> bool:
        return bool(self.overlay and self.overlay.is_running())

    def _scaled_template_size(self, template_path: str | None, resize_factor: float) -> Tuple[int, int]:
        if not template_path:
            return 40, 40
        if template_path not in self._template_cache:
            try:
                image = cv2.imread(template_path)
                if image is None:
                    raise ValueError("Unable to read template")
                h, w = image.shape[:2]
                self._template_cache[template_path] = (w, h)
            except Exception:
                self._template_cache[template_path] = (40, 40)
        base_w, base_h = self._template_cache[template_path]
        scaled_w = max(12, int(base_w * resize_factor))
        scaled_h = max(12, int(base_h * resize_factor))
        return scaled_w, scaled_h

    def update_detections_from_scan(
        self,
        detection_results: Dict,
        game_area: Tuple[int, int, int, int],
        resize_factor: float,
    ):
        if not detection_results or not self.overlay or not self.overlay.is_running():
            return
        self.update_game_area(game_area)
        self.set_resize_factor(resize_factor)

        # IMPORTANT: Build complete payload from ALL detection results at once
        # This ensures hybrid mode's GPU+CPU verification results are all included
        # in a single overlay update, preventing "two waves" of green boxes
        payload = []
        for template_name, data in detection_results.items():
            points = data.get("points", [])
            if not points:  # Skip templates with no detections
                continue
            template_path = data.get("template_path")
            width, height = self._scaled_template_size(template_path, resize_factor)
            half_w = width // 2
            half_h = height // 2
            label = os.path.splitext(template_name)[0]

            for cx, cy in points:
                x1 = int(cx - half_w)
                y1 = int(cy - half_h)
                x2 = int(cx + half_w)
                y2 = int(cy + half_h)
                payload.append(
                    {
                        "label": label,
                        "bbox": (x1, y1, x2, y2),
                    }
                )

        # Update overlay ONCE with complete payload (all detections together)
        # The overlay's queue mechanism will flush any pending updates and show only this final result
        if payload:
            self.overlay.update_detections(payload)
        else:
            self.overlay.update_detections([])

    def display_manual_snapshot(
        self,
        detection_results: Dict,
        game_area: Tuple[int, int, int, int],
        resize_factor: float,
        hold_duration: float | None = None,
    ):
        """Show manual detections and pause live updates briefly."""
        duration = hold_duration if hold_duration is not None else self._manual_hold_duration
        self._manual_hold_until = time.time() + duration
        self._live_updates_allowed.clear()
        self.update_detections_from_scan(detection_results, game_area, resize_factor)

    def start_live_detection(
        self,
        scan_callable,
        scan_interval: float = 1.0,
        resize_factor: float | None = None,
    ):
        if not self._ensure_overlay():
            return

        if self.detection_thread and self.detection_thread.is_alive():
            self._log("Live detection already running", "warning")
            return

        if resize_factor is not None:
            self.resize_factor = resize_factor

        self._stop_detection.clear()
        interval = max(0.05, float(scan_interval) if scan_interval is not None else 0.0)

        def detection_loop():
            while not self._stop_detection.is_set():
                loop_start = time.perf_counter()
                try:
                    results = scan_callable()
                except Exception as exc:
                    self._log(f"Live scan error: {exc}", "error")
                    break

                if results:
                    detections, _ = results
                    if detections is not None and self.game_area:
                        # Wait until manual snapshot window expires
                        if not self._live_updates_allowed.is_set():
                            if time.time() >= self._manual_hold_until:
                                self._live_updates_allowed.set()
                            else:
                                self._stop_detection.wait(timeout=0.05)
                                continue
                        self.update_detections_from_scan(detections, self.game_area, self.resize_factor)

                elapsed = time.perf_counter() - loop_start
                remaining = interval - elapsed
                if remaining > 0:
                    self._stop_detection.wait(timeout=remaining)

        self.detection_thread = threading.Thread(target=detection_loop, daemon=True)
        self.detection_thread.start()
        self._log("Live scanning started", "success")

    def stop_live_detection(self):
        self._stop_detection.set()
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1.0)
        self.detection_thread = None
        if self.overlay:
            self.overlay.update_detections([])
        self._log("Live scanning stopped", "info")
