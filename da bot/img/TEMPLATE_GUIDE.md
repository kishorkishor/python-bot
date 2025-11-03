# Template Collection Guide

This guide explains how to collect and organize game element templates for the Farm Merge Valley automation system.

## Directory Structure

```
img/
├── ui_elements/     # UI buttons, icons, and interface elements
├── producers/       # Animals and crops showing ready indicators
├── orders/          # Order board items and requirements
└── [existing]       # Your existing merge item templates
```

## Template Collection Methods

### Method 1: Using the Built-in Template Collector

The GUI includes a template collection tool that makes capturing game elements easy:

1. Launch the GUI: `python gui.py`
2. Navigate to the **⚙️ Settings** tab
3. Click **"📸 Collect UI Templates"** or **"📸 Collect Producer Templates"**
4. The screen will show a transparent overlay
5. **Left-click** on any game element to capture it
6. Enter a descriptive name when prompted
7. The template is automatically saved to the correct directory
8. **Right-click** or press **ESC** to exit capture mode

### Method 2: Manual Screenshot Capture

For more control, you can manually capture templates:

1. Take a screenshot of the game
2. Open in an image editor (Paint, GIMP, Photoshop, etc.)
3. Crop to just the element you want to detect
4. Save as PNG with a descriptive name
5. Place in the appropriate directory

## Template Naming Conventions

Use clear, descriptive names that indicate what the template represents:

### UI Elements (`img/ui_elements/`)
- `close_button.png` - X button to close popups
- `ok_button.png` - OK confirmation button
- `claim_button.png` - Claim rewards button
- `repair_button.png` - Building repair button
- `expand_button.png` - Land expansion button
- `back_button.png` - Back/return button
- `home_button.png` - Return to farm button
- `orders_button.png` - Order board button
- `shop_button.png` - Shop menu button
- `settings_button.png` - Settings button
- `levelup_popup.png` - Level-up screen indicator
- `daily_reward.png` - Daily reward popup
- `not_enough_energy.png` - Energy warning popup

### Producers (`img/producers/`)
- `chicken_ready.png` - Chicken with ready indicator
- `cow_ready.png` - Cow with ready indicator
- `sheep_ready.png` - Sheep with ready indicator
- `wheat_ready.png` - Wheat ready to harvest
- `corn_ready.png` - Corn ready to harvest
- `tomato_ready.png` - Tomato ready to harvest

### Orders (`img/orders/`)
- `order_egg.png` - Egg requirement in order
- `order_milk.png` - Milk requirement in order
- `order_bread.png` - Bread requirement in order
- `order_coins.png` - Coin reward indicator

## Template Quality Guidelines

### Size
- Capture templates at the resolution you play the game at
- Templates should be large enough to be distinctive (minimum 20x20 pixels)
- Don't include too much surrounding context

### Content
- Include only the element itself, not background
- For buttons, capture the entire button including borders
- For icons, capture just the icon
- For ready indicators, include the sparkle/glow effect

### Consistency
- Use the same game graphics settings for all templates
- Capture templates in the same lighting conditions
- Avoid capturing during animations or transitions

## Testing Templates

After collecting templates, test them:

1. Navigate to the **🔍 Detection** tab in the GUI
2. Click **"🔍 Scan Now"** to preview detection
3. Check if your templates are being detected correctly
4. Adjust threshold slider if needed (default: 0.75)
5. If detection fails:
   - Recapture the template with better quality
   - Ensure the template matches current game graphics
   - Try adjusting the resize factor

## Template Organization Tips

1. **Start with essentials**: Focus on UI elements you'll use most (close buttons, popups)
2. **Collect incrementally**: Add templates as you enable new automation features
3. **Test frequently**: Verify each template works before collecting more
4. **Keep backups**: Save a copy of your templates directory
5. **Document custom templates**: Add notes about special templates

## Common Issues and Solutions

### Template Not Detected
- **Solution**: Lower the threshold slider (try 0.70 or 0.65)
- **Solution**: Recapture at exact game resolution
- **Solution**: Ensure game graphics settings haven't changed

### False Positives
- **Solution**: Raise the threshold slider (try 0.80 or 0.85)
- **Solution**: Capture a more unique portion of the element
- **Solution**: Include more distinctive features in the template

### Inconsistent Detection
- **Solution**: Capture multiple variations and test each
- **Solution**: Use the resize factor feature (try 0.9 or 1.1)
- **Solution**: Ensure game is in focus and not minimized

## Advanced: Multi-Resolution Templates

If you play at different resolutions:

1. Create subdirectories: `ui_elements/1920x1080/`, `ui_elements/1280x720/`
2. Capture templates at each resolution
3. Modify detection code to use appropriate template set
4. Or use the resize factor feature to scale templates

## Template Maintenance

- **Review monthly**: Check if game updates changed graphics
- **Update as needed**: Recapture templates after game updates
- **Clean unused**: Remove templates for features you don't use
- **Share with community**: Consider sharing your template set

## Next Steps

After collecting templates:

1. Enable automation features in the **⚙️ Settings** tab
2. Configure screen regions (order board, energy display, coin display)
3. Start with passive automation profile
4. Monitor the **📋 Activity** log for detection results
5. Gradually enable more advanced features

## Support

If you need help with template collection:
- Check the main README.md for troubleshooting
- Review FIXES.md for known issues
- Ensure all dependencies are installed (OpenCV, PyAutoGUI)



