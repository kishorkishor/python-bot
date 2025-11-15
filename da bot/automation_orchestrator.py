"""Automation Orchestrator for Farm Merge Valley

Coordinates all automation modules into a unified automation loop.
"""

import time
import threading
from typing import Dict, Optional, Tuple
from queue import Queue

from game_state_detector import GameStateDetector
from game_state_machine import GameStateMachine, GameState
from collectors import SmartCollector
from order_manager import SmartOrderManager
from energy_manager import SmartEnergyManager
from popup_handler import PopupHandler

# Try to import ProfileManager, make it optional
try:
    from profiles import ProfileManager
    PROFILE_MANAGER_AVAILABLE = True
except ImportError:
    PROFILE_MANAGER_AVAILABLE = False
    ProfileManager = None


class AutomationOrchestrator:
    """
    Main automation coordinator that manages all automation modules.
    
    Provides a unified interface for starting, stopping, and monitoring
    the complete automation system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize automation orchestrator with all modules."""
        self.config = config or {}
        
        # Initialize all modules
        self.detector = GameStateDetector()
        self.state_machine = GameStateMachine()
        self.collector = SmartCollector(self.detector)
        self.order_manager = SmartOrderManager(self.detector, self.collector)
        self.energy_manager = SmartEnergyManager()
        self.popup_handler = PopupHandler(self.detector)
        
        # Profile manager (optional)
        if PROFILE_MANAGER_AVAILABLE:
            self.profile_manager = ProfileManager()
        else:
            self.profile_manager = None
        
        # State
        self.is_running = False
        self.is_paused = False
        self.automation_thread = None
        self.stop_event = threading.Event()
        
        # Game regions (must be set before starting)
        self.game_area: Optional[Tuple[int, int, int, int]] = None
        self.order_board_region: Optional[Tuple[int, int, int, int]] = None
        self.energy_region: Optional[Tuple[int, int, int, int]] = None
        self.coin_region: Optional[Tuple[int, int, int, int]] = None
        
        # Settings
        self.resize_factor = 1.0
        self.detection_threshold = 0.75
        
        # Statistics
        self.stats = {
            'start_time': None,
            'runtime': 0,
            'actions_executed': 0,
            'errors': 0,
            'last_action': None,
            'last_error': None
        }
        
        # Callbacks for UI updates
        self.status_callback = None
        self.log_callback = None
        
        # Apply configuration
        self._apply_config()
    
    def _apply_config(self):
        """Apply configuration to all modules."""
        if not self.config:
            return
        
        # Update state machine config
        automation_config = self.config.get('automation', {})
        self.state_machine.update_config(automation_config)
        
        # Update collector config
        timing_config = self.config.get('timing', {})
        if 'scan_interval_resources' in timing_config:
            self.collector.update_config({'scan_interval': timing_config['scan_interval_resources']})
        
        # Update order manager config
        if 'scan_interval_orders' in timing_config:
            self.order_manager.update_config({'scan_interval': timing_config['scan_interval_orders']})
        
        # Update energy manager config
        if 'energy_threshold' in automation_config:
            self.energy_manager.update_config({'low_energy_threshold': automation_config['energy_threshold']})
    
    def set_game_regions(
        self,
        game_area: Tuple[int, int, int, int],
        order_board_region: Optional[Tuple[int, int, int, int]] = None,
        energy_region: Optional[Tuple[int, int, int, int]] = None,
        coin_region: Optional[Tuple[int, int, int, int]] = None
    ):
        """Set game screen regions for detection."""
        self.game_area = game_area
        self.order_board_region = order_board_region
        self.energy_region = energy_region
        self.coin_region = coin_region
        
        # Update energy manager
        if energy_region:
            self.energy_manager.set_energy_region(energy_region)
    
    def set_callbacks(self, status_callback=None, log_callback=None):
        """Set callbacks for UI updates."""
        self.status_callback = status_callback
        self.log_callback = log_callback
    
    def _log(self, message: str, level: str = "info"):
        """Log a message via callback."""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
    
    def _update_status(self, status: str):
        """Update status via callback."""
        if self.status_callback:
            self.status_callback(status)
    
    def start(self):
        """Start the automation loop."""
        if self.is_running:
            self._log("Automation already running", "warning")
            return False
        
        if not self.game_area:
            self._log("Game area not set. Please configure screen area first.", "error")
            return False
        
        self.is_running = True
        self.is_paused = False
        self.stop_event.clear()
        self.stats['start_time'] = time.time()
        
        # Start automation thread
        self.automation_thread = threading.Thread(target=self._automation_loop, daemon=True)
        self.automation_thread.start()
        
        self._log("Automation started", "success")
        self._update_status("Running")
        return True
    
    def stop(self):
        """Stop the automation loop."""
        if not self.is_running:
            return
        
        self.is_running = False
        self.stop_event.set()
        
        if self.automation_thread:
            self.automation_thread.join(timeout=2.0)
        
        self._log("Automation stopped", "info")
        self._update_status("Stopped")
    
    def pause(self):
        """Pause automation."""
        if not self.is_running:
            return
        
        self.is_paused = True
        self.state_machine.pause()
        self._log("Automation paused", "info")
        self._update_status("Paused")
    
    def resume(self):
        """Resume automation."""
        if not self.is_running:
            return
        
        self.is_paused = False
        self.state_machine.resume()
        self._log("Automation resumed", "info")
        self._update_status("Running")
    
    def _automation_loop(self):
        """Main automation loop."""
        loop_count = 0
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # Handle pause
                if self.is_paused:
                    time.sleep(1)
                    continue
                
                loop_count += 1
                
                # Priority 1: Handle popups (blocks everything)
                if self.config.get('automation', {}).get('handle_popups', True):
                    popup = self.popup_handler.check_and_handle_popups(self.game_area)
                    if popup:
                        self._log(f"Handled popup: {popup.get('type', 'unknown')}", "info")
                        self.stats['actions_executed'] += 1
                        self.stats['last_action'] = "handle_popup"
                        time.sleep(0.5)
                        continue
                
                # Priority 2: Update energy
                if self.energy_region:
                    energy_status = self.energy_manager.update()
                    if energy_status.get('tasks_paused'):
                        self._log(f"Tasks paused: {energy_status.get('pause_reason', 'Low energy')}", "warning")
                        time.sleep(5)
                        continue
                
                # Priority 3: Get game state
                game_state = self.detector.get_game_state_summary(
                    self.game_area,
                    self.order_board_region,
                    self.energy_region,
                    self.coin_region,
                    self.resize_factor
                )
                
                # Priority 4: Decide next action
                next_action = self.state_machine.decide_next_action(game_state)
                
                if not next_action:
                    # No action needed, idle
                    if loop_count % 10 == 0:  # Log every 10 idle cycles
                        self._log("Idle - waiting for actions", "info")
                    time.sleep(2)
                    continue
                
                # Priority 5: Execute action
                success = self._execute_action(next_action, game_state)
                
                if success:
                    self.stats['actions_executed'] += 1
                    self.stats['last_action'] = next_action
                else:
                    self.stats['errors'] += 1
                
                # Small delay between actions
                time.sleep(1)
                
            except Exception as e:
                self.stats['errors'] += 1
                self.stats['last_error'] = str(e)
                self._log(f"Error in automation loop: {e}", "error")
                time.sleep(2)
        
        # Update runtime
        if self.stats['start_time']:
            self.stats['runtime'] = time.time() - self.stats['start_time']
    
    def _execute_action(self, action: str, game_state: Dict) -> bool:
        """Execute an automation action."""
        try:
            if action == "collect_resources":
                result = self.collector.collect_from_producers(
                    self.game_area,
                    self.resize_factor,
                    self.detection_threshold
                )
                if result.get('success'):
                    collected = result.get('collected', 0)
                    if collected > 0:
                        self._log(f"Collected from {collected} producers", "success")
                    return True
                return False
            
            elif action == "fulfill_orders":
                # Scan orders first
                if self.order_board_region:
                    scan_result = self.order_manager.scan_orders(
                        self.order_board_region,
                        self.resize_factor,
                        self.detection_threshold
                    )
                    
                    if scan_result.get('success'):
                        # Fulfill orders
                        fulfill_result = self.order_manager.fulfill_orders()
                        if fulfill_result.get('success'):
                            fulfilled = fulfill_result.get('fulfilled', 0)
                            if fulfilled > 0:
                                coins = fulfill_result.get('coins_earned', 0)
                                self._log(f"Fulfilled {fulfilled} orders (+{coins} coins)", "success")
                            return True
                return False
            
            elif action == "merge_items":
                # Basic merging is handled by the main merge loop
                # This is a placeholder for future merge integration
                self._log("Merge action (handled by main loop)", "info")
                return True
            
            elif action == "repair_buildings":
                # Placeholder for building repair
                self._log("Repair buildings (not yet implemented)", "info")
                return False
            
            elif action == "expand_land":
                # Placeholder for land expansion
                self._log("Expand land (not yet implemented)", "info")
                return False
            
            elif action == "handle_popup":
                popup = self.popup_handler.check_and_handle_popups(self.game_area)
                if popup:
                    self._log(f"Handled popup: {popup.get('type', 'unknown')}", "info")
                    return True
                return False
            
            else:
                self._log(f"Unknown action: {action}", "warning")
                return False
                
        except Exception as e:
            self._log(f"Error executing action {action}: {e}", "error")
            return False
    
    def get_statistics(self) -> Dict:
        """Get automation statistics."""
        current_stats = self.stats.copy()
        
        # Add module statistics
        current_stats['state_machine'] = self.state_machine.get_statistics()
        current_stats['collector'] = self.collector.get_statistics()
        current_stats['order_manager'] = self.order_manager.get_statistics()
        current_stats['energy_manager'] = self.energy_manager.get_statistics()
        
        # Update runtime
        if self.stats['start_time']:
            current_stats['runtime'] = time.time() - self.stats['start_time']
        
        return current_stats
    
    def update_config(self, new_config: Dict):
        """Update orchestrator configuration."""
        self.config.update(new_config)
        self._apply_config()
    
    def set_profile(self, profile_name: str):
        """Set automation profile."""
        if not self.profile_manager:
            self._log("Profile manager not available", "warning")
            return False
        try:
            self.profile_manager.set_active_profile(profile_name)
            profile_config = self.profile_manager.get_active_profile()
            if profile_config:
                self.update_config(profile_config)
                self._log(f"Profile set to: {profile_name}", "success")
                return True
        except Exception as e:
            self._log(f"Failed to set profile: {e}", "error")
        return False
    
    def is_running(self) -> bool:
        """Check if automation is running."""
        return self.is_running
    
    def is_paused(self) -> bool:
        """Check if automation is paused."""
        return self.is_paused

