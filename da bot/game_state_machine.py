"""Game State Machine for Farm Merge Valley Automation.

Manages automation states and prioritizes actions based on
game conditions and resource availability.
"""

import time
from enum import Enum, auto
from queue import PriorityQueue
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field


class GameState(Enum):
    """Possible automation states."""
    IDLE = auto()
    MERGING = auto()
    COLLECTING = auto()
    FULFILLING_ORDERS = auto()
    EXPANDING = auto()
    REPAIRING = auto()
    HANDLING_POPUP = auto()
    PAUSED = auto()
    ERROR = auto()


class ActionPriority(Enum):
    """Action priority levels."""
    CRITICAL = 1  # Popups, errors
    HIGH = 2      # Resource collection, order fulfillment
    MEDIUM = 3    # Merging, repairs
    LOW = 4       # Expansion, optimization
    IDLE = 5      # Background tasks


@dataclass(order=True)
class Action:
    """Represents an automation action with priority."""
    priority: int
    name: str = field(compare=False)
    callback: Callable = field(compare=False)
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    cooldown: float = field(default=0.0, compare=False)
    last_executed: float = field(default=0.0, compare=False)
    
    def can_execute(self) -> bool:
        """Check if action is off cooldown."""
        if self.cooldown == 0:
            return True
        return (time.time() - self.last_executed) >= self.cooldown
    
    def execute(self):
        """Execute the action callback."""
        try:
            self.callback(*self.args, **self.kwargs)
            self.last_executed = time.time()
            return True
        except Exception as e:
            print(f"[StateMachine] Action '{self.name}' failed: {e}")
            return False


