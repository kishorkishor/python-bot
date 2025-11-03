"""Pop-up Handler for Farm Merge Valley.

Detects and dismisses various game pop-ups and modal dialogs
to keep automation running smoothly.
"""

import time
import random
from typing import Dict, List, Tuple, Optional

import pyautogui

from game_state_detector import GameStateDetector


class PopupHandler:
    """
    Handles detection and dismissal of game pop-ups.
    
    Manages level-up screens, warnings, ads, daily bonuses,
    and tutorial prompts.
    """
    
    def __init__(self, game_state_detector: GameStateDetector):
        self.detector = game_state_detector
        self.popups_handled = 0
        self.popup_history = []  # (timestamp, popup_type)
        self.last_check_time = 0
        self.check_interval = 5  # Seconds between popup checks
        
        # Configuration
        self.config = {
            'auto_dismiss': True,
            'claim_rewards': True,
            'skip_ads': True,
            'dismiss_tutorials': True,
            'click_delay': 0.5,
        }
        
        # Popup button positions (relative to popup)
        self.button_offsets = {
            'close_x': (0.9, 0.1),      # Top-right X button
            'ok_button': (0.5, 0.7),     # Center-bottom OK
            'claim_button': (0.5, 0.7),  # Center-bottom Claim
            'skip_button': (0.9, 0.1),   # Top-right Skip
        }
    
    def can_check_popups(self) -> bool:
        """Check if popup check cooldown has elapsed."""
        elapsed = time.time() - self.last_check_time
        return elapsed >= self.check_interval
    
    def check_and_handle_popups(
        self,
        game_area: Tuple[int, int, int, int],
        threshold: float = 0.75
    ) -> Dict:
        """
        Check for and handle any active popups.
        
        Args:
            game_area: Full game screen region
            threshold: Detection confidence threshold
            
        Returns:
            Result dictionary with popup info
        """
        if not self.can_check_popups():
            return {
                'success': False,
                'reason': 'On cooldown',
                'popup_found': False
            }
        
        # Detect popup
        popup = self.detector.detect_popup(game_area, threshold=threshold)
        
        self.last_check_time = time.time()
        
        if not popup:
            return {
                'success': True,
                'popup_found': False
            }
        
        # Handle the popup
        if self.config['auto_dismiss']:
            success = self._handle_popup(popup)
            
            if success:
                self.popups_handled += 1
                self.popup_history.append((time.time(), popup['type']))
                
                return {
                    'success': True,
                    'popup_found': True,
                    'popup_type': popup['type'],
                    'dismissed': True
                }
        
        return {
            'success': True,
            'popup_found': True,
            'popup_type': popup['type'],
            'dismissed': False
        }
    
    def _handle_popup(self, popup: Dict) -> bool:
        """
        Handle a specific popup type.
        
        Args:
            popup: Popup info from detector
            
        Returns:
            True if successfully handled
        """
        popup_type = popup['type']
        
        # Route to specific handler
        handlers = {
            'levelup': self._handle_levelup,
            'daily_reward': self._handle_daily_reward,
            'not_enough_energy': self._handle_energy_warning,
            'tutorial': self._handle_tutorial,
        }
        
        handler = handlers.get(popup_type, self._handle_generic)
        return handler(popup)
    
    def _handle_levelup(self, popup: Dict) -> bool:
        """Handle level-up popup (claim rewards and dismiss)."""
        print("[PopupHandler] Handling level-up popup...")
        
        # Try to click claim button first
        if self.config['claim_rewards']:
            dismiss_pos = popup.get('dismiss_button')
            if dismiss_pos:
                self._click_position(dismiss_pos)
                time.sleep(self.config['click_delay'])
                return True
        
        # Fallback: click center of popup
        popup_pos = popup['position']
        self._click_position(popup_pos)
        return True
    
    def _handle_daily_reward(self, popup: Dict) -> bool:
        """Handle daily reward popup (claim and dismiss)."""
        print("[PopupHandler] Handling daily reward popup...")
        
        if self.config['claim_rewards']:
            dismiss_pos = popup.get('dismiss_button')
            if dismiss_pos:
                self._click_position(dismiss_pos)
                time.sleep(self.config['click_delay'])
                return True
        
        return False
    
    def _handle_energy_warning(self, popup: Dict) -> bool:
        """Handle 'not enough energy' warning (dismiss)."""
        print("[PopupHandler] Handling energy warning...")
        
        dismiss_pos = popup.get('dismiss_button')
        if dismiss_pos:
            self._click_position(dismiss_pos)
            return True
        
        # Try ESC key
        pyautogui.press('escape')
        return True
    
    def _handle_tutorial(self, popup: Dict) -> bool:
        """Handle tutorial popup (skip/dismiss)."""
        print("[PopupHandler] Handling tutorial popup...")
        
        if self.config['dismiss_tutorials']:
            dismiss_pos = popup.get('dismiss_button')
            if dismiss_pos:
                self._click_position(dismiss_pos)
                return True
            
            # Try ESC key
            pyautogui.press('escape')
            return True
        
        return False
    
    def _handle_generic(self, popup: Dict) -> bool:
        """Handle unknown popup type (generic dismiss)."""
        print(f"[PopupHandler] Handling unknown popup: {popup['type']}")
        
        dismiss_pos = popup.get('dismiss_button')
        if dismiss_pos:
            self._click_position(dismiss_pos)
            return True
        
        # Try ESC key
        pyautogui.press('escape')
        return True
    
    def _click_position(self, position: Tuple[int, int]) -> bool:
        """
        Click at a specific position with randomness.
        
        Args:
            position: (x, y) to click
            
        Returns:
            True if click succeeded
        """
        try:
            x, y = position
            
            # Add slight randomness
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            
            target_x = x + offset_x
            target_y = y + offset_y
            
            # Move and click
            pyautogui.moveTo(target_x, target_y, duration=0.2)
            pyautogui.click()
            
            return True
        
        except Exception as e:
            print(f"[PopupHandler] Failed to click: {e}")
            return False
    
    def handle_specific_popup(self, popup_type: str, game_area: Tuple[int, int, int, int]) -> bool:
        """
        Look for and handle a specific popup type.
        
        Args:
            popup_type: Type of popup to handle
            game_area: Game screen region
            
        Returns:
            True if popup was found and handled
        """
        popup = self.detector.detect_popup(
            game_area,
            popup_types=[popup_type]
        )
        
        if popup:
            return self._handle_popup(popup)
        
        return False
    
    def get_statistics(self) -> Dict:
        """
        Get popup handling statistics.
        
        Returns:
            Dictionary of stats
        """
        # Count by type
        type_counts = {}
        for _, popup_type in self.popup_history:
            type_counts[popup_type] = type_counts.get(popup_type, 0) + 1
        
        return {
            'total_popups_handled': self.popups_handled,
            'by_type': type_counts,
            'history_length': len(self.popup_history)
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.popups_handled = 0
        self.popup_history.clear()
    
    def update_config(self, new_config: Dict):
        """
        Update popup handler configuration.
        
        Args:
            new_config: Dictionary of config updates
        """
        self.config.update(new_config)


class SmartPopupHandler(PopupHandler):
    """
    Enhanced popup handler with learning capabilities.
    
    Learns popup patterns and optimizes detection/handling.
    """
    
    def __init__(self, game_state_detector: GameStateDetector):
        super().__init__(game_state_detector)
        self.popup_frequencies = {}  # Track how often each popup appears
        self.last_popup_time = {}    # Track when each popup last appeared
    
    def check_and_handle_popups(
        self,
        game_area: Tuple[int, int, int, int],
        threshold: float = 0.75
    ) -> Dict:
        """Enhanced popup checking with priority based on frequency."""
        result = super().check_and_handle_popups(game_area, threshold)
        
        if result.get('popup_found') and result.get('popup_type'):
            popup_type = result['popup_type']
            
            # Update frequency tracking
            self.popup_frequencies[popup_type] = \
                self.popup_frequencies.get(popup_type, 0) + 1
            
            self.last_popup_time[popup_type] = time.time()
        
        return result
    
    def get_priority_popup_types(self) -> List[str]:
        """
        Get popup types sorted by frequency (most common first).
        
        Returns:
            List of popup types
        """
        if not self.popup_frequencies:
            return []
        
        return sorted(
            self.popup_frequencies.keys(),
            key=lambda t: self.popup_frequencies[t],
            reverse=True
        )
    
    def predict_next_popup(self) -> Optional[str]:
        """
        Predict which popup is most likely to appear next.
        
        Returns:
            Popup type prediction, or None
        """
        if not self.popup_frequencies:
            return None
        
        # Return most frequent popup
        priority_types = self.get_priority_popup_types()
        return priority_types[0] if priority_types else None
    
    def get_popup_interval(self, popup_type: str) -> Optional[float]:
        """
        Get average interval between appearances of a popup type.
        
        Args:
            popup_type: Popup type to check
            
        Returns:
            Average interval in seconds, or None
        """
        # Filter history for this type
        type_history = [
            timestamp for timestamp, ptype in self.popup_history
            if ptype == popup_type
        ]
        
        if len(type_history) < 2:
            return None
        
        # Calculate average interval
        intervals = []
        for i in range(1, len(type_history)):
            interval = type_history[i] - type_history[i-1]
            intervals.append(interval)
        
        return sum(intervals) / len(intervals) if intervals else None



