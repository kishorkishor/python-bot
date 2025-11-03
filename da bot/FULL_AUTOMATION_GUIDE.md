# Complete Farm Merge Valley Automation Guide

**Version 2.0** - Full-Game Automation System

This guide covers the complete automation system for Farm Merge Valley, from basic merging to advanced autonomous gameplay.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Features](#core-features)
3. [Automation Modules](#automation-modules)
4. [Configuration](#configuration)
5. [Profiles](#profiles)
6. [Template Collection](#template-collection)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)
9. [Performance Optimization](#performance-optimization)

---

## Quick Start

### Prerequisites

- Python 3.7+
- Windows 10/11
- Farm Merge Valley game installed
- Required packages (see `requirements.txt`)

### Installation

```bash
cd farm_merger
pip install -r requirements.txt
```

### First-Time Setup

1. **Launch the GUI**:
   ```bash
   python gui.py
   ```

2. **Configure Basic Settings** (⚡ Quick Start tab):
   - Click "Select Screen Area" to define your game board
   - Click "Select Merge Points" to set merge targets
   - Adjust "Merge Count" (default: 3)
   - Set "Resize Factor" (default: 1.0)

3. **Add Merge Templates**:
   - Place PNG images of items to merge in `img/` folder
   - Or use the template collector tool

4. **Test Basic Merging**:
   - Click "▶ Start Merging"
   - Watch the Activity log
   - Press `=` key to stop

---

## Core Features

### 1. Automatic Merging

**What it does**: Detects and merges identical items on your game board.

**How to use**:
- Add item templates to `img/` folder
- Configure screen area and merge points
- Click "▶ Start Merging"

**Configuration**:
- `merge_count`: Number of items to merge (2-10)
- `resize_factor`: Template scaling (0.5-2.0)
- `drag_duration_seconds`: Merge animation speed

**Features**:
- Priority-based merging (producers first)
- Self-healing (auto-rescans after failures)
- Box/chest integration
- Hotkey stop (`=` key)

### 2. Resource Collection

**What it does**: Automatically collects goods from animals and crops.

**How to use**:
1. Collect producer templates (chicken, cow, wheat, etc.)
2. Place in `img/producers/` folder
3. Enable "Auto-Collect Resources" in settings
4. Configure producer area region

**Configuration**:
- `scan_interval_resources`: Seconds between scans (default: 30)
- `click_delay`: Delay between clicks (default: 0.5)

**Features**:
- Smart priority (collects items needed for orders first)
- Inventory tracking
- Cooldown management
- Statistics tracking

### 3. Order Fulfillment

**What it does**: Detects and completes customer orders automatically.

**How to use**:
1. Collect order board templates
2. Place in `img/orders/` folder
3. Enable "Auto-Fulfill Orders" in settings
4. Configure order board region

**Configuration**:
- `scan_interval_orders`: Seconds between scans (default: 60)
- `order_priority`: "coins", "speed", or "simplicity"

**Features**:
- Coin-optimized fulfillment
- Inventory checking
- Order prioritization
- Earnings tracking

### 4. Energy Management

**What it does**: Monitors energy levels and pauses energy-intensive tasks when low.

**How to use**:
1. Configure energy display region
2. Set energy threshold (default: 20)
3. Enable "Auto-Pause on Low Energy"

**Configuration**:
- `energy_threshold`: Minimum energy before pausing
- `pause_threshold`: Energy level to pause at
- `resume_threshold`: Energy level to resume at

**Features**:
- OCR-based energy reading
- Automatic task pausing
- Regeneration rate tracking
- Task scheduling based on energy

### 5. Popup Handling

**What it does**: Automatically dismisses game popups and dialogs.

**How to use**:
1. Collect popup templates (level-up, daily reward, etc.)
2. Place in `img/ui_elements/` folder
3. Enable "Auto-Dismiss Popups"

**Features**:
- Level-up screen handling
- Daily reward claiming
- Energy warning dismissal
- Tutorial skip
- Ad dismissal

### 6. Land Expansion

**What it does**: Automatically purchases land expansions when coins are available.

**How to use**:
1. Collect expansion button templates
2. Enable "Auto-Expand Land" in settings
3. Set coin threshold (default: 5000)

**Configuration**:
- `coin_threshold_expand`: Minimum coins before expanding
- `max_coins_per_session`: Maximum to spend per session

**Features**:
- Coin balance tracking
- Spending limits
- Obstacle clearing
- Cost-benefit analysis

### 7. Building Repairs

**What it does**: Automatically repairs and upgrades buildings.

**How to use**:
1. Collect repair button templates
2. Enable "Auto-Repair Buildings"
3. System detects repair-ready buildings

**Features**:
- Priority-based repairs (production buildings first)
- Material tracking
- Strategic repair planning

### 8. Event Participation

**What it does**: Automatically joins daily challenges and special events.

**How to use**:
1. Collect event icon templates
2. Enable "Participate in Events"

**Features**:
- Daily challenge completion
- Visitor interaction
- Special offer handling (accept free, skip paid)
- Time-limited event joining

---

## Automation Modules

### Game State Detector (`game_state_detector.py`)

Detects multiple game elements:
- Producer ready indicators
- Order board elements
- UI buttons and icons
- Resource displays (coins, energy)
- Popups and modals

### State Machine (`game_state_machine.py`)

Manages automation states:
- `IDLE`: Waiting for tasks
- `MERGING`: Performing merges
- `COLLECTING`: Collecting resources
- `FULFILLING_ORDERS`: Completing orders
- `HANDLING_POPUP`: Dismissing popups
- `EXPANDING`: Purchasing land
- `REPAIRING`: Fixing buildings

### Resource Collector (`collectors.py`)

- Scans for ready producers
- Clicks to collect goods
- Tracks inventory
- Prioritizes collection based on orders

### Order Manager (`order_manager.py`)

- Detects active orders
- Checks inventory availability
- Fulfills orders by priority
- Tracks coins earned

### Energy Manager (`energy_manager.py`)

- Reads energy level via OCR
- Pauses/resumes tasks based on energy
- Tracks regeneration rate
- Schedules energy-intensive tasks

### Popup Handler (`popup_handler.py`)

- Detects popup types
- Clicks dismiss buttons
- Claims rewards
- Handles warnings

### Expansion Manager (`expansion_manager.py`)

- Scans for expansion plots
- Tracks coin balance
- Purchases expansions
- Clears obstacles

### Building Manager (`building_manager.py`)

- Detects repair-ready buildings
- Tracks material inventory
- Prioritizes repairs
- Executes repairs

### Event Handler (`event_handler.py`)

- Detects daily challenges
- Handles visitor interactions
- Manages special offers
- Joins time-limited events

### Navigator (`navigator.py`)

- Detects current screen
- Navigates between menus
- Pans camera for large farms
- Auto-returns to farm view

### Telemetry (`telemetry.py`)

- Tracks automation performance
- Logs session data
- Calculates efficiency metrics
- Identifies bottlenecks

### Task Scheduler (`scheduler.py`)

- Manages scheduled tasks
- Handles cooldowns
- Supports daily routines
- Energy-aware scheduling

---

## Configuration

### Config File: `farm_merger_config.json`

The config file stores all automation settings. See `farm_merger_config_example.json` for a complete example.

### Key Settings

#### Screen Regions
```json
{
  "screen_area": [100, 100, 800, 600],
  "regions": {
    "order_board": [50, 50, 300, 400],
    "energy_display": [10, 10, 100, 30],
    "coin_display": [10, 50, 100, 30]
  }
}
```

#### Automation Toggles
```json
{
  "automation": {
    "collect_resources": true,
    "fulfill_orders": true,
    "auto_merge": true,
    "handle_popups": true,
    "expand_land": false,
    "repair_buildings": true,
    "participate_in_events": true
  }
}
```

#### Timing
```json
{
  "timing": {
    "scan_interval_resources": 30,
    "scan_interval_orders": 60,
    "merge_delay": 0.05,
    "click_delay": 0.5
  }
}
```

#### Safety
```json
{
  "safety": {
    "max_actions_per_minute": 60,
    "randomize_delays": true,
    "humanlike_mouse": true
  }
}
```

---

## Profiles

Automation profiles define different strategies and behaviors.

### Built-in Profiles

#### Aggressive
- **Goal**: Maximum coins/hour
- **Features**: All automation enabled, fast actions, frequent scans
- **Energy**: Low threshold (10), aggressive expansion
- **Best for**: Active play sessions, maximizing progress

#### Balanced (Default)
- **Goal**: Mix of growth and resource building
- **Features**: Core automation enabled, moderate pace
- **Energy**: Medium threshold (20), manual expansion
- **Best for**: General use, sustainable automation

#### Passive
- **Goal**: Minimal activity, focus on collection
- **Features**: Basic automation only, slow pace
- **Energy**: High threshold (30), conservative spending
- **Best for**: Background play, low-impact automation

#### Merge Only
- **Goal**: Focus exclusively on merging
- **Features**: Only merging enabled, all other features disabled
- **Best for**: Template testing, merge-focused gameplay

### Using Profiles

**Via GUI**:
1. Navigate to ⚙️ Settings tab
2. Select profile from dropdown
3. Click "Apply Profile"

**Via Code**:
```python
from profiles import ProfileManager, ProfileApplicator

manager = ProfileManager()
manager.set_active_profile('aggressive')
```

### Creating Custom Profiles

1. Copy `farm_merger_profiles.json`
2. Add new profile entry
3. Customize settings
4. Save and reload

---

## Template Collection

Templates are PNG images used for detecting game elements.

### Collection Methods

#### Method 1: Built-in Collector (Recommended)

1. Click "📸 Collect Templates" in Settings
2. Left-click on game elements
3. Enter descriptive names
4. Right-click or ESC to exit

#### Method 2: Manual Screenshots

1. Take screenshot of game
2. Crop to element
3. Save as PNG
4. Place in appropriate folder

### Template Organization

```
img/
├── ui_elements/      # Buttons, icons, popups
├── producers/        # Animals, crops with ready indicators
├── orders/           # Order board items
└── [merge items]     # Your existing merge templates
```

### Template Quality

- **Size**: Minimum 20x20 pixels
- **Content**: Element only, no background
- **Consistency**: Same resolution and graphics settings
- **Testing**: Use Detection tab to verify

See `img/TEMPLATE_GUIDE.md` for detailed instructions.

---

## Advanced Features

### Watchdog and Crash Recovery

**Coming Soon**: Automatic restart on crashes, state recovery, screenshot logging.

### Health Dashboard

**Coming Soon**: Real-time automation stats, performance graphs, resource tracking.

### Rate Limiting

**Coming Soon**: Action throttling, humanlike delays, detection avoidance.

### Daily Routines

Schedule tasks at specific times:

```python
from scheduler import DailyRoutineScheduler

scheduler = DailyRoutineScheduler()
scheduler.add_daily_routine(
    name="morning_collection",
    hour=8,
    minute=0,
    callback=collect_all_resources
)
```

### Telemetry Analysis

Track and analyze performance:

```python
from telemetry import TelemetryCollector, PerformanceAnalyzer

telemetry = TelemetryCollector()
analyzer = PerformanceAnalyzer(telemetry)

# Get efficiency metrics
efficiency = analyzer.analyze_efficiency()
print(f"Overall efficiency: {efficiency['overall_score']}%")

# Identify bottlenecks
bottlenecks = analyzer.identify_bottlenecks()
for issue in bottlenecks:
    print(f"⚠ {issue}")

# Get optimization suggestions
suggestions = analyzer.suggest_optimizations()
for tip in suggestions:
    print(f"💡 {tip}")
```

---

## Troubleshooting

### Common Issues

#### Templates Not Detected

**Symptoms**: "No matches found" in log

**Solutions**:
1. Lower threshold slider (try 0.70 or 0.65)
2. Recapture template at exact game resolution
3. Ensure game graphics settings haven't changed
4. Try different resize factors (0.9, 1.1)

#### False Positives

**Symptoms**: Detecting wrong items

**Solutions**:
1. Raise threshold slider (try 0.80 or 0.85)
2. Capture more unique portion of element
3. Add more distinctive features to template

#### Energy Reading Fails

**Symptoms**: Energy shows as None

**Solutions**:
1. Install Tesseract OCR
2. Reconfigure energy display region
3. Ensure region captures only the number
4. Try different OCR preprocessing

#### Orders Not Fulfilling

**Symptoms**: Orders detected but not completed

**Solutions**:
1. Check inventory tracking
2. Verify order button templates
3. Ensure order board region is correct
4. Check click delay settings

#### High CPU Usage

**Solutions**:
1. Increase scan intervals
2. Reduce max actions per minute
3. Disable unused automation features
4. Use passive profile

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Log Files

Session logs are saved to `logs/` directory:
- `session-YYYYMMDD-HHMM.json`: Complete session data
- `metrics-YYYYMMDD-HHMM.csv`: Exportable metrics

---

## Performance Optimization

### Maximize Coins/Hour

1. Use **Aggressive** profile
2. Enable all automation features
3. Prioritize order fulfillment
4. Reduce scan intervals
5. Collect high-value order templates

### Minimize Resource Usage

1. Use **Passive** profile
2. Increase scan intervals
3. Disable expansion and events
4. Reduce max actions per minute

### Balance Speed and Safety

1. Use **Balanced** profile
2. Enable randomized delays
3. Set reasonable action limits
4. Monitor telemetry for issues

### Template Optimization

1. Keep templates small but distinctive
2. Remove unused templates
3. Use appropriate thresholds
4. Test regularly after game updates

### Energy Efficiency

1. Set appropriate energy thresholds
2. Prioritize low-energy tasks
3. Schedule energy-intensive tasks
4. Track regeneration rate

---

## Best Practices

### Daily Routine

**Morning** (8:00 AM):
- Collect daily rewards
- Complete daily challenge
- Collect from all producers
- Fulfill pending orders

**Afternoon** (2:00 PM):
- Run merge cycles
- Check for events
- Repair buildings if needed

**Evening** (8:00 PM):
- Final resource collection
- Order fulfillment
- Save session data

### Safety Guidelines

1. **Start Slow**: Begin with passive profile
2. **Monitor First Hour**: Watch for issues
3. **Adjust Gradually**: Tweak settings incrementally
4. **Regular Checks**: Review logs weekly
5. **Backup Config**: Save working configurations

### Maintenance

- **Weekly**: Check template quality
- **Monthly**: Review and update templates
- **After Updates**: Verify all features work
- **Regular**: Clean up old log files

---

## Support and Community

### Getting Help

1. Check this guide and troubleshooting section
2. Review `FIXES.md` for known issues
3. Check `CHANGELOG.md` for recent changes
4. Examine session logs for errors

### Contributing

- Share your template collections
- Report bugs and issues
- Suggest new features
- Contribute code improvements

---

## Appendix

### Module Reference

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `game_state_detector.py` | Element detection | `detect_producers_ready()`, `detect_active_orders()` |
| `game_state_machine.py` | State management | `transition_to()`, `decide_next_action()` |
| `collectors.py` | Resource collection | `collect_from_producers()` |
| `order_manager.py` | Order fulfillment | `fulfill_orders()` |
| `energy_manager.py` | Energy monitoring | `read_energy_level()`, `should_pause_tasks()` |
| `popup_handler.py` | Popup dismissal | `check_and_handle_popups()` |
| `expansion_manager.py` | Land expansion | `purchase_expansion()` |
| `building_manager.py` | Building repairs | `repair_building()` |
| `event_handler.py` | Event participation | `handle_daily_challenge()` |
| `navigator.py` | Menu navigation | `navigate_to()`, `pan_camera()` |
| `telemetry.py` | Performance tracking | `record_merge()`, `get_metrics_summary()` |
| `scheduler.py` | Task scheduling | `add_task()`, `add_daily_routine()` |
| `profiles.py` | Profile management | `set_active_profile()` |

### Hotkeys

- `=`: Stop automation
- (More hotkeys coming in future updates)

### File Structure

```
farm_merger/
├── gui.py                          # Main GUI
├── main.py                         # CLI entry point
├── item_finder.py                  # Image detection core
├── game_state_detector.py          # Multi-element detection
├── game_state_machine.py           # State management
├── collectors.py                   # Resource collection
├── order_manager.py                # Order fulfillment
├── energy_manager.py               # Energy monitoring
├── popup_handler.py                # Popup handling
├── expansion_manager.py            # Land expansion
├── building_manager.py             # Building repairs
├── event_handler.py                # Event participation
├── navigator.py                    # Navigation
├── telemetry.py                    # Performance tracking
├── scheduler.py                    # Task scheduling
├── profiles.py                     # Profile management
├── screen_area_selector.py         # Screen region tool
├── merging_points_selector.py      # Merge point tool
├── template_collector.py           # Template capture tool
├── farm_merger_config.json         # Configuration
├── farm_merger_profiles.json       # Profiles
├── img/                            # Templates
│   ├── ui_elements/
│   ├── producers/
│   ├── orders/
│   └── TEMPLATE_GUIDE.md
└── logs/                           # Session logs
```

---

**Version**: 2.0  
**Last Updated**: November 2025  
**Author**: Kishor  
**License**: See repository for details



