"""Image detection utilities for Kishor Farm Merger Pro."""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import deque

import cv2
import numpy as np
from pyautogui_safe import pyautogui
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


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
        self._lock = threading.Lock()
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
    
    def set_threshold(self, template_name: str, threshold: float) -> None:
        """Set threshold for a template and auto-save."""
        with self._lock:
            if template_name not in self.templates:
                self.templates[template_name] = {}
            self.templates[template_name]["threshold"] = float(threshold)
            self._save()
    
    def set_default_threshold(self, threshold: float) -> None:
        """Set default threshold and auto-save."""
        with self._lock:
            self.defaults["threshold"] = float(threshold)
            self._save()
    
    def _save(self) -> None:
        """Save catalog to JSON file."""
        if not self.catalog_path:
            return
        
        try:
            # Ensure directory exists
            self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            
            payload = {
                "defaults": self.defaults,
                "templates": self.templates
            }
            
            with self.catalog_path.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=4)
        except (OSError, json.JSONEncodeError) as exc:
            print(f"[catalog] Failed to save template catalog: {exc}")


CATALOG_PATH = Path(__file__).resolve().parent / "img" / "catalog.json"
TEMPLATE_CATALOG = TemplateCatalog(CATALOG_PATH)


# Optimization: Historic detection tracking for hybrid mode
class DetectionHistoryTracker:
    """Track historic detections to skip redundant CPU verification."""
    
    def __init__(self, max_history=10, position_tolerance=5):
        self.history = {}  # template_name -> deque of (x, y, confidence, timestamp)
        self.max_history = max_history
        self.position_tolerance = position_tolerance
        self._lock = threading.Lock()
    
    def is_known_detection(self, template_name: str, x: int, y: int, confidence: float, cooldown: float = 0.5) -> bool:
        """Check if this detection is a known stable position."""
        with self._lock:
            if template_name not in self.history:
                return False
            
            current_time = time.time()
            recent_detections = self.history[template_name]
            
            # Check if we've seen this position recently
            for (hx, hy, hconf, htime) in recent_detections:
                if current_time - htime > cooldown:
                    continue
                
                # Check if position matches within tolerance
                if abs(x - hx) <= self.position_tolerance and abs(y - hy) <= self.position_tolerance:
                    # If confidence is similar, skip verification
                    if abs(confidence - hconf) < 0.05:
                        return True
            
            return False
    
    def add_detection(self, template_name: str, x: int, y: int, confidence: float):
        """Add a verified detection to history."""
        with self._lock:
            if template_name not in self.history:
                self.history[template_name] = deque(maxlen=self.max_history)
            
            self.history[template_name].append((x, y, confidence, time.time()))
    
    def clear_old(self, max_age: float = 5.0):
        """Clear detections older than max_age seconds."""
        with self._lock:
            current_time = time.time()
            for template_name in list(self.history.keys()):
                recent = deque(maxlen=self.max_history)
                for detection in self.history[template_name]:
                    if current_time - detection[3] <= max_age:
                        recent.append(detection)
                
                if recent:
                    self.history[template_name] = recent
                else:
                    del self.history[template_name]


# Global tracker instance
DETECTION_HISTORY = DetectionHistoryTracker()


