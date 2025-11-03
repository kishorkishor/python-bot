"""Navigation System for Farm Merge Valley.

Handles menu navigation, screen detection, and camera
panning for large farms.
"""

import time
import random
from typing import Dict, List, Tuple, Optional
from enum import Enum, auto

import pyautogui

from game_state_detector import GameStateDetector


class GameScreen(Enum):
    """Possible game screens."""
    FARM_VIEW = auto()
    ORDER_BOARD = auto()
    SHOP = auto()
    SETTINGS = auto()
    INVENTORY = auto()
    MAP = auto()
    UNKNOWN = auto()


class Navigator:
    """
    Manages navigation between game screens and menus.
    
    Detects current screen, navigates to target screens,
    and handles camera panning.
    """
    
    def __init__(self, game_state_detector: GameStateDetector):
        self.detector = game_state_detector
        self.current_screen = GameScreen.UNKNOWN
        self.last_navigation = 0
        self.navigation_cooldown = 2  # Seconds between navigations
        
        # Configuration
        self.config = {
            'auto_return_to_farm': True,
            'return_delay': 30,  # Seconds before auto-return
            'click_delay': 0.5,
            'pan_speed': 1.0,
        }
        
        # Tracking
        self.navigation_history = []  # (timestamp, from_screen, to_screen)
        self.last_farm_visit = time.time()
        
        # Screen detection templates (positions of unique UI elements)
        self.screen_indicators = {
            GameScreen.FARM_VIEW: ['farm_ui', 'merge_board'],
            GameScreen.ORDER_BOARD: ['order_list', 'customer_icon'],
            GameScreen.SHOP: ['shop_tab', 'buy_button'],
            GameScreen.SETTINGS: ['settings_icon', 'volume_slider'],
            GameScreen.INVENTORY: ['inventory_grid', 'item_count'],
        }
    
    def can_navigate(self) -> bool:
        """Check if navigation cooldown has elapsed."""
        elapsed = time.time() - self.last_navigation
        return elapsed >= self.navigation_cooldown
    
    def detect_current_screen(
        self,
        game_area: Tuple[int, int, int, int],
        threshold: float = 0.75
    ) -> GameScreen:
        """
        Detect which screen we're currently on.
        
        Args:
            game_area: Game screen region
            threshold: Detection confidence threshold
            
        Returns:
            Detected screen
        """
        # Detect all UI elements
        ui_elements = self.detector.detect_ui_elements(
            game_area,
            threshold=threshold
        )
        
        detected_elements = set(ui_elements.keys())
        
        # Match against screen indicators
        best_match = GameScreen.UNKNOWN
        best_match_count = 0
        
        for screen, indicators in self.screen_indicators.items():
            match_count = len(detected_elements.intersection(indicators))
            
            if match_count > best_match_count:
                best_match = screen
                best_match_count = match_count
        
        self.current_screen = best_match
        return best_match
    
    def navigate_to(
        self,
        target_screen: GameScreen,
        game_area: Tuple[int, int, int, int]
    ) -> Dict:
        """
        Navigate to a target screen.
        
        Args:
            target_screen: Screen to navigate to
            game_area: Game screen region
            
        Returns:
            Navigation result
        """
        if not self.can_navigate():
            return {
                'success': False,
                'reason': 'On cooldown',
                'navigated': False
            }
        
        # Detect current screen
        current = self.detect_current_screen(game_area)
        
        if current == target_screen:
            return {
                'success': True,
                'reason': 'Already on target screen',
                'navigated': False
            }
        
        # Execute navigation
        success = self._execute_navigation(current, target_screen, game_area)
        
        if success:
            self.navigation_history.append({
                'timestamp': time.time(),
                'from': current,
                'to': target_screen
            })
            
            self.current_screen = target_screen
            self.last_navigation = time.time()
            
            if target_screen == GameScreen.FARM_VIEW:
                self.last_farm_visit = time.time()
            
            print(f"[Navigator] Navigated from {current.name} to {target_screen.name}")
            
            return {
                'success': True,
                'navigated': True,
                'from': current,
                'to': target_screen
            }
        
        return {
            'success': False,
            'reason': 'Navigation failed',
            'navigated': False
        }
    
    def _execute_navigation(
        self,
        from_screen: GameScreen,
        to_screen: GameScreen,
        game_area: Tuple[int, int, int, int]
    ) -> bool:
        """
        Execute the actual navigation between screens.
        
        Args:
            from_screen: Current screen
            to_screen: Target screen
            game_area: Game screen region
            
        Returns:
            True if navigation succeeded
        """
        # Navigation button mapping
        navigation_buttons = {
            GameScreen.FARM_VIEW: 'home_button',
            GameScreen.ORDER_BOARD: 'orders_button',
            GameScreen.SHOP: 'shop_button',
            GameScreen.SETTINGS: 'settings_button',
            GameScreen.INVENTORY: 'inventory_button',
        }
        
        target_button = navigation_buttons.get(to_screen)
        
        if not target_button:
            return False
        
        # First, return to farm view if we're in a nested screen
        if from_screen not in [GameScreen.FARM_VIEW, GameScreen.UNKNOWN]:
            if to_screen != GameScreen.FARM_VIEW:
                # Go to farm first, then to target
                self._click_back_button(game_area)
                time.sleep(self.config['click_delay'])
        
        # Detect and click target button
        ui_elements = self.detector.detect_ui_elements(
            game_area,
            element_types=[target_button],
            threshold=0.80
        )
        
        if target_button in ui_elements and ui_elements[target_button]:
            position = ui_elements[target_button][0]
            return self._click_position(position)
        
        return False
    
    def _click_back_button(self, game_area: Tuple[int, int, int, int]) -> bool:
        """
        Click the back button to return to previous screen.
        
        Args:
            game_area: Game screen region
            
        Returns:
            True if click succeeded
        """
        ui_elements = self.detector.detect_ui_elements(
            game_area,
            element_types=['back_button', 'close_button'],
            threshold=0.80
        )
        
        for button_type in ['back_button', 'close_button']:
            if button_type in ui_elements and ui_elements[button_type]:
                position = ui_elements[button_type][0]
                return self._click_position(position)
        
        # Fallback: ESC key
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
            
            # Add randomness
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            
            target_x = x + offset_x
            target_y = y + offset_y
            
            # Move and click
            pyautogui.moveTo(target_x, target_y, duration=0.2)
            pyautogui.click()
            
            time.sleep(self.config['click_delay'])
            
            return True
        
        except Exception as e:
            print(f"[Navigator] Failed to click: {e}")
            return False
    
    def return_to_farm(self, game_area: Tuple[int, int, int, int]) -> Dict:
        """
        Return to main farm view.
        
        Args:
            game_area: Game screen region
            
        Returns:
            Navigation result
        """
        return self.navigate_to(GameScreen.FARM_VIEW, game_area)
    
    def should_return_to_farm(self) -> bool:
        """
        Check if we should auto-return to farm view.
        
        Returns:
            True if auto-return is needed
        """
        if not self.config['auto_return_to_farm']:
            return False
        
        if self.current_screen == GameScreen.FARM_VIEW:
            return False
        
        elapsed = time.time() - self.last_farm_visit
        return elapsed >= self.config['return_delay']
    
    def pan_camera(
        self,
        direction: str,
        distance: int = 100
    ) -> Dict:
        """
        Pan the camera in a direction (for large farms).
        
        Args:
            direction: 'up', 'down', 'left', 'right'
            distance: Pixels to pan
            
        Returns:
            Pan result
        """
        try:
            # Get current mouse position
            current_x, current_y = pyautogui.position()
            
            # Calculate drag vector
            vectors = {
                'up': (0, distance),
                'down': (0, -distance),
                'left': (distance, 0),
                'right': (-distance, 0)
            }
            
            dx, dy = vectors.get(direction, (0, 0))
            
            if dx == 0 and dy == 0:
                return {
                    'success': False,
                    'reason': 'Invalid direction'
                }
            
            # Perform drag
            pyautogui.mouseDown()
            pyautogui.moveTo(
                current_x + dx,
                current_y + dy,
                duration=self.config['pan_speed']
            )
            pyautogui.mouseUp()
            
            print(f"[Navigator] Panned camera {direction}")
            
            return {
                'success': True,
                'direction': direction,
                'distance': distance
            }
        
        except Exception as e:
            print(f"[Navigator] Failed to pan camera: {e}")
            return {
                'success': False,
                'reason': str(e)
            }
    
    def center_on_position(
        self,
        target_x: int,
        target_y: int,
        game_area: Tuple[int, int, int, int]
    ) -> Dict:
        """
        Pan camera to center on a specific position.
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            game_area: Game screen region
            
        Returns:
            Pan result
        """
        # Calculate center of game area
        area_x, area_y, area_w, area_h = game_area
        center_x = area_x + area_w // 2
        center_y = area_y + area_h // 2
        
        # Calculate offset from center
        offset_x = target_x - center_x
        offset_y = target_y - center_y
        
        # Pan if offset is significant
        threshold = 50
        
        if abs(offset_x) > threshold or abs(offset_y) > threshold:
            try:
                pyautogui.mouseDown()
                pyautogui.moveTo(
                    center_x - offset_x,
                    center_y - offset_y,
                    duration=self.config['pan_speed']
                )
                pyautogui.mouseUp()
                
                return {
                    'success': True,
                    'centered': True
                }
            
            except Exception as e:
                print(f"[Navigator] Failed to center on position: {e}")
                return {
                    'success': False,
                    'reason': str(e)
                }
        
        return {
            'success': True,
            'centered': False,
            'reason': 'Already centered'
        }
    
    def get_statistics(self) -> Dict:
        """
        Get navigation statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            'current_screen': self.current_screen.name,
            'navigation_count': len(self.navigation_history),
            'time_since_farm_visit': time.time() - self.last_farm_visit
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.navigation_history.clear()
    
    def update_config(self, new_config: Dict):
        """
        Update navigator configuration.
        
        Args:
            new_config: Dictionary of config updates
        """
        self.config.update(new_config)


class SmartNavigator(Navigator):
    """
    Enhanced navigator with path optimization.
    
    Finds optimal navigation paths and minimizes
    unnecessary screen transitions.
    """
    
    def __init__(self, game_state_detector: GameStateDetector):
        super().__init__(game_state_detector)
        self.navigation_graph = self._build_navigation_graph()
    
    def _build_navigation_graph(self) -> Dict:
        """
        Build graph of screen connections.
        
        Returns:
            Navigation graph
        """
        # Define which screens are directly accessible from each screen
        graph = {
            GameScreen.FARM_VIEW: [
                GameScreen.ORDER_BOARD,
                GameScreen.SHOP,
                GameScreen.SETTINGS,
                GameScreen.INVENTORY
            ],
            GameScreen.ORDER_BOARD: [GameScreen.FARM_VIEW],
            GameScreen.SHOP: [GameScreen.FARM_VIEW],
            GameScreen.SETTINGS: [GameScreen.FARM_VIEW],
            GameScreen.INVENTORY: [GameScreen.FARM_VIEW],
        }
        
        return graph
    
    def find_navigation_path(
        self,
        from_screen: GameScreen,
        to_screen: GameScreen
    ) -> List[GameScreen]:
        """
        Find optimal path between screens.
        
        Args:
            from_screen: Starting screen
            to_screen: Target screen
            
        Returns:
            List of screens to navigate through
        """
        if from_screen == to_screen:
            return []
        
        # Simple BFS pathfinding
        queue = [(from_screen, [from_screen])]
        visited = {from_screen}
        
        while queue:
            current, path = queue.pop(0)
            
            if current == to_screen:
                return path
            
            neighbors = self.navigation_graph.get(current, [])
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []  # No path found
    
    def navigate_to(
        self,
        target_screen: GameScreen,
        game_area: Tuple[int, int, int, int]
    ) -> Dict:
        """Navigate using optimal path."""
        current = self.detect_current_screen(game_area)
        
        if current == target_screen:
            return {
                'success': True,
                'reason': 'Already on target screen',
                'navigated': False
            }
        
        # Find optimal path
        path = self.find_navigation_path(current, target_screen)
        
        if not path or len(path) < 2:
            # Fallback to direct navigation
            return super().navigate_to(target_screen, game_area)
        
        # Navigate through path
        for i in range(1, len(path)):
            next_screen = path[i]
            result = super().navigate_to(next_screen, game_area)
            
            if not result['success']:
                return result
            
            time.sleep(self.config['click_delay'])
        
        return {
            'success': True,
            'navigated': True,
            'path': [s.name for s in path]
        }



