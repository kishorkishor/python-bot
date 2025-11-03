# Template Collection Guide

## How Your Existing Templates Were Created

Your current templates in `img/` were created by:
1. Taking a screenshot of the game board
2. Manually cropping small squares (~50x50 pixels) around each item
3. Saving with descriptive names (e.g., `cow1.png`, `wheat2.png`)

**The new Template Collector tool automates this process!**

## Using the Template Collector

### Method 1: From GUI (Easiest)

1. **Launch Farm Merger Pro**
   ```bash
   python farm_merger/gui.py
   ```

2. **Open Template Collector**
   - Click "Advanced Features" button
   - Expand "▶ Template Collector" section
   - Choose what to collect:
     - **📸 Collect Items** - Animals, crops on board (50x50px)
     - **📸 Collect UI** - Buttons, icons (60x60px)
     - **📸 Collect Producers** - Items showing ready/sparkle state (50x50px)

3. **Collect Templates**
   - Black semi-transparent overlay appears
   - **Left-click** on any item in the game to capture it
   - Popup asks for a name → type name → press OK
   - Template saved to `img/{category}/{name}.png`
   - **Right-click** or press **ESC** to exit

4. **View Results**
   - Check `img/items/`, `img/ui_elements/`, or `img/producers/`
   - Templates ready for detection immediately!

### Method 2: Standalone CLI

```bash
cd farm_merger
python template_collector.py
```

**Menu options:**
- **1** = Collect game items (animals, crops)
- **2** = Collect UI elements (buttons, icons)
- **3** = Collect producers (ready states)
- **4** = Custom category and size
- **5** = Free mode (click anything)

## What Templates to Collect

### For Full Automation, You Need:

#### 1. UI Elements (`img/ui_elements/`)
Essential for navigation and interaction:
- `claim_button.png` - "Claim" reward button
- `close_button.png` - X close button
- `ok_button.png` - OK confirmation
- `collect_button.png` - Collect goods button
- `expand_button.png` - Land expansion button
- `repair_button.png` - Building repair button
- `energy_icon.png` - Energy indicator
- `coin_icon.png` - Coin counter
- `order_board_icon.png` - Order board tab

**How to capture:**
- Make sure UI elements are visible in game
- Click "📸 Collect UI" from GUI
- Click each button/icon when visible
- Name them descriptively

#### 2. Producers Ready State (`img/producers/`)
For resource collection automation:
- `cow_ready.png` - Cow with milk/goods visible
- `chicken_ready.png` - Chicken with eggs
- `pig_ready.png` - Pig with goods
- `wheat_ready.png` - Wheat ready to harvest
- `corn_ready.png` - Corn with sparkles

**How to capture:**
- Wait for producers to have goods ready (sparkles/icons appear)
- Click "📸 Collect Producers"
- Click on the producer showing ready indicator
- Name with `{item}_ready` pattern

#### 3. Order Items (`img/orders/`)
For order fulfillment:
- `order_wheat.png` - Wheat icon in order requirement
- `order_milk.png` - Milk icon
- `order_egg.png` - Egg icon

**How to capture:**
- Open order board in game
- Use custom mode: `python template_collector.py` → option 4
- Category: `orders`, Size: `40`
- Click on item icons in orders

#### 4. Popups (`img/popups/`)
For handling interruptions:
- `levelup_popup.png` - Level up screen
- `daily_reward.png` - Daily login bonus
- `not_enough_energy.png` - Energy warning
- `ad_popup.png` - Ad offer (to dismiss)

**How to capture:**
- Wait for popup to appear OR trigger it (level up, etc.)
- Use free mode or custom category
- Capture the distinctive part of popup

## Tips for Good Templates

### ✓ DO:
- Capture templates at the same zoom level you play at
- Use tight crops (minimal extra space)
- Capture multiple variations if item appearance changes
- Name templates descriptively (`cow_ready` not `template1`)
- Test detection after capturing (run a scan)

### ✗ DON'T:
- Include too much background
- Crop different sizes for same category
- Use special characters in names (stick to letters, numbers, underscore)
- Capture blurry or partially obscured items
- Forget to test if template actually detects

## Crop Size Guidelines

Match your existing templates:

| Category | Crop Size | Example |
|----------|-----------|---------|
| Game items (animals, crops) | **50x50** | `cow1.png` |
| UI buttons | **60x60** | `claim_button.png` |
| Producers ready | **50x50** | `cow_ready.png` |
| Order icons | **40x40** | `order_wheat.png` |
| Popup sections | **100x100** | `levelup_popup.png` |

## Verifying Templates Work

After collecting templates, test them:

1. **Quick test in Python:**
   ```python
   from item_finder import ImageFinder
   
   # Test detection
   points, _ = ImageFinder.find_image_on_screen(
       "img/ui_elements/claim_button.png",
       0, 0, 1920, 1080,  # Your screen resolution
       resize_factor=1.0
   )
   
   print(f"Found {len(points)} matches")
   ```

2. **Test in GUI:**
   - Run merge automation
   - Check log for detection messages
   - If template not found, recapture with better crop

## Batch Collection Workflow

**Goal: Collect all needed templates in 30 minutes**

1. **Prepare game** (10 min)
   - Position game window
   - Make sure various items are visible
   - Have some producers with goods ready
   - Open different menus to see UI elements

2. **Collect items** (5 min)
   - Launch collector: "📸 Collect Items"
   - Click 10-15 different items on board
   - Name: `{item}{tier}` (e.g., `cow1`, `wheat2`)

3. **Collect UI** (5 min)
   - Launch collector: "📸 Collect UI"
   - Navigate to different screens
   - Click each button/icon type once
   - Name descriptively

4. **Collect producers** (5 min)
   - Wait for goods to be ready (sparkles appear)
   - Launch collector: "📸 Collect Producers"
   - Click ready producers
   - Name: `{item}_ready`

5. **Collect orders** (3 min)
   - Open order board
   - Custom collector with size 40
   - Click order item icons
   - Name: `order_{item}`

6. **Test & verify** (2 min)
   - Check saved files in `img/` folders
   - Run quick detection test
   - Recapture any that look wrong

## Troubleshooting

**"Template not detected during automation"**
- Template might be too small or too large
- Background might vary too much
- Try capturing with more/less background
- Check threshold in `img/catalog.json`

**"Collector won't start / crashes"**
- Make sure `pynput` is installed: `pip install pynput`
- Try running as administrator (Windows)
- Check Python console for error messages

**"Can't name template / popup doesn't appear"**
- Tkinter dialog might be behind game window
- Alt+Tab to find the naming popup
- Or check Windows taskbar

**"Wrong crop size captured"**
- Double-check the crop_size parameter
- Existing items are 50x50, match that size
- Can recapture with correct size

## Advanced: Scripted Collection

For developers who want to automate the automation:

```python
from template_collector import BatchTemplateCollector

# Define your checklist
items = ["cow1", "cow2", "chicken1", "wheat1"]

# Batch collect with prompts
collector = BatchTemplateCollector("items", crop_size=50)
collector.collect_checklist(items)
```

This prompts you to capture each item in sequence.

## Next Steps

After collecting templates:

1. **Update catalog.json** (optional)
   - Add thresholds for new templates
   - Mark reference templates
   - Set priorities

2. **Test automation**
   - Run merge cycle
   - Check if new elements detected
   - Adjust thresholds if needed

3. **Share templates** (optional)
   - Export your `img/` folder
   - Share with other users
   - Help community get started faster

---

**You're now ready to collect all templates needed for full game automation!** 🚀