# Optimization: Template cache with pre-uploaded GPU templates
class TemplateCache:
    """Cache templates in both CPU and GPU memory for reuse."""
    
    def __init__(self):
        self.cpu_cache = {}  # path -> (template_bgr, template_gray)
        self.gpu_cache = {}  # path -> UMat
        self._lock = threading.Lock()
        self._ocl_enabled = False
        self._init_opencl()
    
    def _init_opencl(self):
        """Initialize OpenCL if available with AMD GPU optimizations."""
        try:
            cv2.ocl.setUseOpenCL(True)
            if cv2.ocl.haveOpenCL():
                self._ocl_enabled = True
                print("[template_cache] OpenCL enabled successfully")
                
                # AMD GPU specific optimizations
                try:
                    device = cv2.ocl.Device.getDefault()
                    device_name = device.name() if hasattr(device, 'name') else "Unknown"
                    
                    if 'AMD' in device_name.upper() or 'RADEON' in device_name.upper():
                        print(f"[AMD GPU] Detected: {device_name}")
                        
                        # Enable binary disk cache for AMD (speeds up kernel compilation)
                        cv2.ocl.setBinaryDiskCache(True)
                        print("[AMD GPU] Binary disk cache enabled")
                        
                        # Log AMD GPU specs
                        if hasattr(device, 'maxComputeUnits'):
                            print(f"[AMD GPU] Compute units: {device.maxComputeUnits()}")
                        if hasattr(device, 'globalMemSize'):
                            mem_mb = device.globalMemSize() // (1024**2)
                            print(f"[AMD GPU] Memory: {mem_mb} MB")
                except Exception as dev_e:
                    print(f"[AMD GPU] Could not read device info: {dev_e}")
            else:
                print("[template_cache] OpenCL not available")
        except Exception as e:
            print(f"[template_cache] Failed to enable OpenCL: {e}")
    
    def get_template(self, path: str, resize_factor: float = 1.0, use_gpu: bool = False):
        """Get cached template or load and cache it."""
        cache_key = f"{path}_{resize_factor}"
        
        with self._lock:
            # Check CPU cache
            if cache_key in self.cpu_cache:
                template = self.cpu_cache[cache_key]
            else:
                # Load and cache
                template = cv2.imread(path, cv2.IMREAD_COLOR)
                if template is None:
                    return None
                
                if resize_factor != 1.0:
                    h, w = template.shape[:2]
                    new_h, new_w = int(h * resize_factor), int(w * resize_factor)
                    template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                
                self.cpu_cache[cache_key] = template
            
            # If GPU requested and available, upload to GPU
            if use_gpu and self._ocl_enabled:
                gpu_key = f"{cache_key}_gpu"
                if gpu_key not in self.gpu_cache:
                    try:
                        self.gpu_cache[gpu_key] = cv2.UMat(template)
                    except:
                        pass
                
                return self.gpu_cache.get(gpu_key, template)
            
            return template
    
    def clear_cache(self):
        """Clear all cached templates."""
        with self._lock:
            self.cpu_cache.clear()
            self.gpu_cache.clear()


# Global template cache
TEMPLATE_CACHE = TemplateCache()


