"""Task Scheduler for Farm Merge Valley Automation.

Manages time-based automation control, daily routines,
cooldown management, and energy-efficient scheduling.
"""

import time
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum, auto


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class ScheduledTask:
    """Represents a scheduled automation task."""
    name: str
    callback: Callable
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # Scheduling
    scheduled_time: Optional[float] = None  # Unix timestamp
    interval: Optional[int] = None  # Seconds between executions
    last_run: float = 0.0
    next_run: float = 0.0
    
    # Execution control
    cooldown: int = 0  # Minimum seconds between runs
    max_retries: int = 3
    retry_count: int = 0
    timeout: Optional[int] = None  # Max execution time
    
    # State
    status: TaskStatus = TaskStatus.PENDING
    enabled: bool = True
    
    # Callbacks
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    
    def can_run(self) -> bool:
        """Check if task is ready to run."""
        if not self.enabled:
            return False
        
        if self.status == TaskStatus.RUNNING:
            return False
        
        current_time = time.time()
        
        # Check cooldown
        if self.cooldown > 0:
            if current_time - self.last_run < self.cooldown:
                return False
        
        # Check scheduled time
        if self.scheduled_time:
            if current_time < self.scheduled_time:
                return False
        
        # Check next run time (for intervals)
        if self.next_run > 0:
            if current_time < self.next_run:
                return False
        
        return True
    
    def execute(self) -> bool:
        """Execute the task."""
        if not self.can_run():
            return False
        
        self.status = TaskStatus.RUNNING
        
        try:
            self.callback(*self.args, **self.kwargs)
            self.status = TaskStatus.COMPLETED
            self.last_run = time.time()
            self.retry_count = 0
            
            # Schedule next run if interval is set
            if self.interval:
                self.next_run = time.time() + self.interval
            
            return True
        
        except Exception as e:
            print(f"[Scheduler] Task '{self.name}' failed: {e}")
            self.status = TaskStatus.FAILED
            self.retry_count += 1
            
            # Retry logic
            if self.retry_count < self.max_retries:
                self.status = TaskStatus.PENDING
                self.next_run = time.time() + (self.cooldown or 10)
            
            return False


class TaskScheduler:
    """
    Manages scheduled automation tasks.
    
    Handles time-based task execution, cooldown management,
    and daily routine scheduling.
    """
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.last_tick = time.time()
        
        # Statistics
        self.tasks_executed = 0
        self.tasks_failed = 0
        self.execution_history = []  # (timestamp, task_name, success)
    
    def add_task(
        self,
        name: str,
        callback: Callable,
        priority: TaskPriority = TaskPriority.MEDIUM,
        interval: Optional[int] = None,
        cooldown: int = 0,
        scheduled_time: Optional[float] = None,
        args: tuple = (),
        kwargs: dict = None
    ) -> bool:
        """
        Add a task to the scheduler.
        
        Args:
            name: Unique task name
            callback: Function to execute
            priority: Task priority
            interval: Seconds between executions (None = run once)
            cooldown: Minimum seconds between runs
            scheduled_time: Specific time to run (Unix timestamp)
            args: Positional arguments for callback
            kwargs: Keyword arguments for callback
            
        Returns:
            True if task was added
        """
        if name in self.tasks:
            print(f"[Scheduler] Task already exists: {name}")
            return False
        
        task = ScheduledTask(
            name=name,
            callback=callback,
            priority=priority,
            interval=interval,
            cooldown=cooldown,
            scheduled_time=scheduled_time,
            args=args,
            kwargs=kwargs or {}
        )
        
        # Set initial next_run
        if interval:
            task.next_run = time.time() + interval
        elif scheduled_time:
            task.next_run = scheduled_time
        
        self.tasks[name] = task
        print(f"[Scheduler] Added task: {name}")
        return True
    
    def remove_task(self, name: str) -> bool:
        """
        Remove a task from the scheduler.
        
        Args:
            name: Task name
            
        Returns:
            True if task was removed
        """
        if name in self.tasks:
            del self.tasks[name]
            print(f"[Scheduler] Removed task: {name}")
            return True
        return False
    
    def enable_task(self, name: str) -> bool:
        """Enable a task."""
        if name in self.tasks:
            self.tasks[name].enabled = True
            return True
        return False
    
    def disable_task(self, name: str) -> bool:
        """Disable a task."""
        if name in self.tasks:
            self.tasks[name].enabled = False
            return True
        return False
    
    def get_task(self, name: str) -> Optional[ScheduledTask]:
        """Get a task by name."""
        return self.tasks.get(name)
    
    def list_tasks(self) -> List[str]:
        """Get list of all task names."""
        return list(self.tasks.keys())
    
    def tick(self):
        """
        Execute one scheduler tick.
        
        Checks all tasks and executes those that are ready.
        """
        current_time = time.time()
        self.last_tick = current_time
        
        # Get tasks that can run, sorted by priority
        ready_tasks = [
            task for task in self.tasks.values()
            if task.can_run()
        ]
        
        ready_tasks.sort(key=lambda t: t.priority.value)
        
        # Execute ready tasks
        for task in ready_tasks:
            success = task.execute()
            
            if success:
                self.tasks_executed += 1
            else:
                self.tasks_failed += 1
            
            self.execution_history.append({
                'timestamp': current_time,
                'task': task.name,
                'success': success
            })
    
    def run_once(self):
        """Run one scheduler cycle."""
        self.tick()
    
    def get_next_task_time(self) -> Optional[float]:
        """
        Get time until next task execution.
        
        Returns:
            Seconds until next task, or None if no tasks
        """
        if not self.tasks:
            return None
        
        current_time = time.time()
        next_times = []
        
        for task in self.tasks.values():
            if not task.enabled:
                continue
            
            if task.next_run > 0:
                next_times.append(task.next_run - current_time)
        
        if next_times:
            return max(0, min(next_times))
        
        return None
    
    def get_statistics(self) -> Dict:
        """
        Get scheduler statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            'total_tasks': len(self.tasks),
            'enabled_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'tasks_executed': self.tasks_executed,
            'tasks_failed': self.tasks_failed,
            'success_rate': self._calculate_success_rate(),
            'next_task_in': self.get_next_task_time()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate task success rate."""
        total = self.tasks_executed + self.tasks_failed
        if total == 0:
            return 100.0
        return round((self.tasks_executed / total) * 100, 2)
    
    def get_task_status(self, name: str) -> Optional[Dict]:
        """
        Get status of a specific task.
        
        Args:
            name: Task name
            
        Returns:
            Task status dictionary or None
        """
        task = self.tasks.get(name)
        if not task:
            return None
        
        current_time = time.time()
        
        return {
            'name': task.name,
            'status': task.status.name,
            'enabled': task.enabled,
            'priority': task.priority.name,
            'last_run': task.last_run,
            'next_run': task.next_run,
            'time_until_next': max(0, task.next_run - current_time) if task.next_run > 0 else None,
            'retry_count': task.retry_count
        }


