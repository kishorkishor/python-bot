"""Event Handler for Farm Merge Valley.

Manages dynamic game events including daily challenges,
visitor interactions, and time-limited events.
"""

import time
import random
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

import pyautogui

from game_state_detector import GameStateDetector


class EventHandler:
    """
    Handles detection and participation in game events.
    
    Manages daily challenges, visitor requests, time-limited
    events, and special offers.
    """
    
    def __init__(self, game_state_detector: GameStateDetector):
        self.detector = game_state_detector
        self.events_completed = 0
        self.visitors_handled = 0
        self.last_event_check = 0
        self.event_check_interval = 300  # 5 minutes
        
        # Configuration
        self.config = {
            'participate_in_events': True,
            'accept_visitor_gifts': True,
            'fulfill_visitor_requests': True,
            'join_time_limited_events': True,
            'accept_free_offers': True,
            'skip_paid_offers': True,
            'click_delay': 0.5,
        }
        
        # Tracking
        self.active_events = []
        self.event_history = []  # (timestamp, event_type, result)
        self.daily_challenge_completed = False
        self.last_daily_reset = datetime.now().date()
    
    def can_check_events(self) -> bool:
        """Check if event check cooldown has elapsed."""
        elapsed = time.time() - self.last_event_check
        return elapsed >= self.event_check_interval
    
    def check_for_events(
        self,
        game_area: Tuple[int, int, int, int],
        threshold: float = 0.75
    ) -> Dict:
        """
        Scan for active events.
        
        Args:
            game_area: Game screen region
            threshold: Detection confidence threshold
            
        Returns:
            Scan results with detected events
        """
        if not self.can_check_events():
            return {
                'success': False,
                'reason': 'On cooldown',
                'events': []
            }
        
        # Detect event indicators
        ui_elements = self.detector.detect_ui_elements(
            game_area,
            element_types=[
                'event_icon',
                'daily_challenge',
                'visitor_icon',
                'special_event',
                'gift_icon'
            ],
            threshold=threshold
        )
        
        self.active_events.clear()
        
        # Process detected events
        for element_type, positions in ui_elements.items():
            for position in positions:
                self.active_events.append({
                    'type': element_type,
                    'position': position,
                    'detected_time': time.time()
                })
        
        self.last_event_check = time.time()
        
        # Check if daily challenge needs reset
        self._check_daily_reset()
        
        return {
            'success': True,
            'events': self.active_events,
            'count': len(self.active_events)
        }
    
    def _check_daily_reset(self):
        """Check if daily challenge should reset."""
        today = datetime.now().date()
        if today > self.last_daily_reset:
            self.daily_challenge_completed = False
            self.last_daily_reset = today
    
    def handle_daily_challenge(
        self,
        game_area: Tuple[int, int, int, int]
    ) -> Dict:
        """
        Detect and participate in daily challenge.
        
        Args:
            game_area: Game screen region
            
        Returns:
            Result of challenge handling
        """
        if self.daily_challenge_completed:
            return {
                'success': True,
                'reason': 'Already completed today',
                'participated': False
            }
        
        if not self.config['participate_in_events']:
            return {
                'success': False,
                'reason': 'Event participation disabled',
                'participated': False
            }
        
        # Find daily challenge event
        daily_challenge = None
        for event in self.active_events:
            if event['type'] == 'daily_challenge':
                daily_challenge = event
                break
        
        if not daily_challenge:
            return {
                'success': True,
                'reason': 'No daily challenge found',
                'participated': False
            }
        
        # Click on daily challenge
        success = self._click_event(daily_challenge)
        
        if success:
            self.daily_challenge_completed = True
            self.events_completed += 1
            self.event_history.append({
                'timestamp': time.time(),
                'type': 'daily_challenge',
                'result': 'completed'
            })
            
            print("[EventHandler] Participated in daily challenge")
            
            return {
                'success': True,
                'participated': True
            }
        
        return {
            'success': False,
            'reason': 'Click failed',
            'participated': False
        }
    
    def handle_visitor(
        self,
        visitor_event: Dict
    ) -> Dict:
        """
        Handle visitor interaction (gift or request).
        
        Args:
            visitor_event: Visitor event info
            
        Returns:
            Result of visitor handling
        """
        if not self.config['accept_visitor_gifts'] and \
           not self.config['fulfill_visitor_requests']:
            return {
                'success': False,
                'reason': 'Visitor handling disabled',
                'handled': False
            }
        
        # Click on visitor
        success = self._click_event(visitor_event)
        
        if success:
            time.sleep(self.config['click_delay'])
            
            # Determine if it's a gift or request
            # (Would use detection here in real implementation)
            # For now, just accept/fulfill
            pyautogui.click()  # Click accept/fulfill button
            
            self.visitors_handled += 1
            self.event_history.append({
                'timestamp': time.time(),
                'type': 'visitor',
                'result': 'handled'
            })
            
            print("[EventHandler] Handled visitor")
            
            return {
                'success': True,
                'handled': True
            }
        
        return {
            'success': False,
            'reason': 'Click failed',
            'handled': False
        }
    
    def handle_special_offer(
        self,
        offer_event: Dict
    ) -> Dict:
        """
        Handle special offer (accept free, skip paid).
        
        Args:
            offer_event: Offer event info
            
        Returns:
            Result of offer handling
        """
        # Click on offer to see details
        success = self._click_event(offer_event)
        
        if not success:
            return {
                'success': False,
                'reason': 'Click failed',
                'handled': False
            }
        
        time.sleep(self.config['click_delay'])
        
        # Detect if offer is free or paid
        # (Would use detection here in real implementation)
        # For now, assume we can detect "Free" text or price
        
        is_free = True  # Placeholder logic
        
        if is_free and self.config['accept_free_offers']:
            # Click accept button
            pyautogui.click()
            
            self.event_history.append({
                'timestamp': time.time(),
                'type': 'free_offer',
                'result': 'accepted'
            })
            
            print("[EventHandler] Accepted free offer")
            
            return {
                'success': True,
                'handled': True,
                'action': 'accepted'
            }
        
        elif not is_free and self.config['skip_paid_offers']:
            # Click close/skip button
            pyautogui.press('escape')
            
            print("[EventHandler] Skipped paid offer")
            
            return {
                'success': True,
                'handled': True,
                'action': 'skipped'
            }
        
        return {
            'success': True,
            'handled': False,
            'action': 'none'
        }
    
    def handle_time_limited_event(
        self,
        event: Dict
    ) -> Dict:
        """
        Handle time-limited special event.
        
        Args:
            event: Event info
            
        Returns:
            Result of event handling
        """
        if not self.config['join_time_limited_events']:
            return {
                'success': False,
                'reason': 'Time-limited events disabled',
                'joined': False
            }
        
        # Click on event
        success = self._click_event(event)
        
        if success:
            time.sleep(self.config['click_delay'])
            
            # Click join/participate button
            pyautogui.click()
            
            self.events_completed += 1
            self.event_history.append({
                'timestamp': time.time(),
                'type': 'time_limited_event',
                'result': 'joined'
            })
            
            print("[EventHandler] Joined time-limited event")
            
            return {
                'success': True,
                'joined': True
            }
        
        return {
            'success': False,
            'reason': 'Click failed',
            'joined': False
        }
    
    def _click_event(self, event: Dict) -> bool:
        """
        Click on an event icon/button.
        
        Args:
            event: Event info with position
            
        Returns:
            True if click succeeded
        """
        try:
            position = event['position']
            
            # Add randomness
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            
            target_x = position[0] + offset_x
            target_y = position[1] + offset_y
            
            # Move and click
            pyautogui.moveTo(target_x, target_y, duration=0.2)
            pyautogui.click()
            
            return True
        
        except Exception as e:
            print(f"[EventHandler] Failed to click event: {e}")
            return False
    
    def process_all_events(
        self,
        game_area: Tuple[int, int, int, int]
    ) -> Dict:
        """
        Process all detected events.
        
        Args:
            game_area: Game screen region
            
        Returns:
            Summary of event processing
        """
        results = {
            'daily_challenge': None,
            'visitors': 0,
            'special_offers': 0,
            'time_limited': 0
        }
        
        # Handle daily challenge first (highest priority)
        if not self.daily_challenge_completed:
            results['daily_challenge'] = self.handle_daily_challenge(game_area)
        
        # Handle other events
        for event in self.active_events:
            event_type = event['type']
            
            if event_type == 'visitor_icon':
                result = self.handle_visitor(event)
                if result.get('handled'):
                    results['visitors'] += 1
            
            elif event_type == 'special_event':
                result = self.handle_time_limited_event(event)
                if result.get('joined'):
                    results['time_limited'] += 1
            
            elif event_type == 'gift_icon':
                result = self.handle_special_offer(event)
                if result.get('handled'):
                    results['special_offers'] += 1
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        Get event handling statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            'events_completed': self.events_completed,
            'visitors_handled': self.visitors_handled,
            'daily_challenge_completed': self.daily_challenge_completed,
            'active_events': len(self.active_events),
            'event_history_length': len(self.event_history)
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.events_completed = 0
        self.visitors_handled = 0
        self.event_history.clear()
    
    def update_config(self, new_config: Dict):
        """
        Update event handler configuration.
        
        Args:
            new_config: Dictionary of config updates
        """
        self.config.update(new_config)


