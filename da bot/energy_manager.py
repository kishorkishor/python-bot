"""Energy Management System for Farm Merge Valley.

Monitors energy levels, pauses energy-intensive tasks when low,
and tracks energy regeneration timing.
"""

import time
import re
from typing import Optional, Tuple, Dict

import cv2
import numpy as np
from pyautogui_safe import pyautogui


class EnergyManager:
    """
    Manages energy resource monitoring and task scheduling.
    
    Uses OCR to read energy levels and pauses/resumes tasks
    based on energy availability.
    """
    
    def __init__(self, energy_region: Optional[Tuple[int, int, int, int]] = None):
        self.energy_region = energy_region
        self.current_energy = None
        self.max_energy = None
        self.last_read_time = 0
        self.read_interval = 10  # Seconds between energy reads
        
        # Energy tracking
        self.energy_history = []  # (timestamp, energy_level)
        self.regeneration_rate = 1.0  # Energy per minute (estimated)
        
        # Configuration
        self.config = {
            'low_energy_threshold': 20,
            'pause_threshold': 10,
            'resume_threshold': 30,
            'auto_pause': True,
            'track_regeneration': True,
        }
        
        # State
        self.tasks_paused = False
        self.pause_reason = ""
        
        # Check for Tesseract
        self.ocr_available = self._check_ocr_availability()
    
    def _check_ocr_availability(self) -> bool:
        """Check if Tesseract OCR is available."""
        try:
            import pytesseract
            # Try a simple test
            pytesseract.get_tesseract_version()
            return True
        except (ImportError, Exception):
            print("[EnergyManager] Warning: Tesseract OCR not available. Energy reading disabled.")
            return False
    
    def set_energy_region(self, region: Tuple[int, int, int, int]):
        """
        Set the screen region containing energy display.
        
        Args:
            region: (x, y, width, height) of energy display
        """
        self.energy_region = region
    
    def can_read_energy(self) -> bool:
        """Check if energy reading is ready."""
        if not self.ocr_available or not self.energy_region:
            return False
        
        elapsed = time.time() - self.last_read_time
        return elapsed >= self.read_interval
    
    def read_energy_level(self) -> Optional[int]:
        """
        Read current energy level from screen using OCR.
        
        Returns:
            Energy level as integer, or None if reading fails
        """
        if not self.can_read_energy():
            return self.current_energy  # Return cached value
        
        try:
            import pytesseract
            
            # Capture energy region
            screenshot = pyautogui.screenshot(region=self.energy_region)
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            
            # Preprocess for better OCR accuracy
            frame = cv2.resize(frame, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            frame = cv2.GaussianBlur(frame, (3, 3), 0)
            
            # Try both thresholding methods
            _, thresh1 = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            _, thresh2 = cv2.threshold(frame, 127, 255, cv2.THRESH_BINARY)
            
            # Extract text from both
            text1 = pytesseract.image_to_string(thresh1, config='--psm 7 digits')
            text2 = pytesseract.image_to_string(thresh2, config='--psm 7 digits')
            
            # Parse numbers
            numbers1 = re.findall(r'\d+', text1)
            numbers2 = re.findall(r'\d+', text2)
            
            # Try to extract energy value
            energy_value = None
            
            if numbers1:
                energy_value = int(numbers1[0])
            elif numbers2:
                energy_value = int(numbers2[0])
            
            if energy_value is not None:
                self.current_energy = energy_value
                self.last_read_time = time.time()
                
                # Track history
                if self.config['track_regeneration']:
                    self.energy_history.append((time.time(), energy_value))
                    self._update_regeneration_rate()
                
                return energy_value
        
        except Exception as e:
            print(f"[EnergyManager] Failed to read energy: {e}")
        
        return None
    
    def _update_regeneration_rate(self):
        """Calculate energy regeneration rate from history."""
        if len(self.energy_history) < 2:
            return
        
        # Keep last 10 readings
        if len(self.energy_history) > 10:
            self.energy_history = self.energy_history[-10:]
        
        # Calculate rate from first and last readings
        first_time, first_energy = self.energy_history[0]
        last_time, last_energy = self.energy_history[-1]
        
        time_diff = (last_time - first_time) / 60  # Minutes
        energy_diff = last_energy - first_energy
        
        if time_diff > 0 and energy_diff > 0:
            self.regeneration_rate = energy_diff / time_diff
    
    def has_sufficient_energy(self, required: Optional[int] = None) -> bool:
        """
        Check if current energy is sufficient.
        
        Args:
            required: Specific energy requirement (uses threshold if None)
            
        Returns:
            True if energy is sufficient
        """
        if self.current_energy is None:
            return True  # Assume OK if we can't read it
        
        threshold = required if required is not None else self.config['low_energy_threshold']
        return self.current_energy >= threshold
    
    def should_pause_tasks(self) -> bool:
        """
        Determine if tasks should be paused due to low energy.
        
        Returns:
            True if tasks should pause
        """
        if not self.config['auto_pause']:
            return False
        
        if self.current_energy is None:
            return False
        
        return self.current_energy <= self.config['pause_threshold']
    
    def should_resume_tasks(self) -> bool:
        """
        Determine if paused tasks can resume.
        
        Returns:
            True if tasks can resume
        """
        if not self.tasks_paused:
            return False
        
        if self.current_energy is None:
            return True  # Resume if we can't read energy
        
        return self.current_energy >= self.config['resume_threshold']
    
    def pause_tasks(self, reason: str = "Low energy"):
        """
        Pause energy-intensive tasks.
        
        Args:
            reason: Reason for pausing
        """
        if not self.tasks_paused:
            self.tasks_paused = True
            self.pause_reason = reason
            print(f"[EnergyManager] ⏸ Tasks paused: {reason} (Energy: {self.current_energy})")
    
    def resume_tasks(self):
        """Resume paused tasks."""
        if self.tasks_paused:
            self.tasks_paused = False
            print(f"[EnergyManager] ▶ Tasks resumed (Energy: {self.current_energy})")
    
    def update(self) -> Dict:
        """
        Update energy state and manage task pausing.
        
        Returns:
            Status dictionary
        """
        # Read energy level
        energy = self.read_energy_level()
        
        # Check if we should pause
        if self.should_pause_tasks():
            self.pause_tasks("Energy below pause threshold")
        
        # Check if we can resume
        elif self.should_resume_tasks():
            self.resume_tasks()
        
        return {
            'energy': self.current_energy,
            'tasks_paused': self.tasks_paused,
            'pause_reason': self.pause_reason,
            'regeneration_rate': self.regeneration_rate
        }
    
    def estimate_time_to_energy(self, target_energy: int) -> Optional[float]:
        """
        Estimate time (minutes) until reaching target energy.
        
        Args:
            target_energy: Target energy level
            
        Returns:
            Estimated minutes, or None if calculation not possible
        """
        if self.current_energy is None or self.regeneration_rate <= 0:
            return None
        
        if self.current_energy >= target_energy:
            return 0.0
        
        energy_needed = target_energy - self.current_energy
        return energy_needed / self.regeneration_rate
    
    def get_statistics(self) -> Dict:
        """
        Get energy management statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            'current_energy': self.current_energy,
            'max_energy': self.max_energy,
            'tasks_paused': self.tasks_paused,
            'pause_reason': self.pause_reason,
            'regeneration_rate': round(self.regeneration_rate, 2),
            'history_length': len(self.energy_history),
            'ocr_available': self.ocr_available
        }
    
    def update_config(self, new_config: Dict):
        """
        Update energy manager configuration.
        
        Args:
            new_config: Dictionary of config updates
        """
        self.config.update(new_config)
    
    def reset(self):
        """Reset energy tracking."""
        self.energy_history.clear()
        self.tasks_paused = False
        self.pause_reason = ""


class SmartEnergyManager(EnergyManager):
    """
    Enhanced energy manager with predictive scheduling.
    
    Predicts energy availability and schedules tasks accordingly.
    """
    
    def __init__(self, energy_region: Optional[Tuple[int, int, int, int]] = None):
        super().__init__(energy_region)
        self.task_energy_costs = {
            'expand_land': 50,
            'clear_obstacle': 30,
            'repair_building': 20,
            'collect_resources': 0,
            'merge_items': 0,
        }
    
    def can_afford_task(self, task_name: str) -> bool:
        """
        Check if we have enough energy for a task.
        
        Args:
            task_name: Name of task to check
            
        Returns:
            True if task is affordable
        """
        if self.current_energy is None:
            return True
        
        cost = self.task_energy_costs.get(task_name, 0)
        return self.current_energy >= cost
    
    def schedule_task(self, task_name: str) -> Dict:
        """
        Schedule a task based on energy availability.
        
        Args:
            task_name: Name of task to schedule
            
        Returns:
            Scheduling result
        """
        cost = self.task_energy_costs.get(task_name, 0)
        
        if cost == 0:
            return {
                'can_execute': True,
                'reason': 'No energy cost',
                'wait_time': 0
            }
        
        if self.current_energy is None:
            return {
                'can_execute': True,
                'reason': 'Energy unknown',
                'wait_time': 0
            }
        
        if self.current_energy >= cost:
            return {
                'can_execute': True,
                'reason': 'Sufficient energy',
                'wait_time': 0
            }
        
        # Calculate wait time
        wait_time = self.estimate_time_to_energy(cost)
        
        return {
            'can_execute': False,
            'reason': f'Insufficient energy (need {cost}, have {self.current_energy})',
            'wait_time': wait_time
        }
    
    def set_task_cost(self, task_name: str, cost: int):
        """
        Set energy cost for a task.
        
        Args:
            task_name: Task name
            cost: Energy cost
        """
        self.task_energy_costs[task_name] = cost
    
    def get_affordable_tasks(self) -> list:
        """
        Get list of tasks that can be executed with current energy.
        
        Returns:
            List of task names
        """
        if self.current_energy is None:
            return list(self.task_energy_costs.keys())
        
        return [
            task for task, cost in self.task_energy_costs.items()
            if self.current_energy >= cost
        ]