class DailyRoutineScheduler(TaskScheduler):
    """
    Extended scheduler with daily routine support.
    
    Allows defining time-of-day based automation schedules.
    """
    
    def __init__(self):
        super().__init__()
        self.routines: Dict[str, Dict] = {}
    
    def add_daily_routine(
        self,
        name: str,
        hour: int,
        minute: int,
        callback: Callable,
        args: tuple = (),
        kwargs: dict = None
    ) -> bool:
        """
        Add a daily routine that runs at a specific time each day.
        
        Args:
            name: Routine name
            hour: Hour (0-23)
            minute: Minute (0-59)
            callback: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            True if routine was added
        """
        if name in self.routines:
            print(f"[Scheduler] Routine already exists: {name}")
            return False
        
        # Calculate next execution time
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed today, schedule for tomorrow
        if target_time <= now:
            target_time += timedelta(days=1)
        
        scheduled_timestamp = target_time.timestamp()
        
        # Add as recurring task with 24-hour interval
        success = self.add_task(
            name=f"routine_{name}",
            callback=callback,
            priority=TaskPriority.HIGH,
            interval=86400,  # 24 hours
            scheduled_time=scheduled_timestamp,
            args=args,
            kwargs=kwargs or {}
        )
        
        if success:
            self.routines[name] = {
                'hour': hour,
                'minute': minute,
                'next_run': target_time
            }
            print(f"[Scheduler] Added daily routine: {name} at {hour:02d}:{minute:02d}")
        
        return success
    
    def remove_daily_routine(self, name: str) -> bool:
        """Remove a daily routine."""
        if name in self.routines:
            del self.routines[name]
            return self.remove_task(f"routine_{name}")
        return False
    
    def list_routines(self) -> List[Dict]:
        """
        Get list of all daily routines.
        
        Returns:
            List of routine info dictionaries
        """
        routines = []
        for name, info in self.routines.items():
            task_status = self.get_task_status(f"routine_{name}")
            routines.append({
                'name': name,
                'time': f"{info['hour']:02d}:{info['minute']:02d}",
                'next_run': info['next_run'].isoformat(),
                'status': task_status['status'] if task_status else 'UNKNOWN'
            })
        return routines


class EnergyAwareScheduler(DailyRoutineScheduler):
    """
    Scheduler with energy-aware task management.
    
    Prioritizes tasks based on energy availability and
    defers energy-intensive tasks when energy is low.
    """
    
    def __init__(self, energy_manager):
        super().__init__()
        self.energy_manager = energy_manager
        
        # Task energy costs
        self.task_energy_costs = {}
    
    def set_task_energy_cost(self, task_name: str, cost: int):
        """
        Set energy cost for a task.
        
        Args:
            task_name: Task name
            cost: Energy cost
        """
        self.task_energy_costs[task_name] = cost
    
    def tick(self):
        """Execute tick with energy awareness."""
        current_time = time.time()
        self.last_tick = current_time
        
        # Get current energy level
        current_energy = self.energy_manager.current_energy
        
        # Get tasks that can run
        ready_tasks = [
            task for task in self.tasks.values()
            if task.can_run()
        ]
        
        # Filter by energy availability
        if current_energy is not None:
            affordable_tasks = []
            for task in ready_tasks:
                cost = self.task_energy_costs.get(task.name, 0)
                if cost == 0 or current_energy >= cost:
                    affordable_tasks.append(task)
            ready_tasks = affordable_tasks
        
        # Sort by priority
        ready_tasks.sort(key=lambda t: t.priority.value)
        
        # Execute ready tasks
        for task in ready_tasks:
            success = task.execute()
            
            if success:
                self.tasks_executed += 1
                
                # Deduct energy cost
                cost = self.task_energy_costs.get(task.name, 0)
                if cost > 0 and current_energy is not None:
                    current_energy -= cost
            else:
                self.tasks_failed += 1
            
            self.execution_history.append({
                'timestamp': current_time,
                'task': task.name,
                'success': success
            })
    
    def get_affordable_tasks(self) -> List[str]:
        """
        Get list of tasks that can be executed with current energy.
        
        Returns:
            List of task names
        """
        current_energy = self.energy_manager.current_energy
        
        if current_energy is None:
            return self.list_tasks()
        
        affordable = []
        for name, task in self.tasks.items():
            cost = self.task_energy_costs.get(name, 0)
            if cost == 0 or current_energy >= cost:
                affordable.append(name)
        
        return affordable



