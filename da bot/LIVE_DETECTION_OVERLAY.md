# Live Detection Overlay

## Overview

The Live Detection Overlay feature displays real-time detection boxes directly on your screen around detected items. Green boxes with labels appear over your game window, showing exactly what the bot is detecting.

## Features

- **Live Visual Feedback**: Green boxes appear around detected items on your screen
- **Item Labels**: Each box shows the item name below it
- **Real-time Updates**: Boxes update automatically when items are detected
- **Click-through Window**: The overlay doesn't interfere with your mouse clicks
- **Two Modes**:
  - **Manual Scan**: Show boxes from a single scan
  - **Live Scanning**: Continuously scan and update boxes automatically

## How to Use

### In the Detection Tab

1. **Set Screen Area**: First, set your game screen area in the Quick Start tab
2. **Enable Overlay**: Toggle "Show boxes on screen" switch
3. **Scan Items**: Click "Detect Items" to scan and show boxes
4. **Live Scanning** (Optional): Enable "Live scanning (auto-update)" for continuous detection

### Controls

- **"Show boxes on screen" Switch**: Enable/disable the overlay window
- **"Live scanning (auto-update)" Switch**: Enable continuous automatic scanning
- **"🔲 Show Overlay" Button**: Quick toggle for the overlay

## Technical Details

### Overlay Window

- Uses a transparent Tkinter window that stays on top
- Fullscreen overlay that doesn't block mouse clicks
- Updates at 20 FPS (every 50ms)
- Green boxes with 2px thickness
- White text labels on black background

### Detection Integration

- Automatically updates when you run "Detect Items"
- Works with all template images in the `img/` folder
- Shows item name (filename without extension) as label
- Box size defaults to 50x50 pixels (adjustable)

## Configuration

You can customize the overlay appearance by modifying `detection_overlay.py`:

```python
self.config = {
    'box_color': '#00FF00',      # Green boxes
    'box_thickness': 2,          # Line thickness
    'label_bg': '#000000',       # Label background
    'label_fg': '#FFFFFF',       # Label text color
    'label_font_size': 10,        # Font size
    'show_labels': True,          # Show/hide labels
    'opacity': 0.8,              # Window opacity
}
```

## Troubleshooting

### Overlay Not Appearing

1. Check that you've set the screen area first
2. Make sure you've run "Detect Items" at least once
3. Check the Activity tab for error messages
4. Try disabling and re-enabling the overlay switch

### Boxes Not Updating

1. Enable "Live scanning" for automatic updates
2. Or manually click "Detect Items" again
3. Check that template images exist in `img/` folder

### Overlay Blocks Mouse

- The overlay should be click-through, but if it's not:
  - Try restarting the GUI
  - Check Windows permissions
  - The overlay uses Windows API for click-through support

## Files

- `detection_overlay.py`: Core overlay window implementation
- `live_detection_overlay.py`: Integration with GUI and detection system
- `gui_flet.py`: UI controls in Detection tab

## Notes

- The overlay runs in a separate thread to avoid blocking the GUI
- Boxes are drawn using Tkinter Canvas
- The overlay window is always on top but doesn't interfere with gameplay
- Live scanning scans every 1 second by default (configurable)