class SmartEventHandler(EventHandler):
    """
    Enhanced event handler with reward optimization.
    
    Prioritizes events based on reward value and
    tracks event patterns.
    """
    
    def __init__(self, game_state_detector: GameStateDetector):
        super().__init__(game_state_detector)
        self.event_rewards = {}  # Track rewards from each event type
        self.event_frequencies = {}  # Track how often events appear
    
    def calculate_event_priority(self, event: Dict) -> float:
        """
        Calculate priority score for an event.
        
        Args:
            event: Event to evaluate
            
        Returns:
            Priority score (higher = more important)
        """
        event_type = event['type']
        
        # Base priorities
        priorities = {
            'daily_challenge': 100,
            'time_limited_event': 80,
            'visitor_icon': 60,
            'gift_icon': 40,
            'special_event': 50
        }
        
        base_priority = priorities.get(event_type, 30)
        
        # Adjust based on historical rewards
        avg_reward = self.event_rewards.get(event_type, 0)
        reward_multiplier = 1.0 + (avg_reward / 100.0)
        
        return base_priority * reward_multiplier
    
    def get_prioritized_events(self) -> List[Dict]:
        """
        Get events sorted by priority.
        
        Returns:
            List of events sorted by priority
        """
        if not self.active_events:
            return []
        
        # Calculate priority for each event
        prioritized = []
        for event in self.active_events:
            priority = self.calculate_event_priority(event)
            prioritized.append({
                'event': event,
                'priority': priority
            })
        
        # Sort by priority
        prioritized.sort(key=lambda x: x['priority'], reverse=True)
        
        return [item['event'] for item in prioritized]
    
    def track_event_reward(self, event_type: str, reward_value: float):
        """
        Track reward received from an event.
        
        Args:
            event_type: Type of event
            reward_value: Value of reward received
        """
        if event_type not in self.event_rewards:
            self.event_rewards[event_type] = []
        
        self.event_rewards[event_type].append(reward_value)
    
    def get_average_reward(self, event_type: str) -> float:
        """
        Get average reward for an event type.
        
        Args:
            event_type: Event type to check
            
        Returns:
            Average reward value
        """
        rewards = self.event_rewards.get(event_type, [])
        if not rewards:
            return 0.0
        
        return sum(rewards) / len(rewards)
    
    def process_all_events(
        self,
        game_area: Tuple[int, int, int, int]
    ) -> Dict:
        """Process events in priority order."""
        # Get prioritized event list
        prioritized_events = self.get_prioritized_events()
        
        # Temporarily replace active_events with prioritized list
        original_events = self.active_events
        self.active_events = prioritized_events
        
        # Process events
        results = super().process_all_events(game_area)
        
        # Restore original list
        self.active_events = original_events
        
        return results



