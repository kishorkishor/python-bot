"""Land Expansion Manager for Farm Merge Valley.

Automates farm growth by purchasing land expansions and
clearing obstacles when beneficial.
"""

import time
import random
from typing import Dict, List, Tuple, Optional

from pyautogui_safe import pyautogui

from game_state_detector import GameStateDetector
from energy_manager import EnergyManager


class ExpansionManager:
    """
    Manages automated land expansion and obstacle clearing.
    
    Detects available expansion plots, tracks coin balance,
    and purchases land when thresholds are met.
    """
    
    def __init__(
        self,
        game_state_detector: GameStateDetector,
        energy_manager: EnergyManager
    ):
        self.detector = game_state_detector
        self.energy_manager = energy_manager
        
        self.expansions_purchased = 0
        self.obstacles_cleared = 0
        self.total_coins_spent = 0
        self.last_expansion_time = 0
        self.expansion_cooldown = 300  # 5 minutes between expansion checks
        
        # Configuration
        self.config = {
            'auto_expand': False,  # Disabled by default (expensive)
            'coin_threshold': 5000,
            'max_coins_per_session': 10000,
            'clear_obstacles': True,
            'obstacle_energy_threshold': 50,
            'click_delay': 1.0,
        }
        
        # Tracking
        self.expansion_history = []  # (timestamp, coins_spent)
        self.available_expansions = []
    
    def can_check_expansions(self) -> bool:
        """Check if expansion check cooldown has elapsed."""
        elapsed = time.time() - self.last_expansion_time
        return elapsed >= self.expansion_cooldown
    
    def scan_for_expansions(
        self,
        game_area: Tuple[int, int, int, int],
        threshold: float = 0.75
    ) -> Dict:
        """
        Scan for available expansion plots.
        
        Args:
            game_area: Game screen region
            threshold: Detection confidence threshold
            
        Returns:
            Scan results with available expansions
        """
        if not self.can_check_expansions():
            return {
                'success': False,
                'reason': 'On cooldown',
                'expansions': []
            }
        
        # Detect expansion buttons/plots
        ui_elements = self.detector.detect_ui_elements(
            game_area,
            element_types=['expand_button', 'expansion_plot'],
            threshold=threshold
        )
        
        self.available_expansions = []
        
        # Process expansion buttons
        if 'expand_button' in ui_elements:
            for position in ui_elements['expand_button']:
                self.available_expansions.append({
                    'type': 'expand',
                    'position': position
                })
        
        # Process expansion plots
        if 'expansion_plot' in ui_elements:
            for position in ui_elements['expansion_plot']:
                self.available_expansions.append({
                    'type': 'plot',
                    'position': position
                })
        
        self.last_expansion_time = time.time()
        
        return {
            'success': True,
            'expansions': self.available_expansions,
            'count': len(self.available_expansions)
        }
    
    def should_expand(self, current_coins: Optional[int]) -> bool:
        """
        Determine if we should purchase expansion.
        
        Args:
            current_coins: Current coin balance
            
        Returns:
            True if expansion should be purchased
        """
        if not self.config['auto_expand']:
            return False
        
        if not self.available_expansions:
            return False
        
        # Check coin threshold
        if current_coins is None:
            return False
        
        if current_coins < self.config['coin_threshold']:
            return False
        
        # Check session spending limit
        if self.total_coins_spent >= self.config['max_coins_per_session']:
            return False
        
        return True
    
    def purchase_expansion(
        self,
        current_coins: Optional[int],
        estimated_cost: int = 1000
    ) -> Dict:
        """
        Purchase an available expansion.
        
        Args:
            current_coins: Current coin balance
            estimated_cost: Estimated cost of expansion
            
        Returns:
            Purchase result
        """
        if not self.should_expand(current_coins):
            return {
                'success': False,
                'reason': 'Expansion not allowed',
                'purchased': False
            }
        
        if not self.available_expansions:
            return {
                'success': False,
                'reason': 'No expansions available',
                'purchased': False
            }
        
        # Click first available expansion
        expansion = self.available_expansions[0]
        success = self._click_expansion(expansion)
        
        if success:
            self.expansions_purchased += 1
            self.total_coins_spent += estimated_cost
            self.expansion_history.append((time.time(), estimated_cost))
            
            print(f"[ExpansionManager] Purchased expansion for ~{estimated_cost} coins")
            
            return {
                'success': True,
                'purchased': True,
                'coins_spent': estimated_cost
            }
        
        return {
            'success': False,
            'reason': 'Click failed',
            'purchased': False
        }
    
    def _click_expansion(self, expansion: Dict) -> bool:
        """
        Click on an expansion plot/button.
        
        Args:
            expansion: Expansion info with position
            
        Returns:
            True if click succeeded
        """
        try:
            position = expansion['position']
            
            # Add randomness
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            
            target_x = position[0] + offset_x
            target_y = position[1] + offset_y
            
            # Move and click
            pyautogui.moveTo(target_x, target_y, duration=0.3)
            time.sleep(0.2)
            pyautogui.click()
            
            # Wait for confirmation dialog
            time.sleep(self.config['click_delay'])
            
            # Click confirm (usually center-bottom)
            # This is game-specific, may need adjustment
            pyautogui.click()
            
            return True
        
        except Exception as e:
            print(f"[ExpansionManager] Failed to click expansion: {e}")
            return False
    
    def scan_for_obstacles(
        self,
        game_area: Tuple[int, int, int, int],
        threshold: float = 0.70
    ) -> Dict:
        """
        Scan for clearable obstacles.
        
        Args:
            game_area: Game screen region
            threshold: Detection confidence threshold
            
        Returns:
            Scan results with obstacles
        """
        ui_elements = self.detector.detect_ui_elements(
            game_area,
            element_types=['obstacle', 'rock', 'tree', 'bush'],
            threshold=threshold
        )
        
        obstacles = []
        
        for element_type, positions in ui_elements.items():
            for position in positions:
                obstacles.append({
                    'type': element_type,
                    'position': position
                })
        
        return {
            'success': True,
            'obstacles': obstacles,
            'count': len(obstacles)
        }
    
    def should_clear_obstacle(self, current_energy: Optional[int]) -> bool:
        """
        Determine if we should clear an obstacle.
        
        Args:
            current_energy: Current energy level
            
        Returns:
            True if obstacle clearing is beneficial
        """
        if not self.config['clear_obstacles']:
            return False
        
        # Check energy threshold
        if current_energy is None:
            return False
        
        if current_energy < self.config['obstacle_energy_threshold']:
            return False
        
        return True
    
    def clear_obstacle(
        self,
        obstacle: Dict,
        energy_cost: int = 30
    ) -> Dict:
        """
        Clear a specific obstacle.
        
        Args:
            obstacle: Obstacle info with position
            energy_cost: Energy cost to clear
            
        Returns:
            Clear result
        """
        current_energy = self.energy_manager.current_energy
        
        if not self.should_clear_obstacle(current_energy):
            return {
                'success': False,
                'reason': 'Clearing not allowed',
                'cleared': False
            }
        
        # Click obstacle
        success = self._click_obstacle(obstacle)
        
        if success:
            self.obstacles_cleared += 1
            
            print(f"[ExpansionManager] Cleared {obstacle['type']} obstacle")
            
            return {
                'success': True,
                'cleared': True,
                'energy_spent': energy_cost
            }
        
        return {
            'success': False,
            'reason': 'Click failed',
            'cleared': False
        }
    
    def _click_obstacle(self, obstacle: Dict) -> bool:
        """
        Click on an obstacle to clear it.
        
        Args:
            obstacle: Obstacle info with position
            
        Returns:
            True if click succeeded
        """
        try:
            position = obstacle['position']
            
            # Add randomness
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            
            target_x = position[0] + offset_x
            target_y = position[1] + offset_y
            
            # Move and click
            pyautogui.moveTo(target_x, target_y, duration=0.3)
            time.sleep(0.2)
            pyautogui.click()
            
            # Wait for action
            time.sleep(self.config['click_delay'])
            
            # Confirm if needed
            pyautogui.click()
            
            return True
        
        except Exception as e:
            print(f"[ExpansionManager] Failed to click obstacle: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Get expansion statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            'expansions_purchased': self.expansions_purchased,
            'obstacles_cleared': self.obstacles_cleared,
            'total_coins_spent': self.total_coins_spent,
            'available_expansions': len(self.available_expansions)
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.expansions_purchased = 0
        self.obstacles_cleared = 0
        self.total_coins_spent = 0
        self.expansion_history.clear()
    
    def update_config(self, new_config: Dict):
        """
        Update expansion manager configuration.
        
        Args:
            new_config: Dictionary of config updates
        """
        self.config.update(new_config)


class SmartExpansionManager(ExpansionManager):
    """
    Enhanced expansion manager with cost-benefit analysis.
    
    Calculates optimal expansion timing based on resource
    generation and coin earning rate.
    """
    
    def __init__(
        self,
        game_state_detector: GameStateDetector,
        energy_manager: EnergyManager
    ):
        super().__init__(game_state_detector, energy_manager)
        self.expansion_costs = []  # Track actual costs
        self.coins_per_hour = 0.0  # Track earning rate
    
    def calculate_expansion_priority(
        self,
        current_coins: int,
        coins_per_hour: float
    ) -> float:
        """
        Calculate priority score for expansion.
        
        Args:
            current_coins: Current coin balance
            coins_per_hour: Coin earning rate
            
        Returns:
            Priority score (higher = more beneficial)
        """
        if not self.available_expansions:
            return 0.0
        
        # Estimate cost based on history
        estimated_cost = self._estimate_expansion_cost()
        
        # Calculate payback time (hours)
        if coins_per_hour > 0:
            payback_hours = estimated_cost / coins_per_hour
        else:
            payback_hours = float('inf')
        
        # Priority decreases with longer payback
        if payback_hours < 1.0:
            return 100.0  # Very high priority
        elif payback_hours < 2.0:
            return 50.0   # High priority
        elif payback_hours < 5.0:
            return 25.0   # Medium priority
        else:
            return 10.0   # Low priority
    
    def _estimate_expansion_cost(self) -> int:
        """
        Estimate cost of next expansion based on history.
        
        Returns:
            Estimated cost in coins
        """
        if not self.expansion_costs:
            return 1000  # Default estimate
        
        # Costs usually increase with each expansion
        last_cost = self.expansion_costs[-1]
        return int(last_cost * 1.5)  # Estimate 50% increase
    
    def purchase_expansion(
        self,
        current_coins: Optional[int],
        estimated_cost: int = 1000
    ) -> Dict:
        """Purchase expansion and track actual cost."""
        coins_before = current_coins
        
        result = super().purchase_expansion(current_coins, estimated_cost)
        
        if result.get('purchased'):
            # Track actual cost if we can read coins
            if coins_before is not None:
                self.expansion_costs.append(estimated_cost)
        
        return result
    
    def set_earning_rate(self, coins_per_hour: float):
        """
        Set current coin earning rate.
        
        Args:
            coins_per_hour: Coins earned per hour
        """
        self.coins_per_hour = coins_per_hour
    
    def get_expansion_recommendation(
        self,
        current_coins: int
    ) -> Dict:
        """
        Get recommendation on whether to expand now.
        
        Args:
            current_coins: Current coin balance
            
        Returns:
            Recommendation dictionary
        """
        if not self.available_expansions:
            return {
                'recommend': False,
                'reason': 'No expansions available'
            }
        
        priority = self.calculate_expansion_priority(
            current_coins,
            self.coins_per_hour
        )
        
        estimated_cost = self._estimate_expansion_cost()
        
        if current_coins < estimated_cost:
            return {
                'recommend': False,
                'reason': f'Insufficient coins (need {estimated_cost})',
                'priority': priority
            }
        
        if priority >= 50.0:
            return {
                'recommend': True,
                'reason': 'High priority expansion',
                'priority': priority,
                'estimated_cost': estimated_cost
            }
        elif priority >= 25.0:
            return {
                'recommend': True,
                'reason': 'Medium priority expansion',
                'priority': priority,
                'estimated_cost': estimated_cost
            }
        else:
            return {
                'recommend': False,
                'reason': 'Low priority, save coins',
                'priority': priority,
                'estimated_cost': estimated_cost
            }



