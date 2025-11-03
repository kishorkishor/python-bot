"""Image detection utilities for Kishor Farm Merger Pro."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pyautogui


class TemplateCatalog:
    """Load template metadata (thresholds, rarity, priorities) from catalog.json."""

    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self.defaults: Dict[str, object] = {
            "threshold": 0.75,
            "priority": 5,
            "rarity": "common",
            "reference": False,
        }
        self.templates: Dict[str, Dict[str, object]] = {}
        self._load()

    def _load(self) -> None:
        if not self.catalog_path or not self.catalog_path.exists():
            return

        try:
            with self.catalog_path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[catalog] Failed to load template catalog: {exc}")
            return

        templates = payload.get("templates") if isinstance(payload, dict) else None
        if isinstance(templates, dict):
            for name, metadata in templates.items():
                if isinstance(metadata, dict):
                    self.templates[name] = metadata

        defaults = payload.get("defaults") if isinstance(payload, dict) else None
        if isinstance(defaults, dict):
            for key, value in defaults.items():
                if key in self.defaults:
                    self.defaults[key] = value

    def metadata_for(self, template_name: str) -> Dict[str, object]:
        data = dict(self.defaults)
        data.update(self.templates.get(template_name, {}))
        return data

    def threshold_for(self, template_name: str, fallback: Optional[float] = None) -> float:
        if fallback is not None:
            return float(fallback)
        metadata = self.metadata_for(template_name)
        return float(metadata.get("threshold", self.defaults["threshold"]))

    def reference_template_names(self) -> List[str]:
        return [
            name
            for name, meta in self.templates.items()
            if isinstance(meta, dict) and meta.get("reference")
        ]


CATALOG_PATH = Path(__file__).resolve().parent / "img" / "catalog.json"
TEMPLATE_CATALOG = TemplateCatalog(CATALOG_PATH)


class ImageFinder:
    @staticmethod
    def find_best_resize_factor(area: Optional[Tuple[int, int, int, int]] = None, threshold: float = 0.80) -> float:
        print("Finding best resize factor")
        if area is None or len(area) != 4:
            area = (0, 0, pyautogui.size()[0], pyautogui.size()[1])

        best_factor = 0.5
        best_total_matches = 0
        image_dir = Path(__file__).resolve().parent / "img"

        reference_names = TEMPLATE_CATALOG.reference_template_names()
        if reference_names:
            image_paths = [str(image_dir / name) for name in reference_names if (image_dir / name).exists()]
        else:
            fallback_names = ["cow1.png", "wheat1.png", "chicken1.png", "soybean1.png", "corn1.png"]
            image_paths = [str(image_dir / name) for name in fallback_names if (image_dir / name).exists()]

        if not image_paths:
            image_paths = [
                str(path)
                for path in image_dir.iterdir()
                if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
            ]

        for factor in np.arange(0.8, 2.1, 0.1):  # From 0.8 to 2.0 with 0.1 step
            total_matches = 0
            for image_path in image_paths:
                screen_points, _ = ImageFinder.find_image_on_screen(
                    image_path,
                    area[0],
                    area[1],
                    area[2],
                    area[3],
                    resize_factor=factor,
                    threshold=threshold,
                )
                total_matches += len(screen_points)
            if total_matches > best_total_matches:
                best_total_matches = total_matches
                best_factor = factor

        return best_factor

    @staticmethod
    def find_image_on_screen(
        image_path: str,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        resize_factor: float = 1,
        threshold: Optional[float] = None,
    ):
        # Load the template image
        template = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"[image_finder] Unable to read template: {image_path}")
            return [], None

        # Resize the template image
        h, w = template.shape[:2]
        new_h, new_w = int(h * resize_factor), int(w * resize_factor)
        template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Take a screenshot of the specified region
        screenshot = pyautogui.screenshot(region=(start_x, start_y, end_x - start_x, end_y - start_y))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Perform template matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

        # Find all matches above the threshold
        image_name = os.path.basename(image_path)
        current_threshold = TEMPLATE_CATALOG.threshold_for(image_name, threshold)
        locations = np.where(result >= current_threshold)

        matches = list(zip(*locations[::-1]))  # Reverse the order of coordinates

        # Calculate the center points of all matches and black out the matched areas
        h, w = template.shape[:2]
        center_points: List[Tuple[int, int]] = []
        for (x, y) in matches:
            overlaps = any(
                abs(x - prev_x) < w and abs(y - prev_y) < h
                for prev_x, prev_y in center_points
            )
            if not overlaps:
                center_x = int(x + w / 2)
                center_y = int(y + h / 2)
                center_points.append((center_x, center_y))

                # Black out the matched area
                screenshot[y:y + h, x:x + w] = 0  # 0 represents black in BGR

        # Adjust center points to screen coordinates
        screen_points = [(x + start_x, y + start_y) for (x, y) in center_points]

        return screen_points, screenshot  # Return both the points and the modified screenshot

    @staticmethod
    def get_template_metadata(template_name: str) -> Dict[str, object]:
        return TEMPLATE_CATALOG.metadata_for(template_name)
