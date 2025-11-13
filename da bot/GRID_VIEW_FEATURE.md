# 2D Grid View Feature

## Overview
A new **Grid View** tab has been added to the Flet GUI that provides a visual 2D representation of detected game objects in a top-down grid layout.

## Location
- **File**: `da bot/gui_flet.py`
- **Tab**: "Grid View" (5th tab in the navigation)
- **Lines**: ~3344-3887

## Features

### 1. Visual Grid Representation
- **Dynamic Grid Sizing**: Configurable rows and columns (1-20 each)
- **Color-Coded Cells**:
  - 🟢 **Green**: Single item detected
  - 🟠 **Orange**: Multiple items in same cell
  - ⚪ **Gray**: Empty cell
- **Item Images**: Displays actual template images when available
- **Item Count Badges**: Shows "×N" badge when multiple items occupy one cell

### 2. Smart Object Mapping
- Automatically maps detected objects from screen coordinates to grid cells
- Uses game area boundaries (start_x, start_y, end_x, end_y)
- Calculates cell positions based on relative coordinates
- Handles overlapping items gracefully

### 3. Interactive Features
- **Tooltips**: Hover over cells to see:
  - Cell coordinates (row, col)
  - Item name(s)
  - Additional items if multiple detected
- **Stats Display**: Shows real-time statistics:
  - Grid dimensions (rows × cols)
  - Filled cells count
  - Empty cells count
  - Total items detected
- **Legend**: Visual guide explaining color meanings

### 4. Control Panel
- **Grid Size Inputs**: Text fields for rows and columns
- **Update Grid**: Refresh visualization with current detection data
- **Scan & Update**: Run fresh detection scan and update grid automatically
- **Go to Detection Tab**: Quick navigation when no data available

## How It Works

### Data Flow
```
1. User runs detection scan (Detection Tab)
   ↓
2. Detection results stored in `last_detection_results`
   ↓
3. User switches to Grid View tab
   ↓
4. Clicks "Update Grid" or "Scan & Update"
   ↓
5. create_game_grid_view() processes detection data
   ↓
6. Maps each detected object to grid cell based on coordinates
   ↓
7. Renders visual grid with colored cells and images
```

### Key Functions

#### `create_game_grid_view(detection_results, game_area, grid_size)`
Main rendering function that:
- Validates game area is set
- Creates grid map dictionary
- Maps detected objects to cells
- Builds visual row/column layout
- Returns formatted grid widget

**Parameters**:
- `detection_results`: Dict with format:
  ```python
  {
    "template_name.png": {
      "count": 3,
      "points": [(x1, y1), (x2, y2)],
      "template_path": "path/to/template.png"
    }
  }
  ```
- `game_area`: Tuple (start_x, start_y, end_x, end_y)
- `grid_size`: Tuple (rows, cols)

#### `update_grid_view()`
Updates the grid visualization:
- Checks for detection data
- Validates grid size inputs
- Calls `create_game_grid_view()`
- Updates UI with result

#### `scan_and_update_grid(e)`
Convenience function:
- Triggers detection scan
- Waits 0.5s for completion
- Automatically updates grid view

## Usage Instructions

### For Users
1. **Set Game Area**: Go to "Quick Start" → Select your game area
2. **Run Detection**: Go to "Detection" tab → Click "Show Preview"
3. **View Grid**: Navigate to "Grid View" tab
4. **Configure**: Adjust rows/columns if needed (default: 9×9)
5. **Update**: Click "Update Grid" to see visualization
   - Or "Scan & Update" to re-scan and update in one click

### For Developers
```python
# Access grid view state
grid_view_ref.current  # Container reference
grid_size_rows_ref.current.value  # Current rows
grid_size_cols_ref.current.value  # Current cols

# Programmatic update
update_grid_view()

# Integration with detection system
last_detection_results  # Global variable with latest scan results
```

## Technical Details

### Coordinate Mapping Algorithm
```python
# Convert screen coordinates to grid cell
rel_x = detected_x - game_area_start_x
rel_y = detected_y - game_area_start_y

cell_width = (game_area_end_x - game_area_start_x) / cols
cell_height = (game_area_end_y - game_area_start_y) / rows

col = min(cols - 1, max(0, int(rel_x / cell_width)))
row = min(rows - 1, max(0, int(rel_y / cell_height)))
```

### Grid Cell Structure
```python
grid_map[(row, col)] = [
  {
    "name": "wheat1",
    "pos": (1234, 567),
    "template": "wheat1.png",
    "template_path": "./img/wheat1.png"
  },
  # ... additional items if multiple detected
]
```

## Integration Points

### Global Variables Used
- `last_detection_results`: Latest detection scan results
- `area`: Game area boundaries tuple
- `board_rows`: Default row count
- `board_cols`: Default column count

### Functions Called
- `create_glass_card()`: UI styling
- `create_glass_button()`: Button widgets
- `scan_and_preview_callback()`: Trigger detection
- `update_log()`: Log messages
- `switch_tab()`: Navigation

### Tab System Integration
- Added to `tab_names` list at index 4 (5th position)
- Added to `tab_containers` list
- Uses standard tab visibility system

## UI Design

### Glassmorphism Theme
- Consistent with rest of Flet GUI
- Semi-transparent backgrounds
- Soft borders and shadows
- Smooth animations
- Modern color palette

### Responsive Layout
- Scrollable grid container
- Wrapping control buttons
- Adaptive spacing
- Mobile-friendly sizing

## Performance Considerations

- Grid limited to 20×20 (400 cells max) for performance
- Lazy image loading (only when template exists)
- Efficient dictionary-based lookups
- No real-time updates (manual refresh only)

## Future Enhancements

### Potential Features
- [ ] Click cell to highlight/select item
- [ ] Click cell to trigger merge action
- [ ] Real-time auto-refresh option
- [ ] Export grid layout to JSON
- [ ] Import/load saved grid layouts
- [ ] Zoom in/out functionality
- [ ] Cell filtering by item type
- [ ] Heat map view (density visualization)
- [ ] Animation for item movements

### Technical Improvements
- [ ] Canvas-based rendering for larger grids
- [ ] Virtual scrolling for massive grids
- [ ] WebGL acceleration
- [ ] Caching of grid calculations

## Testing

### Manual Test Cases
1. ✅ No detection data → Shows info message
2. ✅ Invalid grid size → Shows error message
3. ✅ Valid detection data → Renders grid
4. ✅ Single item per cell → Green cells
5. ✅ Multiple items per cell → Orange cells with count
6. ✅ Empty cells → Gray with coordinates
7. ✅ Tooltip display → Shows item info on hover
8. ✅ Stats display → Correct counts
9. ✅ Scan & Update → Triggers scan and refreshes
10. ✅ Tab navigation → Switches correctly

### Known Limitations
- Maximum grid size: 20×20
- No real-time updates (manual refresh required)
- Performance may degrade with very dense grids (>100 items)
- Template images must exist for image display

## Changelog

### Version 1.0 (November 13, 2025)
- ✅ Initial implementation
- ✅ Grid visualization with color coding
- ✅ Item image display
- ✅ Multi-item cell handling
- ✅ Stats panel
- ✅ Control panel with scan integration
- ✅ Tooltips and legend
- ✅ Tab integration
- ✅ Glassmorphism styling
- ✅ No linting errors

## Credits
- **Implementation**: AI Assistant (Claude Sonnet 4.5)
- **Request**: User (Kishor)
- **Framework**: Flet (Python UI framework)
- **Project**: Farm Merger Pro Automation Bot