class GameStateMachine:
    """
    State machine for managing Farm Merge Valley automation.
    
    Tracks current state, prioritizes actions, and coordinates
    different automation modules.
    """
    
    def __init__(self):
        self.current_state = GameState.IDLE
        self.previous_state = GameState.IDLE
        self.action_queue = PriorityQueue()
        self.state_history: List[tuple] = []  # (state, timestamp)
        self.state_start_time = time.time()
        
        # Configuration
        self.config = {
            'collect_resources': True,
            'fulfill_orders': True,
            'auto_merge': True,
            'auto_expand': False,
            'auto_repair': True,
            'handle_popups': True,
            'energy_threshold': 20,
            'coins_threshold_expand': 5000,
        }
        
        # State tracking
        self.resources_collected = 0
        self.orders_fulfilled = 0
        self.merges_completed = 0
        self.popups_handled = 0
        
        # Cooldowns (seconds)
        self.cooldowns = {
            'collect': 30,      # Check for collection every 30s
            'orders': 60,       # Check orders every minute
            'merge': 10,        # Merge check every 10s
            'expand': 300,      # Check expansion every 5 min
            'repair': 120,      # Check repairs every 2 min
        }
    
    def transition_to(self, new_state: GameState, reason: str = ""):
        """
        Transition to a new state.
        
        Args:
            new_state: Target state
            reason: Optional reason for transition
        """
        if new_state == self.current_state:
            return
        
        self.previous_state = self.current_state
        self.current_state = new_state
        
        # Record history
        self.state_history.append((new_state, time.time(), reason))
        self.state_start_time = time.time()
        
        print(f"[StateMachine] {self.previous_state.name} → {new_state.name}" + 
              (f" ({reason})" if reason else ""))
    
    def get_current_state(self) -> GameState:
        """Get current automation state."""
        return self.current_state
    
    def get_state_duration(self) -> float:
        """Get how long we've been in current state (seconds)."""
        return time.time() - self.state_start_time
    
    def add_action(
        self,
        name: str,
        callback: Callable,
        priority: ActionPriority,
        args: tuple = (),
        kwargs: dict = None,
        cooldown: float = 0.0
    ):
        """
        Add an action to the priority queue.
        
        Args:
            name: Action name
            callback: Function to execute
            priority: Action priority level
            args: Positional arguments for callback
            kwargs: Keyword arguments for callback
            cooldown: Minimum seconds between executions
        """
        action = Action(
            priority=priority.value,
            name=name,
            callback=callback,
            args=args,
            kwargs=kwargs or {},
            cooldown=cooldown
        )
        self.action_queue.put(action)
    
    def get_next_action(self) -> Optional[Action]:
        """
        Get the next action to execute from priority queue.
        
        Returns:
            Next action if available and ready, None otherwise
        """
        if self.action_queue.empty():
            return None
        
        # Peek at highest priority action
        action = self.action_queue.get()
        
        # Check if it's ready to execute
        if action.can_execute():
            return action
        else:
            # Put it back and wait
            self.action_queue.put(action)
            return None
    
    def should_collect_resources(self, game_state: Dict) -> bool:
        """
        Determine if we should collect resources.
        
        Args:
            game_state: Current game state from detector
            
        Returns:
            True if collection should happen
        """
        if not self.config['collect_resources']:
            return False
        
        # Check if there are ready producers
        producers_ready = game_state.get('producers_ready', [])
        return len(producers_ready) > 0
    
    def should_fulfill_orders(self, game_state: Dict) -> bool:
        """
        Determine if we should fulfill orders.
        
        Args:
            game_state: Current game state from detector
            
        Returns:
            True if order fulfillment should happen
        """
        if not self.config['fulfill_orders']:
            return False
        
        # Check if there are active orders
        active_orders = game_state.get('active_orders', [])
        return len(active_orders) > 0
    
    def should_merge(self, game_state: Dict) -> bool:
        """
        Determine if we should perform merging.
        
        Args:
            game_state: Current game state from detector
            
        Returns:
            True if merging should happen
        """
        if not self.config['auto_merge']:
            return False
        
        merge_ready = game_state.get('merge_ready')
        if merge_ready is None:
            return False
        
        if isinstance(merge_ready, (list, tuple, set)):
            return len(merge_ready) > 0
        
        if isinstance(merge_ready, dict):
            return any(bool(value) for value in merge_ready.values())
        
        return bool(merge_ready)
    
    def should_expand(self, game_state: Dict) -> bool:
        """
        Determine if we should expand land.
        
        Args:
            game_state: Current game state from detector
            
        Returns:
            True if expansion should happen
        """
        if not self.config['auto_expand']:
            return False
        
        # Check coin threshold
        coins = game_state.get('coins')
        if coins is None:
            return False
        
        return coins >= self.config['coins_threshold_expand']
    
    def should_repair(self, game_state: Dict) -> bool:
        """
        Determine if we should repair buildings.
        
        Args:
            game_state: Current game state from detector
            
        Returns:
            True if repairs should happen
        """
        if not self.config['auto_repair']:
            return False
        
        # Check if repair buttons are visible
        ui_elements = game_state.get('ui_elements', {})
        return 'repair_button' in ui_elements
    
    def should_handle_popup(self, game_state: Dict) -> bool:
        """
        Determine if there's a popup to handle.
        
        Args:
            game_state: Current game state from detector
            
        Returns:
            True if popup handling is needed
        """
        if not self.config['handle_popups']:
            return False
        
        popup = game_state.get('popup')
        return popup is not None
    
    def has_sufficient_energy(self, game_state: Dict, required: int = None) -> bool:
        """
        Check if we have enough energy for energy-intensive tasks.
        
        Args:
            game_state: Current game state from detector
            required: Specific energy requirement (uses threshold if None)
            
        Returns:
            True if energy is sufficient
        """
        energy = game_state.get('energy')
        if energy is None:
            return True  # Assume OK if we can't read it
        
        threshold = required if required is not None else self.config['energy_threshold']
        return energy >= threshold
    
    def decide_next_action(self, game_state: Dict) -> Optional[str]:
        """
        Decide what action to take next based on game state.
        
        Args:
            game_state: Current game state from detector
            
        Returns:
            Action name to execute, or None for idle
        """
        # Priority 1: Handle popups (blocks everything)
        if self.should_handle_popup(game_state):
            self.transition_to(GameState.HANDLING_POPUP, "Popup detected")
            return "handle_popup"
        
        # Priority 2: Collect resources (high value, quick)
        if self.should_collect_resources(game_state):
            self.transition_to(GameState.COLLECTING, "Producers ready")
            return "collect_resources"
        
        # Priority 3: Fulfill orders (generates coins)
        if self.should_fulfill_orders(game_state):
            self.transition_to(GameState.FULFILLING_ORDERS, "Orders available")
            return "fulfill_orders"
        
        # Priority 4: Merge items (core gameplay)
        if self.should_merge(game_state):
            self.transition_to(GameState.MERGING, "Merge cycle")
            return "merge_items"
        
        # Priority 5: Repair buildings (unlocks features)
        if self.should_repair(game_state) and self.has_sufficient_energy(game_state):
            self.transition_to(GameState.REPAIRING, "Repairs available")
            return "repair_buildings"
        
        # Priority 6: Expand land (long-term growth)
        if self.should_expand(game_state) and self.has_sufficient_energy(game_state):
            self.transition_to(GameState.EXPANDING, "Expansion ready")
            return "expand_land"
        
        # Default: Idle
        self.transition_to(GameState.IDLE, "No actions needed")
        return None
    
    def update_config(self, new_config: Dict):
        """
        Update state machine configuration.
        
        Args:
            new_config: Dictionary of config updates
        """
        self.config.update(new_config)
        print(f"[StateMachine] Config updated: {new_config}")
    
    def get_statistics(self) -> Dict:
        """
        Get automation statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            'current_state': self.current_state.name,
            'state_duration': self.get_state_duration(),
            'resources_collected': self.resources_collected,
            'orders_fulfilled': self.orders_fulfilled,
            'merges_completed': self.merges_completed,
            'popups_handled': self.popups_handled,
            'state_history_length': len(self.state_history)
        }
    
    def reset_statistics(self):
        """Reset all statistics counters."""
        self.resources_collected = 0
        self.orders_fulfilled = 0
        self.merges_completed = 0
        self.popups_handled = 0
        self.state_history.clear()
    
    def pause(self):
        """Pause automation."""
        self.transition_to(GameState.PAUSED, "Manual pause")
    
    def resume(self):
        """Resume automation from pause."""
        self.transition_to(GameState.IDLE, "Resumed")
    
    def is_paused(self) -> bool:
        """Check if automation is paused."""
        return self.current_state == GameState.PAUSED
    
    def is_error(self) -> bool:
        """Check if automation is in error state."""
        return self.current_state == GameState.ERROR
    
    def set_error(self, reason: str):
        """Set error state."""
        self.transition_to(GameState.ERROR, f"Error: {reason}")



