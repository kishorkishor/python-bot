# Grid View - Visual Example

## What You'll See

### Grid View Tab Layout
```
┌─────────────────────────────────────────────────────────────────┐
│                     2D Game Grid  🎮                             │
│        Visual representation of detected objects                 │
├─────────────────────────────────────────────────────────────────┤
│  Grid Configuration                                              │
│  ┌──────────┐   ┌──────────┐   ┌────────────┐  ┌─────────────┐│
│  │ Rows: 9  │ × │ Cols: 9  │   │Update Grid │  │Scan & Update││
│  └──────────┘   └──────────┘   └────────────┘  └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  Grid: 9×9 • Filled: 23 • Empty: 58 • Total Items: 27          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐      │
│  │ 0,0 │ 0,1 │🌾  │ 0,3 │🐔  │ 0,5 │ 0,6 │ 0,7 │ 0,8 │      │
│  │     │     │ 1  │     │ 1  │     │     │     │     │      │
│  ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤      │
│  │ 1,0 │🌽  │🌽  │🌽  │ 1,4 │ 1,5 │🐄  │ 1,7 │ 1,8 │      │
│  │     │ 2  │ 1  │ 1  │     │     │ 1  │     │     │      │
│  ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤      │
│  │ 2,0 │ 2,1 │🌾  │🌾  │🌾  │ 2,5 │ 2,6 │🐷  │ 2,8 │      │
│  │     │     │×3  │ 2  │ 1  │     │     │ 1  │     │      │
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘      │
│                        ... (more rows)                           │
├─────────────────────────────────────────────────────────────────┤
│  Legend:                                                         │
│  ┌──────┐ = Single item  ┌──────┐ = Multiple  ┌──────┐ = Empty│
│  │Green │                │Orange│             │ Gray │         │
│  └──────┘                └──────┘             └──────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Cell Types Explained

### 1. Empty Cell (Gray)
```
┌─────┐
│ 2,5 │  ← Shows row,col coordinates
│     │  ← No items detected
└─────┘
Color: Gray background, light border
```

### 2. Single Item Cell (Green)
```
┌─────┐
│ 🌾  │  ← Item image or name
│  1  │  ← Optional: count = 1
└─────┘
Color: Green background, green border
Tooltip: "Cell (2,3): wheat1"
```

### 3. Multiple Items Cell (Orange)
```
┌─────┐
│ 🌽  │  ← First item image
│ ×3  │  ← Count badge (3 items)
└─────┘
Color: Orange background, orange border
Tooltip: "Cell (1,2): corn1
         + corn2, corn3"
```

## Real Example with Detection Data

### Input (Detection Results)
```python
detection_results = {
  "wheat1.png": {
    "count": 5,
    "points": [(120, 80), (180, 80), (240, 160), (300, 160), (360, 160)],
    "template_path": "./img/wheat1.png"
  },
  "corn1.png": {
    "count": 3,
    "points": [(180, 140), (240, 140), (300, 140)],
    "template_path": "./img/corn1.png"
  },
  "chicken1.png": {
    "count": 2,
    "points": [(420, 80), (600, 140)],
    "template_path": "./img/chicken1.png"
  }
}

game_area = (100, 60, 820, 780)  # (start_x, start_y, end_x, end_y)
grid_size = (9, 9)  # 9 rows × 9 columns
```

### Output (Visual Grid)
```
Cell Calculations:
- Game width: 820 - 100 = 720 pixels
- Game height: 780 - 60 = 720 pixels
- Cell width: 720 / 9 = 80 pixels
- Cell height: 720 / 9 = 80 pixels

Mapping:
- wheat1 at (120, 80) → relative (20, 20) → cell [0,0]
- wheat1 at (180, 80) → relative (80, 20) → cell [0,1]
- wheat1 at (240, 160) → relative (140, 100) → cell [1,1]
- corn1 at (180, 140) → relative (80, 80) → cell [1,1] ← Same cell!
- corn1 at (240, 140) → relative (140, 80) → cell [1,1] ← Same cell!
- chicken1 at (420, 80) → relative (320, 20) → cell [0,4]
... etc

Result Grid [0-2, 0-4]:
┌────────┬────────┬────────┬────────┬────────┐
│ 🌾     │ 🌾     │  0,2   │  0,3   │ 🐔     │
│  1     │  1     │        │        │  1     │
├────────┼────────┼────────┼────────┼────────┤
│  1,0   │ 🌾     │  1,2   │  1,3   │  1,4   │
│        │ ×3     │        │        │        │
├────────┼────────┼────────┼────────┼────────┤
│  2,0   │  2,1   │  2,2   │  2,3   │  2,4   │
│        │        │        │        │        │
└────────┴────────┴────────┴────────┴────────┘

