"""Resource Collection Automation for Farm Merge Valley.

Automates collection of produced goods from animals and crops,
tracks inventory, and manages collection cooldowns.
"""

import time
import random
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from pyautogui_safe import pyautogui

from game_state_detector import GameStateDetector


class ResourceCollector:
    """
    Automates collection of resources from producers.
    
    Scans for ready indicators, clicks producers to collect,
    and tracks inventory for order fulfillment.
    """
    
    def __init__(self, game_state_detector: GameStateDetector):
        self.detector = game_state_detector
        self.inventory = defaultdict(int)  # Track collected items
        self.collection_history: List[Dict] = []
        self.last_collection_time = 0
        self.collection_cooldown = 30  # Seconds between scans
        
        # Statistics
        self.total_collections = 0
        self.collections_by_type = defaultdict(int)
        
        # Configuration
        self.config = {
            'click_delay_min': 0.3,
            'click_delay_max': 0.7,
            'double_click': False,  # Some games require double-click
            'scan_interval': 30,
            'max_collections_per_cycle': 20,
        }
    
    def can_collect(self) -> bool:
        """Check if collection cooldown has elapsed."""
        elapsed = time.time() - self.last_collection_time
        return elapsed >= self.collection_cooldown
    
    def collect_from_producers(
        self,
        game_area: Tuple[int, int, int, int],
        resize_factor: float = 1.0,
        threshold: float = 0.75
    ) -> Dict:
        """
        Scan for and collect from ready producers.
        
        Args:
            game_area: Screen region containing game board
            resize_factor: Template scale factor
            threshold: Detection confidence threshold
            
        Returns:
            Collection results with counts and items
        """
        if not self.can_collect():
            return {
                'success': False,
                'reason': 'On cooldown',
                'collected': 0
            }
        
        # Detect ready producers
        producers = self.detector.detect_producers_ready(
            game_area,
            resize_factor,
            threshold
        )
        
        if not producers:
            self.last_collection_time = time.time()
            return {
                'success': True,
                'reason': 'No producers ready',
                'collected': 0
            }
        
        # Collect from each producer
        collected_count = 0
        collected_items = []
        max_collections = self.config['max_collections_per_cycle']
        
        for producer in producers[:max_collections]:
            success = self._click_producer(producer)
            
            if success:
                collected_count += 1
                producer_type = producer['type']
                collected_items.append(producer_type)
                
                # Update inventory (estimate based on producer type)
                self._update_inventory(producer_type)
                
                # Update statistics
                self.total_collections += 1
                self.collections_by_type[producer_type] += 1
                
                # Random delay between collections
                delay = random.uniform(
                    self.config['click_delay_min'],
                    self.config['click_delay_max']
                )
                time.sleep(delay)
        
        # Record collection event
        self.collection_history.append({
            'timestamp': time.time(),
            'collected': collected_count,
            'items': collected_items
        })
        
        self.last_collection_time = time.time()
        
        return {
            'success': True,
            'collected': collected_count,
            'items': collected_items,
            'total_producers': len(producers)
        }
    
    def _click_producer(self, producer: Dict) -> bool:
        """
        Click on a producer to collect resources.
        
        Args:
            producer: Producer info with position
            
        Returns:
            True if click succeeded
        """
        try:
            position = producer['position']
            
            # Move to position with slight randomness
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            
            target_x = position[0] + offset_x
            target_y = position[1] + offset_y
            
            # Move mouse smoothly
            pyautogui.moveTo(target_x, target_y, duration=0.2)
            
            # Click (single or double based on config)
            if self.config['double_click']:
                pyautogui.doubleClick()
            else:
                pyautogui.click()
            
            return True
        
        except Exception as e:
            print(f"[Collector] Failed to click producer: {e}")
            return False
    
    def _update_inventory(self, producer_type: str):
        """
        Update inventory based on collected producer type.
        
        Args:
            producer_type: Type of producer collected from
        """
        # Map producer types to items (game-specific logic)
        producer_to_item = {
            'chicken': 'egg',
            'cow': 'milk',
            'sheep': 'wool',
            'wheat': 'wheat',
            'corn': 'corn',
            'tomato': 'tomato',
        }
        
        item = producer_to_item.get(producer_type, producer_type)
        self.inventory[item] += 1
    
    def get_inventory(self) -> Dict[str, int]:
        """
        Get current inventory counts.
        
        Returns:
            Dictionary mapping item names to counts
        """
        return dict(self.inventory)
    
    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """
        Check if inventory has sufficient quantity of an item.
        
        Args:
            item_name: Item to check
            quantity: Required quantity
            
        Returns:
            True if inventory has enough
        """
        return self.inventory.get(item_name, 0) >= quantity
    
    def consume_item(self, item_name: str, quantity: int = 1) -> bool:
        """
        Remove items from inventory (when used for orders).
        
        Args:
            item_name: Item to consume
            quantity: Amount to consume
            
        Returns:
            True if consumption succeeded
        """
        if not self.has_item(item_name, quantity):
            return False
        
        self.inventory[item_name] -= quantity
        return True
    
    def get_statistics(self) -> Dict:
        """
        Get collection statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            'total_collections': self.total_collections,
            'collections_by_type': dict(self.collections_by_type),
            'inventory': self.get_inventory(),
            'collection_events': len(self.collection_history)
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.total_collections = 0
        self.collections_by_type.clear()
        self.collection_history.clear()
    
    def clear_inventory(self):
        """Clear inventory tracking."""
        self.inventory.clear()
    
    def update_config(self, new_config: Dict):
        """
        Update collector configuration.
        
        Args:
            new_config: Dictionary of config updates
        """
        self.config.update(new_config)
        if 'scan_interval' in new_config:
            self.collection_cooldown = new_config['scan_interval']


class SmartCollector(ResourceCollector):
    """
    Enhanced collector with priority-based collection.
    
    Prioritizes collecting from producers that generate items
    needed for active orders.
    """
    
    def __init__(self, game_state_detector: GameStateDetector):
        super().__init__(game_state_detector)
        self.order_requirements = []  # Items needed for orders
    
    def set_order_requirements(self, requirements: List[str]):
        """
        Set items needed for active orders.
        
        Args:
            requirements: List of item names needed
        """
        self.order_requirements = requirements
    
    def collect_from_producers(
        self,
        game_area: Tuple[int, int, int, int],
        resize_factor: float = 1.0,
        threshold: float = 0.75
    ) -> Dict:
        """
        Collect from producers with priority for order items.
        
        Args:
            game_area: Screen region containing game board
            resize_factor: Template scale factor
            threshold: Detection confidence threshold
            
        Returns:
            Collection results
        """
        if not self.can_collect():
            return {
                'success': False,
                'reason': 'On cooldown',
                'collected': 0
            }
        
        # Detect ready producers
        producers = self.detector.detect_producers_ready(
            game_area,
            resize_factor,
            threshold
        )
        
        if not producers:
            self.last_collection_time = time.time()
            return {
                'success': True,
                'reason': 'No producers ready',
                'collected': 0
            }
        
        # Sort producers by priority
        prioritized = self._prioritize_producers(producers)
        
        # Collect from prioritized producers
        collected_count = 0
        collected_items = []
        max_collections = self.config['max_collections_per_cycle']
        
        for producer in prioritized[:max_collections]:
            success = self._click_producer(producer)
            
            if success:
                collected_count += 1
                producer_type = producer['type']
                collected_items.append(producer_type)
                
                self._update_inventory(producer_type)
                self.total_collections += 1
                self.collections_by_type[producer_type] += 1
                
                delay = random.uniform(
                    self.config['click_delay_min'],
                    self.config['click_delay_max']
                )
                time.sleep(delay)
        
        self.collection_history.append({
            'timestamp': time.time(),
            'collected': collected_count,
            'items': collected_items
        })
        
        self.last_collection_time = time.time()
        
        return {
            'success': True,
            'collected': collected_count,
            'items': collected_items,
            'total_producers': len(producers)
        }
    
    def _prioritize_producers(self, producers: List[Dict]) -> List[Dict]:
        """
        Sort producers by priority (order requirements first).
        
        Args:
            producers: List of detected producers
            
        Returns:
            Sorted list with high-priority producers first
        """
        if not self.order_requirements:
            return producers
        
        priority = []
        normal = []
        
        for producer in producers:
            producer_type = producer['type']
            
            # Check if this producer generates needed items
            if any(req in producer_type for req in self.order_requirements):
                priority.append(producer)
            else:
                normal.append(producer)
        
        return priority + normal