class ImageFinder:
    # Class variable for motion detection
    _previous_screenshot = None
    _motion_detection_enabled = False
    
    # OPTIMIZATION: Result caching with TTL
    _result_cache = {}
    _cache_ttl = 0.2  # 200ms cache time
    _cache_last_cleanup = 0
    
    # OPTIMIZATION: ROI (Region of Interest) scanning
    _roi_regions = []  # List of (x1, y1, x2, y2) regions to scan
    _roi_enabled = False
    
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
        detection_mode: str = "cpu",
        shared_screenshot = None,
    ):
        """
        Find image on screen with different detection modes.
        
        Args:
            detection_mode: "cpu", "gpu", or "hybrid"
                - "cpu": CPU-only matching (most accurate)
                - "gpu": GPU-accelerated matching (faster, may have false positives)
                - "hybrid": GPU first, then CPU verification (fast + accurate)
            shared_screenshot: Pre-captured screenshot to share across multiple template searches
        """
        # Use template cache for faster loading (especially for GPU mode)
        use_gpu_cache = (detection_mode in ["gpu", "hybrid"])
        template = TEMPLATE_CACHE.get_template(image_path, resize_factor, use_gpu=use_gpu_cache)
        
        if template is None:
            print(f"[image_finder] Unable to read template: {image_path}")
            return [], None

        # Get template dimensions
        h, w = template.shape[:2] if not isinstance(template, cv2.UMat) else (template.get().shape[:2])

        # Use shared screenshot if provided, otherwise take a new one
        if shared_screenshot is not None:
            screenshot = shared_screenshot
        else:
            # Take a screenshot of the specified region
            screenshot = pyautogui.screenshot(region=(start_x, start_y, end_x - start_x, end_y - start_y))
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        image_name = os.path.basename(image_path)
        current_threshold = TEMPLATE_CATALOG.threshold_for(image_name, threshold)
        
        # Prepare for hybrid mode's verified_matches list
        verified_matches = []
        
        # Adjust threshold for GPU mode (higher for AMD GPUs to reduce false positives)
        if detection_mode == "gpu":
            # Use higher threshold for GPU to reduce false positives on older AMD GPUs
            gpu_threshold = max(current_threshold, 0.85)
        elif detection_mode == "hybrid":
            # Use slightly higher threshold for GPU pass, then verify with CPU
            gpu_threshold = max(current_threshold, 0.80)
        else:
            gpu_threshold = current_threshold

        # Ensure we have CPU version of template for processing
        template_cpu = template if not isinstance(template, cv2.UMat) else template.get()
        
        # Perform template matching based on mode
        if detection_mode == "cpu":
            # CPU mode - most accurate
            result = cv2.matchTemplate(screenshot, template_cpu, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= current_threshold)
            matches = list(zip(*locations[::-1]))
            
        elif detection_mode == "gpu":
            # INSANE GPU MODE - AMD Optimized for Maximum Accuracy + Speed
            try:
                # OPTIMIZATION 1: Minimal downscaling (0.9x) for better accuracy
                gpu_scale = 0.9  # Only 10% reduction, keeps most detail
                h_scaled = int(h * gpu_scale)
                w_scaled = int(w * gpu_scale)
                
                # OPTIMIZATION 2: Use INTER_CUBIC for superior quality
                template_scaled = cv2.resize(template_cpu, (w_scaled, h_scaled), 
                                           interpolation=cv2.INTER_CUBIC)
                screenshot_scaled = cv2.resize(screenshot, 
                                              (int(screenshot.shape[1] * gpu_scale), 
                                               int(screenshot.shape[0] * gpu_scale)),
                                              interpolation=cv2.INTER_CUBIC)
                
                # OPTIMIZATION 3: AMD GPU sharpening filter (compensates for GPU approximation)
                sharpen_kernel = np.array([[-1,-1,-1], 
                                          [-1, 9,-1], 
                                          [-1,-1,-1]], dtype=np.float32)
                screenshot_sharpened = cv2.filter2D(screenshot_scaled, -1, sharpen_kernel)
                template_sharpened = cv2.filter2D(template_scaled, -1, sharpen_kernel)
                
                # OPTIMIZATION 4: Upload to GPU
                screenshot_umat = cv2.UMat(screenshot_sharpened)
                template_umat = cv2.UMat(template_sharpened)
                
                # OPTIMIZATION 5: GPU template matching
                result_umat = cv2.matchTemplate(screenshot_umat, template_umat, cv2.TM_CCOEFF_NORMED)
                result_gpu = cv2.UMat.get(result_umat)
                
                # OPTIMIZATION 6: Get GPU candidates with lower threshold
                gpu_loose_threshold = max(current_threshold - 0.08, 0.70)
                locations_gpu = np.where(result_gpu >= gpu_loose_threshold)
                candidates_scaled = list(zip(*locations_gpu[::-1]))
                
                # OPTIMIZATION 7: Lightweight CPU post-processing for top candidates
                # Only verify top candidates (sorted by confidence)
                candidate_confidences = [result_gpu[y, x] for (x, y) in candidates_scaled]
                candidates_with_conf = list(zip(candidates_scaled, candidate_confidences))
                candidates_with_conf.sort(key=lambda x: x[1], reverse=True)  # Sort by confidence
                
                verified_matches = []
                
                # Quick CPU verification of top 100 candidates
                for ((x_scaled, y_scaled), conf) in candidates_with_conf[:100]:
                    # Scale back to full resolution
                    x = int(x_scaled / gpu_scale)
                    y = int(y_scaled / gpu_scale)
                    
                    # Extract small region around candidate for CPU verification
                    region_size = 25
                    x1 = max(0, x - region_size)
                    y1 = max(0, y - region_size)
                    x2 = min(screenshot.shape[1], x + w + region_size)
                    y2 = min(screenshot.shape[0], y + h + region_size)
                    
                    region = screenshot[y1:y2, x1:x2]
                    
                    # Quick CPU verification at full resolution
                    if region.size > 0 and region.shape[0] >= h and region.shape[1] >= w:
                        result_cpu = cv2.matchTemplate(region, template_cpu, cv2.TM_CCOEFF_NORMED)
                        max_val = np.max(result_cpu)
                        
                        # Verify with current threshold
                        if max_val >= current_threshold:
                            match_y, match_x = np.unravel_index(np.argmax(result_cpu), result_cpu.shape)
                            verified_matches.append((x1 + match_x, y1 + match_y))
                
                matches = verified_matches
                
            except Exception as e:
                print(f"[gpu_mode] GPU processing failed: {e}, falling back to CPU")
                # Fallback to CPU if GPU fails
                result = cv2.matchTemplate(screenshot, template_cpu, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= current_threshold)
                matches = list(zip(*locations[::-1]))
        
        elif detection_mode == "express":
            # EXPRESS MODE - Optimized for speed while maintaining good accuracy
            # Note: Will never be as accurate as Hybrid (no CPU verification)
            # For 100% accuracy, use Hybrid mode instead
            gpu_matches = []
            try:
                # Use 0.7x scale - better than 0.65 for speed, still reasonable accuracy
                express_scale = 0.7
                h_small = int(h * express_scale)
                w_small = int(w * express_scale)
                template_small = cv2.resize(template_cpu, (w_small, h_small), interpolation=cv2.INTER_LINEAR)
                screenshot_small = cv2.resize(screenshot, 
                                             (int(screenshot.shape[1] * express_scale), 
                                              int(screenshot.shape[0] * express_scale)),
                                             interpolation=cv2.INTER_LINEAR)
                
                # GPU-only detection
                screenshot_umat = cv2.UMat(screenshot_small)
                template_umat = cv2.UMat(template_small)
                result_umat = cv2.matchTemplate(screenshot_umat, template_umat, cv2.TM_CCOEFF_NORMED)
                result_gpu = cv2.UMat.get(result_umat)
                
                # Use slightly lower threshold than hybrid for better recall in express mode
                express_threshold = max(current_threshold - 0.03, 0.72)
                locations_gpu = np.where(result_gpu >= express_threshold)
                gpu_matches_small = list(zip(*locations_gpu[::-1]))
                
                # Scale coordinates back to full resolution
                matches = []
                for (x_small, y_small) in gpu_matches_small:
                    x = int(x_small / express_scale)
                    y = int(y_small / express_scale)
                    matches.append((x, y))
                
            except Exception as e:
                print(f"[express_mode] GPU failed: {e}, falling back to CPU")
                # Fallback to CPU if GPU fails
                result = cv2.matchTemplate(screenshot, template_cpu, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= current_threshold)
                matches = list(zip(*locations[::-1]))
                
        elif detection_mode == "hybrid":
            # OPTIMIZED Hybrid mode - GPU pyramid + batched parallel CPU verification
            gpu_matches = []
            gpu_confidences = []
            
            try:
                # Step 1: Template pyramid - downscale for faster GPU processing
                pyramid_scale = 0.65  # FIXED: Restored to 0.65 for better accuracy (0.5 was too aggressive)
                h_small = int(h * pyramid_scale)
                w_small = int(w * pyramid_scale)
                template_small = cv2.resize(template_cpu, (w_small, h_small), interpolation=cv2.INTER_AREA)
                screenshot_small = cv2.resize(screenshot, 
                                             (int(screenshot.shape[1] * pyramid_scale), 
                                              int(screenshot.shape[0] * pyramid_scale)),
                                             interpolation=cv2.INTER_AREA)
                
                # Step 2: GPU detection on downscaled images
                screenshot_umat = cv2.UMat(screenshot_small)
                template_umat = cv2.UMat(template_small)
                result_umat = cv2.matchTemplate(screenshot_umat, template_umat, cv2.TM_CCOEFF_NORMED)
                result_gpu = cv2.UMat.get(result_umat)
                
                # Get GPU candidates with confidences
                locations_gpu = np.where(result_gpu >= gpu_threshold)
                gpu_matches_small = list(zip(*locations_gpu[::-1]))
                
                # Scale coordinates back to full resolution
                for (x_small, y_small) in gpu_matches_small:
                    x = int(x_small / pyramid_scale)
                    y = int(y_small / pyramid_scale)
                    confidence = result_gpu[y_small, x_small]
                    
                    # Step 3: Smart candidate filtering - skip known stable detections
                    if DETECTION_HISTORY.is_known_detection(image_name, x, y, confidence, cooldown=0.3):
                        # This is a known stable detection, add directly without verification
                        verified_matches.append((x, y))
                        continue
                    
                    gpu_matches.append((x, y))
                    gpu_confidences.append(confidence)
                
            except Exception as e:
                print(f"[hybrid_mode] GPU pass failed: {e}, falling back to CPU")
                # If GPU fails, fall back to CPU
                result = cv2.matchTemplate(screenshot, template_cpu, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= current_threshold)
                matches = list(zip(*locations[::-1]))
            else:
                # Step 4: Batched parallel CPU verification (runs if GPU succeeded)
                if not gpu_matches:
                    # No new candidates to verify, use what we have
                    matches = verified_matches
                else:
                    # Prepare batch verification tasks
                    verification_tasks = []
                    for idx, ((x, y), confidence) in enumerate(zip(gpu_matches, gpu_confidences)):
                        verification_tasks.append((idx, x, y, confidence))
                    
                    # Parallel CPU verification with ThreadPoolExecutor
                    verified_matches_new = []
                    
                    def verify_candidate(task):
                        """Verify a single GPU candidate with CPU."""
                        idx, x, y, confidence = task
                        
                        # Extract region around GPU match for CPU verification
                        region_size = 50
                        x1 = max(0, x - region_size)
                        y1 = max(0, y - region_size)
                        x2 = min(screenshot.shape[1], x + w + region_size)
                        y2 = min(screenshot.shape[0], y + h + region_size)
                        
                        region = screenshot[y1:y2, x1:x2]
                        if region.size == 0:
                            return None
                        
                        # CPU verification
                        result_cpu = cv2.matchTemplate(region, template_cpu, cv2.TM_CCOEFF_NORMED)
                        max_val = np.max(result_cpu)
                        
                        if max_val >= current_threshold:
                            # Adjust coordinates back to full screenshot
                            match_y, match_x = np.unravel_index(np.argmax(result_cpu), result_cpu.shape)
                            final_x = x1 + match_x
                            final_y = y1 + match_y
                            
                            # Add to detection history
                            DETECTION_HISTORY.add_detection(image_name, final_x, final_y, max_val)
                            
                            return (final_x, final_y)
                        
                        return None
                    
                    # Process in parallel with 3 workers for optimal throughput
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        futures = [executor.submit(verify_candidate, task) for task in verification_tasks]
                        
                        for future in as_completed(futures):
                            result = future.result()
                            if result is not None:
                                verified_matches_new.append(result)
                    
                    # Combine verified matches with known stable ones
                    verified_matches.extend(verified_matches_new)
                    matches = verified_matches
                
                # Clean old history entries
                DETECTION_HISTORY.clear_old(max_age=3.0)
        else:
            # Default to CPU
            result = cv2.matchTemplate(screenshot, template_cpu, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= current_threshold)
            matches = list(zip(*locations[::-1]))

        # Calculate the center points of all matches and black out the matched areas
        # Use CPU template for dimensions
        h, w = template_cpu.shape[:2]
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
                if shared_screenshot is None:
                    screenshot[y:y + h, x:x + w] = 0  # 0 represents black in BGR

        # Adjust center points to screen coordinates
        screen_points = [(x + start_x, y + start_y) for (x, y) in center_points]

        return screen_points, screenshot  # Return both the points and the modified screenshot
    
    @staticmethod
    def find_multiple_images_parallel(
        template_paths: List[str],
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        resize_factor: float = 1,
        threshold: Optional[float] = None,
        max_workers: int = 2,  # Reduced to 2 for better accuracy
    ) -> Dict[str, List[Tuple[int, int]]]:
        """Find multiple images in parallel for faster detection."""
        results = {}
        
        # Take screenshot once (shared across all templates) for consistency
        screenshot = pyautogui.screenshot(region=(start_x, start_y, end_x - start_x, end_y - start_y))
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        def process_template(template_path: str):
            """Process a single template."""
            try:
                # Load template
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template is None:
                    return os.path.basename(template_path), []
                
                # Resize template
                h, w = template.shape[:2]
                new_h, new_w = int(h * resize_factor), int(w * resize_factor)
                template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                
                # Use the shared screenshot
                screenshot_copy = screenshot_cv.copy()
                
                # Perform template matching (CPU only for accuracy)
                result = cv2.matchTemplate(screenshot_copy, template, cv2.TM_CCOEFF_NORMED)
                
                # Find matches
                image_name = os.path.basename(template_path)
                current_threshold = TEMPLATE_CATALOG.threshold_for(image_name, threshold)
                locations = np.where(result >= current_threshold)
                matches = list(zip(*locations[::-1]))
                
                # Calculate center points
                h, w = template.shape[:2]
                center_points = []
                for (x, y) in matches:
                    overlaps = any(
                        abs(x - prev_x) < w and abs(y - prev_y) < h
                        for prev_x, prev_y in center_points
                    )
                    if not overlaps:
                        center_x = int(x + w / 2)
                        center_y = int(y + h / 2)
                        center_points.append((center_x, center_y))
                
                # Convert to screen coordinates
                screen_points = [(x + start_x, y + start_y) for (x, y) in center_points]
                return image_name, screen_points
            except Exception as e:
                print(f"[image_finder] Error processing {template_path}: {e}")
                return os.path.basename(template_path), []
        
        # Process templates in parallel (but with shared screenshot for consistency)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_template = {
                executor.submit(process_template, path): path 
                for path in template_paths
            }
            
            for future in as_completed(future_to_template):
                template_name, points = future.result()
                if points:
                    results[template_name] = points
        
        return results

    @staticmethod
    def get_template_metadata(template_name: str) -> Dict[str, object]:
        return TEMPLATE_CATALOG.metadata_for(template_name)
    
    @staticmethod
    def find_multiple_images_batched(
        template_paths: List[str],
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        resize_factor: float = 1,
        threshold: Optional[float] = None,
        detection_mode: str = "cpu",
        batch_size: int = 5,
        fast_mode: bool = False,
        enable_cache: bool = True,
    ) -> Dict[str, List[Tuple[int, int]]]:
        """
        OPTIMIZED: Find multiple images using shared screenshot and parallel batch processing.
        
        This is 5-10x faster than calling find_image_on_screen() for each template.
        
        Args:
            template_paths: List of template image paths to search for
            batch_size: Number of templates to process in parallel (2-8)
            fast_mode: If True, downscale screenshot to 0.8x for extra speed
            enable_cache: If False, forces a fresh scan even within the cache TTL window
        
        Returns:
            Dictionary mapping template names to lists of (x, y) center points
        """
        # OPTIMIZATION: Result caching with TTL (disabled for express mode or if explicitly disabled)
        current_time = time.time()
        cache_enabled = enable_cache and (detection_mode != "express")
        
        if cache_enabled:
            cache_key = f"{start_x}_{start_y}_{end_x}_{end_y}_{detection_mode}_{fast_mode}_{resize_factor}"
            
            if cache_key in ImageFinder._result_cache:
                cached_result, cached_time = ImageFinder._result_cache[cache_key]
                if current_time - cached_time < ImageFinder._cache_ttl:
                    print(f"[cache] Returning cached result (age: {current_time - cached_time:.2f}s)")
                    return cached_result  # Return cached result
            
            # Clean old cache entries every 5 seconds
            if current_time - ImageFinder._cache_last_cleanup > 5.0:
                ImageFinder._result_cache = {
                    k: v for k, v in ImageFinder._result_cache.items()
                    if current_time - v[1] < ImageFinder._cache_ttl * 2
                }
                ImageFinder._cache_last_cleanup = current_time
        
        # OPTIMIZATION 1: Take screenshot ONCE, share it across all templates
        screenshot = pyautogui.screenshot(region=(start_x, start_y, end_x - start_x, end_y - start_y))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # OPTIMIZATION: ROI (Region of Interest) scanning
        roi_offset_x, roi_offset_y = 0, 0
        if ImageFinder._roi_enabled and ImageFinder._roi_regions:
            # Extract and concatenate ROI regions
            roi_screenshots = []
            for roi in ImageFinder._roi_regions:
                rx1, ry1, rx2, ry2 = roi
                # Adjust ROI coordinates relative to screenshot
                local_x1 = max(0, rx1 - start_x)
                local_y1 = max(0, ry1 - start_y)
                local_x2 = min(screenshot.shape[1], rx2 - start_x)
                local_y2 = min(screenshot.shape[0], ry2 - start_y)
                
                if local_x2 > local_x1 and local_y2 > local_y1:
                    roi_shot = screenshot[local_y1:local_y2, local_x1:local_x2]
                    roi_screenshots.append(roi_shot)
            
            # Use ROI regions if any were extracted
            if roi_screenshots:
                screenshot = np.vstack(roi_screenshots)
                print(f"[roi] Scanning {len(roi_screenshots)} regions instead of full screen")
        
        # OPTIMIZATION 2: Motion detection - only scan changed regions (disabled for express mode)
        if ImageFinder._motion_detection_enabled and ImageFinder._previous_screenshot is not None and detection_mode != "express":
            # Calculate difference from previous frame
            diff = cv2.absdiff(screenshot, ImageFinder._previous_screenshot)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            changed_pixels = np.sum(gray_diff > 30)  # Threshold for motion
            total_pixels = gray_diff.size
            change_ratio = changed_pixels / total_pixels
            
            # If less than 5% of screen changed, skip scanning
            if change_ratio < 0.05:
                print(f"[motion_detection] Only {change_ratio*100:.1f}% changed, skipping scan")
                return {}
        
        # Store for next motion detection (only if not express mode)
        if detection_mode != "express":
            ImageFinder._previous_screenshot = screenshot.copy()
        
        # OPTIMIZATION 3: Fast mode - downscale screenshot
        if fast_mode:
            h, w = screenshot.shape[:2]
            screenshot = cv2.resize(screenshot, (int(w*0.8), int(h*0.8)), interpolation=cv2.INTER_AREA)
            # Adjust coordinates when returning results
            scale_factor = 0.8
        else:
            scale_factor = 1.0
        
        results = {}
        
        # OPTIMIZATION 4: Batch parallel processing
        def process_template(template_path: str):
            """Process a single template with shared screenshot."""
            try:
                points, _ = ImageFinder.find_image_on_screen(
                    template_path,
                    start_x, start_y, end_x, end_y,
                    resize_factor=resize_factor,
                    threshold=threshold,
                    detection_mode=detection_mode,
                    shared_screenshot=screenshot,  # Share the screenshot!
                )
                
                # Adjust coordinates if in fast mode
                if fast_mode and points:
                    points = [(int(x/scale_factor), int(y/scale_factor)) for (x, y) in points]
                
                template_name = os.path.basename(template_path)
                return template_name, points
            except Exception as e:
                print(f"[batch_process] Error processing {template_path}: {e}")
                return os.path.basename(template_path), []
        
        # Process templates in parallel batches
        # CRITICAL FIX: Wait for ALL futures to complete BEFORE processing ANY results
        # This ensures hybrid mode CPU verification completes for all templates
        # before any results are returned, preventing "two waves" of green boxes in overlay
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit all tasks
            future_to_path = {executor.submit(process_template, path): path for path in template_paths}
            
            # CRITICAL: Collect results only AFTER all futures complete
            # Store results temporarily, then process all at once to prevent "two waves"
            all_futures = list(future_to_path.keys())
            completed_results = []
            
            # Wait for all futures and collect their results (blocks until ALL complete)
            for future in all_futures:
                template_name, points = future.result()  # Blocks until this future completes
                completed_results.append((template_name, points))
            
            # NOW process all results together after ALL futures have completed
            # This ensures hybrid mode's GPU+CPU verification finishes for ALL templates
            # before any results are returned, preventing "two waves" in overlay
            for template_name, points in completed_results:
                if points:
                    results[template_name] = points
        
        # Cache the result (only if caching is enabled)
        if cache_enabled:
            ImageFinder._result_cache[cache_key] = (results, current_time)
        
        return results
    
    @staticmethod
    def enable_motion_detection(enabled: bool = True):
        """Enable or disable motion detection optimization."""
        ImageFinder._motion_detection_enabled = enabled
        if not enabled:
            ImageFinder._previous_screenshot = None
        print(f"[motion_detection] {'Enabled' if enabled else 'Disabled'}")
    
    @staticmethod
    def set_roi_regions(regions: List[Tuple[int, int, int, int]], enabled: bool = True):
        """Set Region of Interest (ROI) for scanning.
        
        Args:
            regions: List of (x1, y1, x2, y2) tuples defining regions to scan
            enabled: Whether to enable ROI scanning
        """
        ImageFinder._roi_regions = regions
        ImageFinder._roi_enabled = enabled
        if enabled and regions:
            print(f"[roi] Enabled with {len(regions)} region(s)")
        else:
            print("[roi] Disabled")
    
    @staticmethod
    def set_cache_ttl(ttl: float):
        """Set result cache TTL in seconds."""
        ImageFinder._cache_ttl = ttl
        print(f"[cache] TTL set to {ttl}s")