Stats:
- Grid: 9×9
- Filled: 4 cells
- Empty: 77 cells
- Total Items: 10
```

## Interactive Features

### Hover Tooltip Example
```
Mouse over cell [1,1]:

┌─────────────────────────────┐
│ Tooltip:                    │
│ Cell (1,1): wheat1          │
│ + corn1, corn1              │
└─────────────────────────────┘
```

### Click Actions (Future)
```
Click on cell [1,1]:
→ Could highlight all items in that cell
→ Could show detailed item info panel
→ Could trigger merge action
→ Could navigate to that screen location
```

## Color Scheme

### Current Theme (Glassmorphism)
```css
/* Empty Cell */
background: rgba(255, 255, 255, 0.05)
border: rgba(255, 255, 255, 0.1)
text: rgba(255, 255, 255, 0.3)

/* Single Item Cell (Green) */
background: rgba(0, 255, 0, 0.3)
border: #4CD964
text: #FFFFFF

/* Multiple Items Cell (Orange) */
background: rgba(255, 165, 0, 0.4)
border: #FFB800
badge: #FFFF00

/* Stats */
Grid: #FFFFFF
Filled: #4CD964
Empty: #B4BED2
Total: #58B2FF
```

## Practical Use Cases

### 1. Game State Overview
```
"I can see at a glance that my farm has:
- 15 wheat plants (green cells in rows 0-2)
- 8 corn plants (green cells in rows 3-4)
- 5 chickens (scattered green cells)
- 3 cells with multiple items (orange = need attention!)"
```

### 2. Merge Planning
```
"Looking at the grid, I can plan my merge strategy:
- Row 1, Col 1 has ×3 wheat → perfect for merge!
- Row 2, Col 3 has ×2 corn → need one more
- Empty cells in row 5 → good space for new items"
```

### 3. Detection Validation
```
"Grid view helps verify detection accuracy:
✅ All expected items are showing
✅ No false positives in empty areas
❌ Cell [4,2] shows item but should be empty
   → Need to adjust detection threshold"
```

### 4. Automation Monitoring
```
"During automation, I can:
- Watch items being merged (cells changing from orange to green)
- See new items appearing (gray cells turning green)
- Monitor farm density (filled vs empty ratio)
- Track automation progress visually"
```

## Navigation Flow

### Typical User Journey
```
1. Start Application
   ↓
2. Quick Start → Select Area → Select Points
   ↓
3. Detection Tab → Click "Show Preview"
   ↓
4. Wait for scan... (detecting items)
   ↓
5. Grid View Tab → Click "Update Grid"
   ↓
6. View 2D Grid → Analyze game state
   ↓
7. Adjust grid size if needed (e.g., 10×10)
   ↓
8. Click "Update Grid" again → See new layout
   ↓
9. Click "Scan & Update" → Fresh scan + grid update
```

## Tips & Tricks

### 1. Finding Optimal Grid Size
```
Too Small (5×5):
- Large cells = many items per cell (lots of orange)
- Less precise positioning
- ✗ Not recommended

Just Right (9×9):
- Balanced cell size
- Most items in separate cells (mostly green)
- ✓ Default and recommended

Too Large (20×20):
- Small cells = items spread across multiple cells
- Harder to visualize
- ⚠ Use only for very dense farms
```

### 2. Quick Scanning Workflow
```
Fast method:
Grid View → "Scan & Update" button
(One click = scan + update)

Manual method:
Detection → "Show Preview" → Wait → Grid View → "Update Grid"
(Use when you want to see detection details first)
```

### 3. Troubleshooting Empty Grid
```
Problem: Grid shows all gray cells (empty)

Solutions:
1. Check "No detection data available" message
   → Go to Detection tab first
   
2. Verify game area is set correctly
   → Quick Start → Select Area
   
3. Ensure templates exist in ./img/ folder
   → Check Detection tab for template count
   
4. Run "Scan & Update" to force fresh scan
```

## Summary

The Grid View feature provides a **powerful visual overview** of your game state by:
- ✅ Mapping detected objects to grid cells
- ✅ Color-coding for quick status recognition  
- ✅ Showing item images and counts
- ✅ Providing stats and tooltips
- ✅ Integrating seamlessly with detection system

**Result**: You can see your entire farm layout at a glance and make informed decisions about merging, automation, and strategy! 🎮🌾🐔






