"""Telemetry and Analytics System for Farm Merge Valley.

Tracks automation performance metrics, session data,
and success/failure rates for analysis.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict


class TelemetryCollector:
    """
    Collects and logs automation performance metrics.
    
    Tracks merges, resources, coins, orders, and other
    automation activities for analysis.
    """
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.session_start = time.time()
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Metrics
        self.metrics = {
            'merges': {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'by_item': defaultdict(int)
            },
            'resources': {
                'collected': 0,
                'by_type': defaultdict(int)
            },
            'orders': {
                'fulfilled': 0,
                'coins_earned': 0,
                'by_type': defaultdict(int)
            },
            'energy': {
                'spent': 0,
                'pauses': 0
            },
            'coins': {
                'earned': 0,
                'spent': 0,
                'net': 0
            },
            'popups': {
                'handled': 0,
                'by_type': defaultdict(int)
            },
            'events': {
                'completed': 0,
                'by_type': defaultdict(int)
            },
            'expansions': {
                'purchased': 0,
                'coins_spent': 0
            },
            'buildings': {
                'repaired': 0
            }
        }
        
        # Event log
        self.event_log = []
        
        # Performance tracking
        self.performance = {
            'uptime': 0,
            'active_time': 0,
            'idle_time': 0,
            'error_count': 0
        }
    
    def log_event(self, event_type: str, data: Dict):
        """
        Log an automation event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'data': data
        }
        
        self.event_log.append(event)
    
    def record_merge(self, item_name: str, success: bool):
        """
        Record a merge operation.
        
        Args:
            item_name: Name of merged item
            success: Whether merge succeeded
        """
        self.metrics['merges']['total'] += 1
        
        if success:
            self.metrics['merges']['successful'] += 1
            self.metrics['merges']['by_item'][item_name] += 1
        else:
            self.metrics['merges']['failed'] += 1
        
        self.log_event('merge', {
            'item': item_name,
            'success': success
        })
    
    def record_resource_collection(self, resource_type: str, quantity: int = 1):
        """
        Record resource collection.
        
        Args:
            resource_type: Type of resource
            quantity: Amount collected
        """
        self.metrics['resources']['collected'] += quantity
        self.metrics['resources']['by_type'][resource_type] += quantity
        
        self.log_event('resource_collection', {
            'type': resource_type,
            'quantity': quantity
        })
    
    def record_order_fulfillment(self, order_type: str, coins_earned: int):
        """
        Record order fulfillment.
        
        Args:
            order_type: Type of order
            coins_earned: Coins earned from order
        """
        self.metrics['orders']['fulfilled'] += 1
        self.metrics['orders']['coins_earned'] += coins_earned
        self.metrics['orders']['by_type'][order_type] += 1
        
        self.metrics['coins']['earned'] += coins_earned
        self.metrics['coins']['net'] += coins_earned
        
        self.log_event('order_fulfillment', {
            'type': order_type,
            'coins': coins_earned
        })
    
    def record_energy_spent(self, amount: int, task: str):
        """
        Record energy expenditure.
        
        Args:
            amount: Energy spent
            task: Task that consumed energy
        """
        self.metrics['energy']['spent'] += amount
        
        self.log_event('energy_spent', {
            'amount': amount,
            'task': task
        })
    
    def record_energy_pause(self):
        """Record an energy-related pause."""
        self.metrics['energy']['pauses'] += 1
        self.log_event('energy_pause', {})
    
    def record_popup_handled(self, popup_type: str):
        """
        Record popup handling.
        
        Args:
            popup_type: Type of popup
        """
        self.metrics['popups']['handled'] += 1
        self.metrics['popups']['by_type'][popup_type] += 1
        
        self.log_event('popup_handled', {
            'type': popup_type
        })
    
    def record_event_completion(self, event_type: str):
        """
        Record event completion.
        
        Args:
            event_type: Type of event
        """
        self.metrics['events']['completed'] += 1
        self.metrics['events']['by_type'][event_type] += 1
        
        self.log_event('event_completed', {
            'type': event_type
        })
    
    def record_expansion(self, coins_spent: int):
        """
        Record land expansion.
        
        Args:
            coins_spent: Coins spent on expansion
        """
        self.metrics['expansions']['purchased'] += 1
        self.metrics['expansions']['coins_spent'] += coins_spent
        
        self.metrics['coins']['spent'] += coins_spent
        self.metrics['coins']['net'] -= coins_spent
        
        self.log_event('expansion', {
            'coins_spent': coins_spent
        })
    
    def record_building_repair(self, building_type: str):
        """
        Record building repair.
        
        Args:
            building_type: Type of building
        """
        self.metrics['buildings']['repaired'] += 1
        
        self.log_event('building_repair', {
            'type': building_type
        })
    
    def record_error(self, error_type: str, details: str):
        """
        Record an error.
        
        Args:
            error_type: Type of error
            details: Error details
        """
        self.performance['error_count'] += 1
        
        self.log_event('error', {
            'type': error_type,
            'details': details
        })
    
    def update_performance(self, active: bool):
        """
        Update performance metrics.
        
        Args:
            active: Whether automation is actively working
        """
        self.performance['uptime'] = time.time() - self.session_start
        
        if active:
            self.performance['active_time'] += 1
        else:
            self.performance['idle_time'] += 1
    
    def get_metrics_summary(self) -> Dict:
        """
        Get summary of all metrics.
        
        Returns:
            Dictionary of metrics
        """
        uptime_hours = self.performance['uptime'] / 3600
        
        return {
            'session_id': self.session_id,
            'uptime_hours': round(uptime_hours, 2),
            'merges': {
                'total': self.metrics['merges']['total'],
                'successful': self.metrics['merges']['successful'],
                'failed': self.metrics['merges']['failed'],
                'success_rate': self._calculate_rate(
                    self.metrics['merges']['successful'],
                    self.metrics['merges']['total']
                ),
                'per_hour': self._calculate_per_hour(
                    self.metrics['merges']['successful'],
                    uptime_hours
                )
            },
            'resources': {
                'collected': self.metrics['resources']['collected'],
                'per_hour': self._calculate_per_hour(
                    self.metrics['resources']['collected'],
                    uptime_hours
                )
            },
            'orders': {
                'fulfilled': self.metrics['orders']['fulfilled'],
                'coins_earned': self.metrics['orders']['coins_earned'],
                'per_hour': self._calculate_per_hour(
                    self.metrics['orders']['fulfilled'],
                    uptime_hours
                )
            },
            'coins': {
                'earned': self.metrics['coins']['earned'],
                'spent': self.metrics['coins']['spent'],
                'net': self.metrics['coins']['net'],
                'per_hour': self._calculate_per_hour(
                    self.metrics['coins']['earned'],
                    uptime_hours
                )
            },
            'popups_handled': self.metrics['popups']['handled'],
            'events_completed': self.metrics['events']['completed'],
            'expansions': self.metrics['expansions']['purchased'],
            'buildings_repaired': self.metrics['buildings']['repaired'],
            'errors': self.performance['error_count']
        }
    
    def _calculate_rate(self, numerator: int, denominator: int) -> float:
        """Calculate percentage rate."""
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)
    
    def _calculate_per_hour(self, count: int, hours: float) -> float:
        """Calculate per-hour rate."""
        if hours == 0:
            return 0.0
        return round(count / hours, 2)
    
    def get_detailed_metrics(self) -> Dict:
        """
        Get detailed metrics breakdown.
        
        Returns:
            Detailed metrics dictionary
        """
        return {
            'session_id': self.session_id,
            'session_start': datetime.fromtimestamp(self.session_start).isoformat(),
            'uptime_seconds': self.performance['uptime'],
            'metrics': {
                'merges': dict(self.metrics['merges']),
                'resources': dict(self.metrics['resources']),
                'orders': dict(self.metrics['orders']),
                'energy': dict(self.metrics['energy']),
                'coins': dict(self.metrics['coins']),
                'popups': dict(self.metrics['popups']),
                'events': dict(self.metrics['events']),
                'expansions': dict(self.metrics['expansions']),
                'buildings': dict(self.metrics['buildings'])
            },
            'performance': dict(self.performance)
        }
    
    def save_session_log(self):
        """Save session data to JSON file."""
        log_file = self.log_dir / f"session-{self.session_id}.json"
        
        data = {
            'session_info': {
                'id': self.session_id,
                'start_time': datetime.fromtimestamp(self.session_start).isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': time.time() - self.session_start
            },
            'summary': self.get_metrics_summary(),
            'detailed_metrics': self.get_detailed_metrics(),
            'event_log': self.event_log[:1000]  # Limit to last 1000 events
        }
        
        try:
            with open(log_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            print(f"[Telemetry] Session log saved to {log_file}")
            return True
        
        except Exception as e:
            print(f"[Telemetry] Failed to save session log: {e}")
            return False
    
    def export_csv(self, filename: Optional[str] = None):
        """
        Export metrics to CSV format.
        
        Args:
            filename: Output filename (auto-generated if None)
        """
        if filename is None:
            filename = f"metrics-{self.session_id}.csv"
        
        csv_file = self.log_dir / filename
        
        try:
            import csv
            
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write summary metrics
                writer.writerow(['Metric', 'Value'])
                summary = self.get_metrics_summary()
                
                for key, value in summary.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            writer.writerow([f"{key}_{subkey}", subvalue])
                    else:
                        writer.writerow([key, value])
            
            print(f"[Telemetry] Metrics exported to {csv_file}")
            return True
        
        except Exception as e:
            print(f"[Telemetry] Failed to export CSV: {e}")
            return False


class PerformanceAnalyzer:
    """
    Analyzes telemetry data to provide insights.
    
    Calculates trends, identifies bottlenecks, and
    suggests optimizations.
    """
    
    def __init__(self, telemetry: TelemetryCollector):
        self.telemetry = telemetry
    
    def analyze_efficiency(self) -> Dict:
        """
        Analyze automation efficiency.
        
        Returns:
            Efficiency analysis
        """
        metrics = self.telemetry.get_metrics_summary()
        uptime = self.telemetry.performance['uptime'] / 3600
        
        # Calculate efficiency scores
        merge_efficiency = metrics['merges']['success_rate']
        resource_efficiency = metrics['resources']['per_hour']
        coin_efficiency = metrics['coins']['per_hour']
        
        # Overall efficiency score (0-100)
        overall = (merge_efficiency + 
                  min(resource_efficiency / 10, 100) + 
                  min(coin_efficiency / 100, 100)) / 3
        
        return {
            'overall_score': round(overall, 2),
            'merge_efficiency': merge_efficiency,
            'resource_rate': resource_efficiency,
            'coin_rate': coin_efficiency,
            'uptime_hours': round(uptime, 2),
            'errors_per_hour': round(
                self.telemetry.performance['error_count'] / max(uptime, 0.1),
                2
            )
        }
    
    def identify_bottlenecks(self) -> List[str]:
        """
        Identify performance bottlenecks.
        
        Returns:
            List of bottleneck descriptions
        """
        bottlenecks = []
        metrics = self.telemetry.get_metrics_summary()
        
        # Check merge success rate
        if metrics['merges']['success_rate'] < 80:
            bottlenecks.append(
                f"Low merge success rate ({metrics['merges']['success_rate']}%). "
                "Check template quality and screen area configuration."
            )
        
        # Check energy pauses
        energy_pauses = self.telemetry.metrics['energy']['pauses']
        if energy_pauses > 10:
            bottlenecks.append(
                f"Frequent energy pauses ({energy_pauses}). "
                "Consider adjusting energy thresholds."
            )
        
        # Check error rate
        uptime = self.telemetry.performance['uptime'] / 3600
        error_rate = self.telemetry.performance['error_count'] / max(uptime, 0.1)
        if error_rate > 5:
            bottlenecks.append(
                f"High error rate ({error_rate:.1f} per hour). "
                "Check logs for recurring issues."
            )
        
        # Check coin efficiency
        if metrics['coins']['per_hour'] < 100:
            bottlenecks.append(
                "Low coin generation rate. "
                "Focus on order fulfillment and resource collection."
            )
        
        return bottlenecks
    
    def suggest_optimizations(self) -> List[str]:
        """
        Suggest optimization strategies.
        
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        metrics = self.telemetry.get_metrics_summary()
        
        # Merge optimization
        if metrics['merges']['per_hour'] < 50:
            suggestions.append(
                "Increase merge frequency by reducing delays or adding more templates."
            )
        
        # Resource collection
        if metrics['resources']['per_hour'] < 20:
            suggestions.append(
                "Improve resource collection by reducing scan intervals."
            )
        
        # Order fulfillment
        if metrics['orders']['per_hour'] < 5:
            suggestions.append(
                "Prioritize order fulfillment to maximize coin generation."
            )
        
        # Expansion strategy
        if metrics['coins']['net'] > 10000 and metrics['expansions'] == 0:
            suggestions.append(
                "Consider enabling land expansion to unlock more space."
            )
        
        return suggestions



