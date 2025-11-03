"""Game State Detection System for Farm Merge Valley.

Detects multiple game elements beyond merge items:
- Producer ready indicators (animals/crops with goods)
- Order board elements (customer requests)
- UI buttons (collect, claim, expand, repair)
- Resource displays (coins, energy, materials)
- Pop-ups and modal dialogs
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pyautogui

from item_finder import ImageFinder, TEMPLATE_CATALOG


class GameStateDetector:
    """Detects various game state elements using template matching."""
    
    def __init__(self, base_path: str = "./img"):
        self.base_path = Path(base_path)
        self.ui_elements_path = self.base_path / "ui_elements"
        self.producers_path = self.base_path / "producers"
        self.orders_path = self.base_path / "orders"
        
        # Ensure directories exist
        self.ui_elements_path.mkdir(exist_ok=True)
        self.producers_path.mkdir(exist_ok=True)
        self.orders_path.mkdir(exist_ok=True)
        
        self.image_finder = ImageFinder()
    
    def detect_producers_ready(
        self, 
        area: Tuple[int, int, int, int],
        resize_factor: float = 1.0,
        threshold: float = 0.75
    ) -> List[Dict]:
        """
        Detect producers (animals/crops) showing ready indicators.
        
        Args:
            area: Screen region (start_x, start_y, end_x, end_y)
            resize_factor: Scale factor for templates
            threshold: Detection confidence threshold
            
        Returns:
            List of detected producers with positions and types
        """
        if not self.producers_path.exists():
            return []
        
        producers = []
        template_files = list(self.producers_path.glob("*.png"))
        
        for template_path in template_files:
            points, _ = ImageFinder.find_image_on_screen(
                str(template_path),
                area[0], area[1], area[2], area[3],
                resize_factor,
                threshold
            )
            
            if points:
                producer_name = template_path.stem
                for point in points:
                    producers.append({
                        'type': producer_name,
                        'position': point,
                        'template': str(template_path),
                        'state': 'ready'
                    })
        
        return producers
    
    def detect_active_orders(
        self,
        order_board_region: Tuple[int, int, int, int],
        resize_factor: float = 1.0,
        threshold: float = 0.70
    ) -> List[Dict]:
        """
        Detect active orders on the order board.
        
        Args:
            order_board_region: Order board screen region
            resize_factor: Scale factor for templates
            threshold: Detection confidence threshold
            
        Returns:
            List of detected orders with required items
        """
        if not self.orders_path.exists():
            return []
        
        orders = []
        template_files = list(self.orders_path.glob("*.png"))
        
        # Group detections by vertical position (same order)
        all_detections = []
        
        for template_path in template_files:
            points, _ = ImageFinder.find_image_on_screen(
                str(template_path),
                order_board_region[0], order_board_region[1],
                order_board_region[2], order_board_region[3],
                resize_factor,
                threshold
            )
            
            if points:
                item_name = template_path.stem.replace("order_", "")
                for point in points:
                    all_detections.append({
                        'item': item_name,
                        'position': point,
                        'y': point[1]
                    })
        
        # Group by Y position (orders are horizontal)
        if all_detections:
            all_detections.sort(key=lambda x: x['y'])
            
            current_order = []
            last_y = all_detections[0]['y']
            
            for detection in all_detections:
                if abs(detection['y'] - last_y) < 50:  # Same order
                    current_order.append(detection['item'])
                else:
                    if current_order:
                        orders.append({
                            'items': current_order,
                            'position': (detection['position'][0], last_y)
                        })
                    current_order = [detection['item']]
                    last_y = detection['y']
            
            if current_order:
                orders.append({
                    'items': current_order,
                    'position': (all_detections[-1]['position'][0], last_y)
                })
        
        return orders
    
    def detect_ui_elements(
        self,
        area: Tuple[int, int, int, int],
        element_types: Optional[List[str]] = None,
        resize_factor: float = 1.0,
        threshold: float = 0.80
    ) -> Dict[str, List[Tuple[int, int]]]:
        """
        Detect UI elements (buttons, icons).
        
        Args:
            area: Screen region to search
            element_types: Specific elements to detect (None = all)
            resize_factor: Scale factor for templates
            threshold: Detection confidence threshold
            
        Returns:
            Dictionary mapping element types to positions
        """
        if not self.ui_elements_path.exists():
            return {}
        
        elements = {}
        template_files = list(self.ui_elements_path.glob("*.png"))
        
        for template_path in template_files:
            element_name = template_path.stem
            
            # Filter by requested types
            if element_types and element_name not in element_types:
                continue
            
            points, _ = ImageFinder.find_image_on_screen(
                str(template_path),
                area[0], area[1], area[2], area[3],
                resize_factor,
                threshold
            )
            
            if points:
                elements[element_name] = points
        
        return elements
    
    def detect_energy_level(
        self,
        energy_region: Tuple[int, int, int, int]
    ) -> Optional[int]:
        """
        Detect current energy level using OCR.
        
        Args:
            energy_region: Screen region containing energy display
            
        Returns:
            Energy level as integer, or None if detection fails
        """
        try:
            import pytesseract
            
            # Capture energy region
            screenshot = pyautogui.screenshot(region=energy_region)
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            
            # Preprocess for OCR
            frame = cv2.resize(frame, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            frame = cv2.GaussianBlur(frame, (3, 3), 0)
            _, thresh = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Extract number
            text = pytesseract.image_to_string(thresh, config='--psm 7 digits')
            
            # Parse first number found
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
        
        except (ImportError, Exception):
            pass
        
        return None
    
    def detect_coin_count(
        self,
        coin_region: Tuple[int, int, int, int]
    ) -> Optional[int]:
        """
        Detect current coin count using OCR.
        
        Args:
            coin_region: Screen region containing coin display
            
        Returns:
            Coin count as integer, or None if detection fails
        """
        try:
            import pytesseract
            
            # Capture coin region
            screenshot = pyautogui.screenshot(region=coin_region)
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            
            # Preprocess for OCR
            frame = cv2.resize(frame, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            frame = cv2.GaussianBlur(frame, (3, 3), 0)
            _, thresh = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Extract number
            text = pytesseract.image_to_string(thresh, config='--psm 7')
            
            # Parse number (may have commas)
            import re
            text = text.replace(',', '').replace('.', '')
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
        
        except (ImportError, Exception):
            pass
        
        return None
    
    def detect_popup(
        self,
        full_screen_area: Tuple[int, int, int, int],
        popup_types: Optional[List[str]] = None,
        threshold: float = 0.75
    ) -> Optional[Dict]:
        """
        Detect if a popup/modal is present.
        
        Args:
            full_screen_area: Full game screen region
            popup_types: Specific popup types to detect
            threshold: Detection confidence
            
        Returns:
            Popup info with type and dismiss button position, or None
        """
        popup_templates = {
            'levelup': 'levelup_popup.png',
            'daily_reward': 'daily_reward.png',
            'not_enough_energy': 'not_enough_energy.png',
            'tutorial': 'tutorial_overlay.png'
        }
        
        for popup_type, template_name in popup_templates.items():
            if popup_types and popup_type not in popup_types:
                continue
            
            template_path = self.ui_elements_path / template_name
            if not template_path.exists():
                continue
            
            points, _ = ImageFinder.find_image_on_screen(
                str(template_path),
                full_screen_area[0], full_screen_area[1],
                full_screen_area[2], full_screen_area[3],
                1.0,
                threshold
            )
            
            if points:
                # Try to find dismiss button near popup
                dismiss_buttons = self.detect_ui_elements(
                    full_screen_area,
                    element_types=['close_button', 'ok_button', 'claim_button'],
                    threshold=0.80
                )
                
                dismiss_position = None
                if dismiss_buttons:
                    # Get closest dismiss button to popup
                    popup_pos = points[0]
                    for button_type, positions in dismiss_buttons.items():
                        if positions:
                            dismiss_position = positions[0]
                            break
                
                return {
                    'type': popup_type,
                    'position': points[0],
                    'dismiss_button': dismiss_position
                }
        
        return None
    
    def get_game_state_summary(
        self,
        game_area: Tuple[int, int, int, int],
        order_board_region: Optional[Tuple[int, int, int, int]] = None,
        energy_region: Optional[Tuple[int, int, int, int]] = None,
        coin_region: Optional[Tuple[int, int, int, int]] = None,
        resize_factor: float = 1.0
    ) -> Dict:
        """
        Get comprehensive game state snapshot.
        
        Args:
            game_area: Main game screen region
            order_board_region: Order board region (if configured)
            energy_region: Energy display region (if configured)
            coin_region: Coin display region (if configured)
            resize_factor: Template scale factor
            
        Returns:
            Dictionary with all detected game state information
        """
        state = {
            'producers_ready': [],
            'active_orders': [],
            'ui_elements': {},
            'energy': None,
            'coins': None,
            'popup': None
        }
        
        # Detect producers
        state['producers_ready'] = self.detect_producers_ready(
            game_area, resize_factor
        )
        
        # Detect orders
        if order_board_region:
            state['active_orders'] = self.detect_active_orders(
                order_board_region, resize_factor
            )
        
        # Detect UI elements
        state['ui_elements'] = self.detect_ui_elements(
            game_area, resize_factor=resize_factor
        )
        
        # Read energy
        if energy_region:
            state['energy'] = self.detect_energy_level(energy_region)
        
        # Read coins
        if coin_region:
            state['coins'] = self.detect_coin_count(coin_region)
        
        # Check for popups
        state['popup'] = self.detect_popup(game_area)
        
        return state



