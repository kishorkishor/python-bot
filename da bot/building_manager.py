"""Building Management System for Farm Merge Valley.

Manages building repairs and upgrades, tracks material inventory,
and prioritizes repairs that unlock new production.
"""

import time
import random
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

import pyautogui

from game_state_detector import GameStateDetector


class BuildingManager:
    """
    Manages automated building repairs and upgrades.
    
    Detects repair-ready buildings, tracks materials,
    and prioritizes repairs strategically.
    """
    
    def __init__(self, game_state_detector: GameStateDetector):
        self.detector = game_state_detector
        self.material_inventory = defaultdict(int)  # wood, bricks, etc.
        self.buildings_repaired = 0
        self.last_scan_time = 0
        self.scan_cooldown = 120  # 2 minutes between scans
        
        # Configuration
        self.config = {
            'auto_repair': True,
            'prioritize_production': True,  # Prioritize buildings that unlock production
            'click_delay': 1.0,
        }
        
        # Tracking
        self.available_repairs = []
        self.repair_history = []  # (timestamp, building_type, materials_used)
        
        # Building priorities (game-specific, customize as needed)
        self.building_priorities = {
            'barn': 100,          # High priority (storage)
            'factory': 90,        # High priority (production)
            'chicken_coop': 80,   # High priority (resource generation)
            'cow_barn': 80,
            'workshop': 70,
            'house': 50,          # Medium priority
            'decoration': 10,     # Low priority
        }
    
    def can_scan_buildings(self) -> bool:
        """Check if building scan cooldown has elapsed."""
        elapsed = time.time() - self.last_scan_time
        return elapsed >= self.scan_cooldown
    
    def scan_for_repairs(
        self,
        game_area: Tuple[int, int, int, int],
        threshold: float = 0.75
    ) -> Dict:
        """
        Scan for buildings that need repair.
        
        Args:
            game_area: Game screen region
            threshold: Detection confidence threshold
            
        Returns:
            Scan results with repairable buildings
        """
        if not self.can_scan_buildings():
            return {
                'success': False,
                'reason': 'On cooldown',
                'repairs': []
            }
        
        # Detect repair buttons
        ui_elements = self.detector.detect_ui_elements(
            game_area,
            element_types=['repair_button', 'upgrade_button', 'fix_button'],
            threshold=threshold
        )
        
        self.available_repairs.clear()
        
        # Process repair buttons
        for element_type, positions in ui_elements.items():
            for position in positions:
                self.available_repairs.append({
                    'type': 'unknown',  # Would need building detection to identify
                    'position': position,
                    'button_type': element_type
                })
        
        self.last_scan_time = time.time()
        
        return {
            'success': True,
            'repairs': self.available_repairs,
            'count': len(self.available_repairs)
        }
    
    def should_repair(self) -> bool:
        """
        Determine if we should perform repairs.
        
        Returns:
            True if repair should happen
        """
        if not self.config['auto_repair']:
            return False
        
        if not self.available_repairs:
            return False
        
        # Check if we have materials (simplified check)
        # In a real implementation, would check specific requirements
        return True
    
    def repair_building(self, building: Optional[Dict] = None) -> Dict:
        """
        Repair a specific building or the highest priority one.
        
        Args:
            building: Specific building to repair (None = auto-select)
            
        Returns:
            Repair result
        """
        if not self.should_repair():
            return {
                'success': False,
                'reason': 'Repair not allowed',
                'repaired': False
            }
        
        # Select building to repair
        if building is None:
            if not self.available_repairs:
                return {
                    'success': False,
                    'reason': 'No repairs available',
                    'repaired': False
                }
            
            # Get highest priority repair
            building = self._select_priority_repair()
        
        # Click repair button
        success = self._click_repair(building)
        
        if success:
            self.buildings_repaired += 1
            self.repair_history.append({
                'timestamp': time.time(),
                'building_type': building.get('type', 'unknown'),
                'materials_used': {}  # Would track actual materials
            })
            
            print(f"[BuildingManager] Repaired building at {building['position']}")
            
            return {
                'success': True,
                'repaired': True,
                'building': building
            }
        
        return {
            'success': False,
            'reason': 'Click failed',
            'repaired': False
        }
    
    def _select_priority_repair(self) -> Dict:
        """
        Select the highest priority repair from available repairs.
        
        Returns:
            Selected repair
        """
        if not self.available_repairs:
            return {}
        
        # Sort by priority (if building types are known)
        prioritized = sorted(
            self.available_repairs,
            key=lambda b: self.building_priorities.get(b.get('type', 'unknown'), 50),
            reverse=True
        )
        
        return prioritized[0]
    
    def _click_repair(self, building: Dict) -> bool:
        """
        Click on a repair button.
        
        Args:
            building: Building info with repair button position
            
        Returns:
            True if click succeeded
        """
        try:
            position = building['position']
            
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
            
            # Click confirm (usually center or specific button)
            # This is game-specific, may need adjustment
            pyautogui.click()
            
            return True
        
        except Exception as e:
            print(f"[BuildingManager] Failed to click repair: {e}")
            return False
    
    def update_material_inventory(self, materials: Dict[str, int]):
        """
        Update material inventory counts.
        
        Args:
            materials: Dictionary of material counts
        """
        self.material_inventory.update(materials)
    
    def has_materials(self, requirements: Dict[str, int]) -> bool:
        """
        Check if we have required materials.
        
        Args:
            requirements: Required materials
            
        Returns:
            True if we have all required materials
        """
        for material, quantity in requirements.items():
            if self.material_inventory.get(material, 0) < quantity:
                return False
        return True
    
    def consume_materials(self, materials: Dict[str, int]):
        """
        Remove materials from inventory (when used for repair).
        
        Args:
            materials: Materials to consume
        """
        for material, quantity in materials.items():
            self.material_inventory[material] -= quantity
            if self.material_inventory[material] < 0:
                self.material_inventory[material] = 0
    
    def get_statistics(self) -> Dict:
        """
        Get building management statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            'buildings_repaired': self.buildings_repaired,
            'available_repairs': len(self.available_repairs),
            'material_inventory': dict(self.material_inventory),
            'repair_history_length': len(self.repair_history)
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.buildings_repaired = 0
        self.repair_history.clear()
    
    def update_config(self, new_config: Dict):
        """
        Update building manager configuration.
        
        Args:
            new_config: Dictionary of config updates
        """
        self.config.update(new_config)


class SmartBuildingManager(BuildingManager):
    """
    Enhanced building manager with strategic repair planning.
    
    Analyzes building benefits and optimizes repair order
    for maximum productivity gain.
    """
    
    def __init__(self, game_state_detector: GameStateDetector):
        super().__init__(game_state_detector)
        self.building_benefits = {}  # Track productivity gains from repairs
    
    def calculate_repair_value(self, building: Dict) -> float:
        """
        Calculate value score for repairing a building.
        
        Args:
            building: Building to evaluate
            
        Returns:
            Value score (higher = more valuable)
        """
        building_type = building.get('type', 'unknown')
        
        # Base priority from config
        base_priority = self.building_priorities.get(building_type, 50)
        
        # Adjust based on production unlock
        if self.config['prioritize_production']:
            if building_type in ['barn', 'factory', 'chicken_coop', 'cow_barn']:
                base_priority *= 1.5
        
        # Adjust based on material availability
        # (Would check actual requirements in real implementation)
        material_bonus = 1.0
        
        return base_priority * material_bonus
    
    def get_repair_plan(self) -> List[Dict]:
        """
        Generate optimal repair order for all available repairs.
        
        Returns:
            List of repairs sorted by value
        """
        if not self.available_repairs:
            return []
        
        # Calculate value for each repair
        valued_repairs = []
        for repair in self.available_repairs:
            value = self.calculate_repair_value(repair)
            valued_repairs.append({
                'repair': repair,
                'value': value
            })
        
        # Sort by value
        valued_repairs.sort(key=lambda x: x['value'], reverse=True)
        
        return [item['repair'] for item in valued_repairs]
    
    def track_repair_benefit(self, building_type: str, productivity_gain: float):
        """
        Track productivity gain from a repair.
        
        Args:
            building_type: Type of building repaired
            productivity_gain: Measured productivity increase
        """
        if building_type not in self.building_benefits:
            self.building_benefits[building_type] = []
        
        self.building_benefits[building_type].append(productivity_gain)
    
    def get_average_benefit(self, building_type: str) -> float:
        """
        Get average productivity benefit for a building type.
        
        Args:
            building_type: Building type to check
            
        Returns:
            Average benefit
        """
        benefits = self.building_benefits.get(building_type, [])
        if not benefits:
            return 0.0
        
        return sum(benefits) / len(benefits)
    
    def repair_building(self, building: Optional[Dict] = None) -> Dict:
        """Repair with value-based selection."""
        if building is None and self.available_repairs:
            # Use repair plan to select best repair
            repair_plan = self.get_repair_plan()
            if repair_plan:
                building = repair_plan[0]
        
        return super().repair_building(building)



