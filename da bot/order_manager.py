"""Order Fulfillment System for Farm Merge Valley.

Automates detecting, tracking, and completing customer orders
to maximize coin generation.
"""

import time
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from pyautogui_safe import pyautogui

from game_state_detector import GameStateDetector
from collectors import ResourceCollector


@dataclass
class Order:
    """Represents a customer order."""
    items: List[str]
    position: Tuple[int, int]
    reward_coins: int = 0
    reward_xp: int = 0
    detected_time: float = 0.0
    
    def can_fulfill(self, inventory: Dict[str, int]) -> bool:
        """Check if we have all required items."""
        for item in self.items:
            if inventory.get(item, 0) < 1:
                return False
        return True
    
    def get_priority_score(self) -> float:
        """Calculate priority score (higher = more important)."""
        # Prioritize high coin rewards and simple orders
        coin_score = self.reward_coins if self.reward_coins > 0 else 100
        complexity_penalty = len(self.items) * 10
        return coin_score - complexity_penalty


class OrderManager:
    """
    Manages order detection and fulfillment automation.
    
    Detects available orders, checks inventory, and clicks to
    fulfill when ready. Prioritizes high-value orders.
    """
    
    def __init__(
        self,
        game_state_detector: GameStateDetector,
        resource_collector: ResourceCollector
    ):
        self.detector = game_state_detector
        self.collector = resource_collector
        
        self.active_orders: List[Order] = []
        self.fulfilled_orders = 0
        self.total_coins_earned = 0
        self.last_scan_time = 0
        self.scan_cooldown = 60  # Seconds between order scans
        
        # Configuration
        self.config = {
            'auto_fulfill': True,
            'min_coins_per_order': 0,  # Minimum coins to accept order
            'max_order_complexity': 5,  # Max items per order
            'click_delay': 0.5,
            'prioritize_coins': True,
        }
    
    def can_scan_orders(self) -> bool:
        """Check if order scan cooldown has elapsed."""
        elapsed = time.time() - self.last_scan_time
        return elapsed >= self.scan_cooldown
    
    def scan_orders(
        self,
        order_board_region: Tuple[int, int, int, int],
        resize_factor: float = 1.0,
        threshold: float = 0.70
    ) -> Dict:
        """
        Scan order board for active orders.
        
        Args:
            order_board_region: Screen region of order board
            resize_factor: Template scale factor
            threshold: Detection confidence threshold
            
        Returns:
            Scan results with detected orders
        """
        if not self.can_scan_orders():
            return {
                'success': False,
                'reason': 'On cooldown',
                'orders': []
            }
        
        # Detect orders
        detected_orders = self.detector.detect_active_orders(
            order_board_region,
            resize_factor,
            threshold
        )
        
        # Convert to Order objects
        self.active_orders.clear()
        
        for order_data in detected_orders:
            order = Order(
                items=order_data['items'],
                position=order_data['position'],
                detected_time=time.time()
            )
            
            # Estimate reward (game-specific logic)
            order.reward_coins = self._estimate_reward(order)
            
            # Filter by configuration
            if order.reward_coins < self.config['min_coins_per_order']:
                continue
            
            if len(order.items) > self.config['max_order_complexity']:
                continue
            
            self.active_orders.append(order)
        
        self.last_scan_time = time.time()
        
        return {
            'success': True,
            'orders': self.active_orders,
            'count': len(self.active_orders)
        }
    
    def _estimate_reward(self, order: Order) -> int:
        """
        Estimate coin reward for an order.
        
        Args:
            order: Order to estimate
            
        Returns:
            Estimated coin reward
        """
        # Base reward increases with complexity
        base_reward = 50
        per_item_reward = 25
        
        return base_reward + (len(order.items) * per_item_reward)
    
    def fulfill_orders(self) -> Dict:
        """
        Attempt to fulfill all ready orders.
        
        Returns:
            Fulfillment results
        """
        if not self.config['auto_fulfill']:
            return {
                'success': False,
                'reason': 'Auto-fulfill disabled',
                'fulfilled': 0
            }
        
        if not self.active_orders:
            return {
                'success': True,
                'reason': 'No active orders',
                'fulfilled': 0
            }
        
        # Get current inventory
        inventory = self.collector.get_inventory()
        
        # Sort orders by priority
        prioritized_orders = self._prioritize_orders(self.active_orders)
        
        fulfilled_count = 0
        fulfilled_items = []
        coins_earned = 0
        
        for order in prioritized_orders:
            if order.can_fulfill(inventory):
                success = self._click_order(order)
                
                if success:
                    fulfilled_count += 1
                    fulfilled_items.append(order.items)
                    coins_earned += order.reward_coins
                    
                    # Update inventory (consume items)
                    for item in order.items:
                        self.collector.consume_item(item, 1)
                        inventory = self.collector.get_inventory()
                    
                    # Update statistics
                    self.fulfilled_orders += 1
                    self.total_coins_earned += order.reward_coins
                    
                    # Delay between fulfillments
                    time.sleep(self.config['click_delay'])
        
        return {
            'success': True,
            'fulfilled': fulfilled_count,
            'items': fulfilled_items,
            'coins_earned': coins_earned,
            'total_orders': len(self.active_orders)
        }
    
    def _prioritize_orders(self, orders: List[Order]) -> List[Order]:
        """
        Sort orders by priority.
        
        Args:
            orders: List of orders to prioritize
            
        Returns:
            Sorted list with high-priority orders first
        """
        if self.config['prioritize_coins']:
            return sorted(orders, key=lambda o: o.get_priority_score(), reverse=True)
        else:
            # Simplest orders first
            return sorted(orders, key=lambda o: len(o.items))
    
    def _click_order(self, order: Order) -> bool:
        """
        Click on an order to fulfill it.
        
        Args:
            order: Order to click
            
        Returns:
            True if click succeeded
        """
        try:
            position = order.position
            
            # Add slight randomness
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            
            target_x = position[0] + offset_x
            target_y = position[1] + offset_y
            
            # Move and click
            pyautogui.moveTo(target_x, target_y, duration=0.2)
            pyautogui.click()
            
            return True
        
        except Exception as e:
            print(f"[OrderManager] Failed to click order: {e}")
            return False
    
    def get_fulfillable_orders(self) -> List[Order]:
        """
        Get orders that can be fulfilled with current inventory.
        
        Returns:
            List of fulfillable orders
        """
        inventory = self.collector.get_inventory()
        return [order for order in self.active_orders if order.can_fulfill(inventory)]
    
    def get_missing_items(self) -> Dict[str, int]:
        """
        Get items needed to fulfill all active orders.
        
        Returns:
            Dictionary mapping item names to required quantities
        """
        inventory = self.collector.get_inventory()
        needed = {}
        
        for order in self.active_orders:
            for item in order.items:
                current = inventory.get(item, 0)
                if current < 1:
                    needed[item] = needed.get(item, 0) + 1
        
        return needed
    
    def get_statistics(self) -> Dict:
        """
        Get order fulfillment statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            'fulfilled_orders': self.fulfilled_orders,
            'total_coins_earned': self.total_coins_earned,
            'active_orders': len(self.active_orders),
            'fulfillable_orders': len(self.get_fulfillable_orders())
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.fulfilled_orders = 0
        self.total_coins_earned = 0
    
    def update_config(self, new_config: Dict):
        """
        Update order manager configuration.
        
        Args:
            new_config: Dictionary of config updates
        """
        self.config.update(new_config)
        if 'scan_interval' in new_config:
            self.scan_cooldown = new_config['scan_interval']


class SmartOrderManager(OrderManager):
    """
    Enhanced order manager with predictive fulfillment.
    
    Tracks order patterns and optimizes collection priorities
    to maximize fulfillment rate.
    """
    
    def __init__(
        self,
        game_state_detector: GameStateDetector,
        resource_collector: ResourceCollector
    ):
        super().__init__(game_state_detector, resource_collector)
        self.order_history: List[Dict] = []
        self.item_frequency = {}  # Track most common order items
    
    def scan_orders(
        self,
        order_board_region: Tuple[int, int, int, int],
        resize_factor: float = 1.0,
        threshold: float = 0.70
    ) -> Dict:
        """Scan orders and update item frequency tracking."""
        result = super().scan_orders(order_board_region, resize_factor, threshold)
        
        if result['success']:
            # Update item frequency
            for order in self.active_orders:
                for item in order.items:
                    self.item_frequency[item] = self.item_frequency.get(item, 0) + 1
        
        return result
    
    def get_collection_priorities(self) -> List[str]:
        """
        Get prioritized list of items to collect based on orders.
        
        Returns:
            List of item names sorted by priority
        """
        # Get items needed for active orders
        missing = self.get_missing_items()
        
        # Sort by frequency and current need
        priority_items = sorted(
            missing.keys(),
            key=lambda item: (missing[item], self.item_frequency.get(item, 0)),
            reverse=True
        )
        
        return priority_items
    
    def fulfill_orders(self) -> Dict:
        """Fulfill orders and record to history."""
        result = super().fulfill_orders()
        
        if result['success'] and result['fulfilled'] > 0:
            self.order_history.append({
                'timestamp': time.time(),
                'fulfilled': result['fulfilled'],
                'coins': result['coins_earned']
            })
        
        return result
    
    def get_coins_per_hour(self) -> float:
        """
        Calculate average coins earned per hour.
        
        Returns:
            Coins per hour rate
        """
        if not self.order_history:
            return 0.0
        
        # Calculate from last hour of history
        one_hour_ago = time.time() - 3600
        recent_history = [
            h for h in self.order_history
            if h['timestamp'] >= one_hour_ago
        ]
        
        if not recent_history:
            return 0.0
        
        total_coins = sum(h['coins'] for h in recent_history)
        time_span = time.time() - recent_history[0]['timestamp']
        
        if time_span == 0:
            return 0.0
        
        return (total_coins / time_span) * 3600



