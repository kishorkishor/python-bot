"""Automation Profiles for Farm Merge Valley.

Defines multiple automation strategies with different
priorities and behaviors (aggressive, balanced, passive, custom).
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class AutomationProfile:
    """Represents an automation strategy profile."""
    name: str
    description: str
    
    # Core automation toggles
    auto_merge: bool = True
    collect_resources: bool = True
    fulfill_orders: bool = True
    handle_popups: bool = True
    
    # Advanced features
    auto_expand: bool = False
    auto_repair: bool = True
    participate_in_events: bool = True
    
    # Priorities and thresholds
    merge_priority: str = "balanced"  # "speed", "balanced", "efficiency"
    energy_threshold: int = 20
    coin_threshold_expand: int = 5000
    max_coins_per_session: int = 10000
    
    # Timing and delays
    merge_delay: float = 0.05
    click_delay: float = 0.5
    scan_interval_resources: int = 30
    scan_interval_orders: int = 60
    
    # Safety limits
    max_actions_per_minute: int = 60
    randomize_delays: bool = True
    
    def to_dict(self) -> Dict:
        """Convert profile to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AutomationProfile':
        """Create profile from dictionary."""
        return cls(**data)


class ProfileManager:
    """
    Manages automation profiles.
    
    Loads, saves, and switches between different automation
    strategies.
    """
    
    def __init__(self, config_file: str = "farm_merger_profiles.json"):
        self.config_file = Path(config_file)
        self.profiles: Dict[str, AutomationProfile] = {}
        self.active_profile_name: Optional[str] = None
        
        # Load or create default profiles
        if self.config_file.exists():
            self.load_profiles()
        else:
            self._create_default_profiles()
            self.save_profiles()
    
    def _create_default_profiles(self):
        """Create default automation profiles."""
        # Aggressive profile - max coins/hour
        self.profiles['aggressive'] = AutomationProfile(
            name="Aggressive",
            description="Maximum coin generation and activity. High energy usage.",
            auto_merge=True,
            collect_resources=True,
            fulfill_orders=True,
            handle_popups=True,
            auto_expand=True,
            auto_repair=True,
            participate_in_events=True,
            merge_priority="speed",
            energy_threshold=10,  # Lower threshold, more aggressive
            coin_threshold_expand=3000,  # Expand sooner
            max_coins_per_session=20000,
            merge_delay=0.03,  # Faster merging
            click_delay=0.3,
            scan_interval_resources=20,  # More frequent scans
            scan_interval_orders=45,
            max_actions_per_minute=80,
            randomize_delays=True
        )
        
        # Balanced profile - mix of growth and resource building
        self.profiles['balanced'] = AutomationProfile(
            name="Balanced",
            description="Balanced approach to growth and resource management.",
            auto_merge=True,
            collect_resources=True,
            fulfill_orders=True,
            handle_popups=True,
            auto_expand=False,  # Manual expansion
            auto_repair=True,
            participate_in_events=True,
            merge_priority="balanced",
            energy_threshold=20,
            coin_threshold_expand=5000,
            max_coins_per_session=10000,
            merge_delay=0.05,
            click_delay=0.5,
            scan_interval_resources=30,
            scan_interval_orders=60,
            max_actions_per_minute=60,
            randomize_delays=True
        )
        
        # Passive profile - minimal actions, focus on collection
        self.profiles['passive'] = AutomationProfile(
            name="Passive",
            description="Low activity mode. Focus on collection and simple tasks.",
            auto_merge=True,
            collect_resources=True,
            fulfill_orders=True,
            handle_popups=True,
            auto_expand=False,
            auto_repair=False,  # Manual repairs
            participate_in_events=False,  # Skip events
            merge_priority="efficiency",
            energy_threshold=30,  # Higher threshold, more conservative
            coin_threshold_expand=10000,
            max_coins_per_session=5000,
            merge_delay=0.1,  # Slower merging
            click_delay=0.8,
            scan_interval_resources=60,  # Less frequent scans
            scan_interval_orders=120,
            max_actions_per_minute=30,
            randomize_delays=True
        )
        
        # Merge-only profile - focus on merging
        self.profiles['merge_only'] = AutomationProfile(
            name="Merge Only",
            description="Focus exclusively on merging items.",
            auto_merge=True,
            collect_resources=False,
            fulfill_orders=False,
            handle_popups=True,
            auto_expand=False,
            auto_repair=False,
            participate_in_events=False,
            merge_priority="speed",
            energy_threshold=50,
            coin_threshold_expand=999999,  # Never expand
            max_coins_per_session=0,
            merge_delay=0.05,
            click_delay=0.5,
            scan_interval_resources=999,
            scan_interval_orders=999,
            max_actions_per_minute=80,
            randomize_delays=True
        )
        
        # Set balanced as default
        self.active_profile_name = 'balanced'
    
    def get_profile(self, name: str) -> Optional[AutomationProfile]:
        """
        Get a profile by name.
        
        Args:
            name: Profile name
            
        Returns:
            Profile or None if not found
        """
        return self.profiles.get(name)
    
    def get_active_profile(self) -> Optional[AutomationProfile]:
        """
        Get the currently active profile.
        
        Returns:
            Active profile or None
        """
        if self.active_profile_name:
            return self.profiles.get(self.active_profile_name)
        return None
    
    def set_active_profile(self, name: str) -> bool:
        """
        Set the active profile.
        
        Args:
            name: Profile name to activate
            
        Returns:
            True if profile was activated
        """
        if name in self.profiles:
            self.active_profile_name = name
            print(f"[Profiles] Activated profile: {name}")
            return True
        
        print(f"[Profiles] Profile not found: {name}")
        return False
    
    def add_profile(self, profile: AutomationProfile) -> bool:
        """
        Add a new profile.
        
        Args:
            profile: Profile to add
            
        Returns:
            True if profile was added
        """
        profile_key = profile.name.lower().replace(' ', '_')
        
        if profile_key in self.profiles:
            print(f"[Profiles] Profile already exists: {profile.name}")
            return False
        
        self.profiles[profile_key] = profile
        print(f"[Profiles] Added profile: {profile.name}")
        return True
    
    def update_profile(self, name: str, updates: Dict) -> bool:
        """
        Update an existing profile.
        
        Args:
            name: Profile name
            updates: Dictionary of updates
            
        Returns:
            True if profile was updated
        """
        if name not in self.profiles:
            print(f"[Profiles] Profile not found: {name}")
            return False
        
        profile = self.profiles[name]
        
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        print(f"[Profiles] Updated profile: {name}")
        return True
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a profile.
        
        Args:
            name: Profile name
            
        Returns:
            True if profile was deleted
        """
        if name not in self.profiles:
            return False
        
        # Don't delete if it's the active profile
        if name == self.active_profile_name:
            print(f"[Profiles] Cannot delete active profile: {name}")
            return False
        
        del self.profiles[name]
        print(f"[Profiles] Deleted profile: {name}")
        return True
    
    def list_profiles(self) -> List[str]:
        """
        Get list of all profile names.
        
        Returns:
            List of profile names
        """
        return list(self.profiles.keys())
    
    def get_profile_info(self, name: str) -> Optional[Dict]:
        """
        Get profile information.
        
        Args:
            name: Profile name
            
        Returns:
            Profile info dictionary or None
        """
        profile = self.profiles.get(name)
        if profile:
            return {
                'name': profile.name,
                'description': profile.description,
                'is_active': name == self.active_profile_name
            }
        return None
    
    def save_profiles(self) -> bool:
        """
        Save profiles to JSON file.
        
        Returns:
            True if save succeeded
        """
        try:
            data = {
                'active_profile': self.active_profile_name,
                'profiles': {
                    name: profile.to_dict()
                    for name, profile in self.profiles.items()
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"[Profiles] Saved profiles to {self.config_file}")
            return True
        
        except Exception as e:
            print(f"[Profiles] Failed to save profiles: {e}")
            return False
    
    def load_profiles(self) -> bool:
        """
        Load profiles from JSON file.
        
        Returns:
            True if load succeeded
        """
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            self.active_profile_name = data.get('active_profile')
            
            self.profiles.clear()
            for name, profile_data in data.get('profiles', {}).items():
                self.profiles[name] = AutomationProfile.from_dict(profile_data)
            
            print(f"[Profiles] Loaded {len(self.profiles)} profiles from {self.config_file}")
            return True
        
        except Exception as e:
            print(f"[Profiles] Failed to load profiles: {e}")
            return False
    
    def export_profile(self, name: str, filename: str) -> bool:
        """
        Export a profile to a separate file.
        
        Args:
            name: Profile name
            filename: Output filename
            
        Returns:
            True if export succeeded
        """
        profile = self.profiles.get(name)
        if not profile:
            return False
        
        try:
            with open(filename, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            
            print(f"[Profiles] Exported profile '{name}' to {filename}")
            return True
        
        except Exception as e:
            print(f"[Profiles] Failed to export profile: {e}")
            return False
    
    def import_profile(self, filename: str) -> bool:
        """
        Import a profile from a file.
        
        Args:
            filename: Input filename
            
        Returns:
            True if import succeeded
        """
        try:
            with open(filename, 'r') as f:
                profile_data = json.load(f)
            
            profile = AutomationProfile.from_dict(profile_data)
            return self.add_profile(profile)
        
        except Exception as e:
            print(f"[Profiles] Failed to import profile: {e}")
            return False


class ProfileApplicator:
    """
    Applies profile settings to automation modules.
    
    Configures all automation components based on
    the active profile.
    """
    
    def __init__(self, profile_manager: ProfileManager):
        self.profile_manager = profile_manager
    
    def apply_to_state_machine(self, state_machine):
        """
        Apply profile settings to game state machine.
        
        Args:
            state_machine: GameStateMachine instance
        """
        profile = self.profile_manager.get_active_profile()
        if not profile:
            return
        
        state_machine.update_config({
            'collect_resources': profile.collect_resources,
            'fulfill_orders': profile.fulfill_orders,
            'auto_merge': profile.auto_merge,
            'auto_expand': profile.auto_expand,
            'auto_repair': profile.auto_repair,
            'handle_popups': profile.handle_popups,
            'energy_threshold': profile.energy_threshold,
            'coins_threshold_expand': profile.coin_threshold_expand,
        })
    
    def apply_to_collector(self, collector):
        """
        Apply profile settings to resource collector.
        
        Args:
            collector: ResourceCollector instance
        """
        profile = self.profile_manager.get_active_profile()
        if not profile:
            return
        
        collector.update_config({
            'click_delay_min': profile.click_delay * 0.6,
            'click_delay_max': profile.click_delay * 1.4,
            'scan_interval': profile.scan_interval_resources,
        })
    
    def apply_to_order_manager(self, order_manager):
        """
        Apply profile settings to order manager.
        
        Args:
            order_manager: OrderManager instance
        """
        profile = self.profile_manager.get_active_profile()
        if not profile:
            return
        
        order_manager.update_config({
            'auto_fulfill': profile.fulfill_orders,
            'scan_interval': profile.scan_interval_orders,
            'click_delay': profile.click_delay,
        })
    
    def apply_to_energy_manager(self, energy_manager):
        """
        Apply profile settings to energy manager.
        
        Args:
            energy_manager: EnergyManager instance
        """
        profile = self.profile_manager.get_active_profile()
        if not profile:
            return
        
        energy_manager.update_config({
            'low_energy_threshold': profile.energy_threshold,
            'pause_threshold': max(profile.energy_threshold - 10, 5),
            'resume_threshold': profile.energy_threshold + 10,
        })
    
    def apply_to_expansion_manager(self, expansion_manager):
        """
        Apply profile settings to expansion manager.
        
        Args:
            expansion_manager: ExpansionManager instance
        """
        profile = self.profile_manager.get_active_profile()
        if not profile:
            return
        
        expansion_manager.update_config({
            'auto_expand': profile.auto_expand,
            'coin_threshold': profile.coin_threshold_expand,
            'max_coins_per_session': profile.max_coins_per_session,
            'click_delay': profile.click_delay,
        })
    
    def apply_to_building_manager(self, building_manager):
        """
        Apply profile settings to building manager.
        
        Args:
            building_manager: BuildingManager instance
        """
        profile = self.profile_manager.get_active_profile()
        if not profile:
            return
        
        building_manager.update_config({
            'auto_repair': profile.auto_repair,
            'click_delay': profile.click_delay,
        })
    
    def apply_to_event_handler(self, event_handler):
        """
        Apply profile settings to event handler.
        
        Args:
            event_handler: EventHandler instance
        """
        profile = self.profile_manager.get_active_profile()
        if not profile:
            return
        
        event_handler.update_config({
            'participate_in_events': profile.participate_in_events,
            'click_delay': profile.click_delay,
        })
    
    def apply_to_all(self, modules: Dict):
        """
        Apply profile settings to all automation modules.
        
        Args:
            modules: Dictionary of module instances
        """
        profile = self.profile_manager.get_active_profile()
        if not profile:
            print("[ProfileApplicator] No active profile")
            return
        
        print(f"[ProfileApplicator] Applying profile: {profile.name}")
        
        if 'state_machine' in modules:
            self.apply_to_state_machine(modules['state_machine'])
        
        if 'collector' in modules:
            self.apply_to_collector(modules['collector'])
        
        if 'order_manager' in modules:
            self.apply_to_order_manager(modules['order_manager'])
        
        if 'energy_manager' in modules:
            self.apply_to_energy_manager(modules['energy_manager'])
        
        if 'expansion_manager' in modules:
            self.apply_to_expansion_manager(modules['expansion_manager'])
        
        if 'building_manager' in modules:
            self.apply_to_building_manager(modules['building_manager'])
        
        if 'event_handler' in modules:
            self.apply_to_event_handler(modules['event_handler'])
        
        print(f"[ProfileApplicator] Profile '{profile.name}' applied successfully")



