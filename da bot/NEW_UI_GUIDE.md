# New UI Design - Kishor Farm Merger Pro v2.4

## Overview

The GUI has been completely redesigned for better usability, scalability, and visual feedback. The new layout features a **3-column design** with dedicated panels for different workflows.

## Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  KISHOR FARM MERGER PRO - Dark Black & Orange Edition        │
│  Status: Ready  |  Boxes: 6  |  Detected: 0 items           │
├──────────────┬────────────────────┬─────────────────────────┤
│              │                    │                         │
│  ⚙️ SETUP    │  🔍 DETECTION      │  🎮 CONTROL            │
│              │     PREVIEW        │                         │
│  Configure   │                    │  ▶ Enable = Toggle      │
│  detection   │  [Scan Now]        │                         │
│  parameters  │  □ Auto-refresh    │  Activity Log:          │
│              │                    │  ───────────────        │
│  ▶ Basic     │  Total: 0          │  > Ready                │
│  ▶ Fine Tune │  Types: 0          │  > Waiting...           │
│  ▶ Templates │  Last: Not scanned │                         │
│  ▶ Advanced  │                    │                         │
│              │  ┌──────────────┐  │                         │
│  [Save]      │  │ (Item cards) │  │                         │
│  [Load]      │  │  with images │  │                         │
│              │  │  & counts)   │  │                         │
│              │  └──────────────┘  │                         │
└──────────────┴────────────────────┴─────────────────────────┘
```

## Panel Breakdown

### LEFT PANEL - ⚙️ Setup (350px)

**Purpose:** Configure all detection and automation parameters

**Sections:**

1. **▶ Basic Setup** (default open)
   - Merge Count: 3, 5, or 10 items
   - Start Hotkey: Customize start key
   - Pause Hotkey: Customize pause key
   - Screen Area: Define game region
   - Merge Slots: Set drop points

2. **▶ Fine Tuning** (collapsed)
   - Image Scale: Auto-calculate or manual
   - Drag Duration: Speed of drag operations
   - Box Button: Position for box clicks
   - Available Boxes: Manual or OCR counter

3. **▶ Template Tools** (collapsed)
   - 📸 Items: Capture game items (50px)
   - 📸 UI: Capture UI buttons (60px)
   - 📸 Producers: Capture ready states (50px)

4. **▶ Advanced** (collapsed)
   - Auto Sort Planner
   - Grid configuration
   - Slot management

5. **Configuration Buttons**
   - Save Settings
   - Load Settings

---

### MIDDLE PANEL - 🔍 Detection Preview (400px)

**Purpose:** Visual feedback showing what items are currently detected

**Features:**

**Control Bar:**
- 🔄 Scan Now button - Manually trigger detection scan
- □ Auto-refresh checkbox - Auto-scan every 3 seconds

**Stats Summary (3 cards):**
```
┌──────────────┬──────────────┬──────────────┐
│ Total        │ Unique       │ Last Scan    │
│ Detected     │ Types        │              │
│      0       │      0       │ Not scanned  │
└──────────────┴──────────────┴──────────────┘
```

**Detection Grid (scrollable):**

Each detected item displays as a card:
```
┌─────────────────────────────────────┐
│ [🖼️]  Cow 1                         │
│       × 5 detected                  │
│       (120,340), (245,340)...       │
├─────────────────────────────────────┤
│ [🖼️]  Wheat 2                       │
│       × 3 detected                  │
│       (120,410), (245,410)...       │
└─────────────────────────────────────┘
```

**Card Elements:**
- **Thumbnail**: 50x50px image preview
- **Item Name**: Cleaned, readable name
- **Count Badge**: Color-coded by quantity
  - Green (5+): Many items detected
  - Yellow (3-4): Moderate items
  - Gray (1-2): Few items
- **Coordinates**: First 3 detection positions

---

### RIGHT PANEL - 🎮 Control (450px)

**Purpose:** Start/stop automation and monitor activity

**Components:**

1. **Control Buttons:**
   - ▶ Enable = Toggle (Start monitoring)
   - ⏹ Disable (Stop automation)

2. **Activity Log:**
   - Real-time scrolling log
   - Color-coded messages:
     - [info] - Normal operations
     - [warn] - Warnings
     - [error] - Errors
   - 580px tall for maximum visibility

---

## Top Status Bar

**Always visible at the top:**

| Status | Boxes | Detected |
|--------|-------|----------|
| Ready / Running / Paused | Current box count | Total items found |

Colors indicate health:
- Green: Good
- Yellow: Warning
- Red: Error

---

## Key Improvements

### 1. Visual Detection Preview ⭐
**Problem:** Users couldn't see what the bot detected
**Solution:** Live preview panel with thumbnails and counts

### 2. Better Organization
**Problem:** All settings mixed together
**Solution:** Collapsible sections grouped by purpose

### 3. Scalability
**Problem:** Fixed 950px width couldn't fit more features
**Solution:** 1250px width, resizable, 3-column layout

### 4. Real-time Feedback
**Problem:** Only text logs, no visual confirmation
**Solution:** Status bar + detection cards with images

### 5. Template Collection Integration
**Problem:** Template collector was separate tool
**Solution:** Built into GUI with easy access buttons

---

## Workflow Examples

### First-Time Setup

1. **Configure basics** (Left Panel → Basic Setup)
   - Set merge count
   - Select screen area
   - Choose merge points
   
2. **Test detection** (Middle Panel)
   - Click "🔄 Scan Now"
   - Verify items are detected
   - Check counts match what's on screen

3. **Adjust if needed** (Left Panel → Fine Tuning)
   - Click "Auto calculate" for resize factor
   - Adjust drag duration if too fast/slow

4. **Start automation** (Right Panel)
   - Click "▶ Enable = Toggle"
   - Press = key to start merging
   - Monitor log for activity

### Collecting Templates

1. **Open template tools** (Left Panel → ▶ Template Tools)

2. **Click category button:**
   - 📸 Items - For animals/crops
   - 📸 UI - For buttons
   - 📸 Producers - For ready states

3. **Capture templates:**
   - Black overlay appears
   - Left-click items in game
   - Name each template
   - Right-click when done

4. **Verify detection** (Middle Panel)
   - Click "🔄 Scan Now"
   - New templates appear in detection list

### Monitoring Active Automation

1. **Start automation** (Right Panel)
   - Enable monitoring
   - Press = to start

2. **Watch detection panel** (Middle Panel)
   - Enable "Auto-refresh"
   - See live updates every 3 seconds
   - Monitor item counts changing

3. **Check status bar** (Top)
   - Status shows "Running"
   - Box count decrements
   - Detected count updates

4. **Review logs** (Right Panel)
   - Scroll through activity
   - Check for errors/warnings
   - Verify merge operations

### Using Auto-Sort

1. **Configure grid** (Left Panel → Advanced)
   - Enable "Auto-discover grid"
   - Set rows/columns manually if needed

2. **Scan board** (Advanced panel)
   - Click "Auto Scan"
   - Wait for detection
   - Review slot table

3. **Generate plan** (Advanced panel)
   - Click "📋 Generate Plan"
   - Review move sequence
   - Check slot assignments

4. **Execute sort** (Advanced panel)
   - Click "▶ Execute Sort"
   - Watch automation move items
   - Verify in Detection Preview

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `=` | Start/Stop merge (when monitoring enabled) |
| `ESC` | Close template collector overlay |
| `Right Click` | Exit template collector |

---

## Visual Design Elements

### Color Coding

**Accent Orange** (`#FF873C`):
- Primary actions
- Important numbers
- Active states

**Teal/Cyan** (`#00BEA8`):
- Secondary actions
- Success states
- Highlights

**Green** (`#4ABB8C`):
- Success messages
- High counts
- Ready states

**Yellow** (`#FFC56E`):
- Warnings
- Medium counts
- Attention needed

**Red** (`#D6544A`):
- Errors
- Zero counts
- Critical issues

### Typography

- **Hero Font (34px)**: App title
- **Header Font (24px)**: Panel headers, large numbers
- **Button Font (20px)**: Action buttons, item names
- **Primary Font (18px)**: Body text, labels

---

## Responsive Behavior

**Minimum Size:** 1200×800 pixels
**Default Size:** 1250×850 pixels
**Resizable:** Yes

**Scaling:**
- Left panel: Fixed 350px
- Middle panel: Fixed 400px
- Right panel: Fixed 450px
- Spacing: 15px gutters
- Total: ~1215px + padding

**If window resized smaller:**
- Panels maintain minimum widths
- Scrollbars appear as needed
- No content clipping

---

## Configuration Compatibility

**Old configs still work!** The new UI reads the same `farm_merger_config.json` format. All your existing settings, coordinates, and preferences are preserved.

**New features** (auto-save enabled):
- Detection preview settings
- Auto-refresh preferences
- Panel collapse states

---

## Troubleshooting

**"Detection preview shows nothing"**
- Set screen area first (Left Panel → Basic Setup)
- Make sure img/ folder has templates
- Click "🔄 Scan Now" manually
- Check resize factor matches game zoom

**"Images not loading in preview"**
- Verify template files exist in img/
- Check file format is PNG/JPG
- Ensure filenames have no special characters
- Try re-capturing template

**"UI feels cramped"**
- Resize window larger (drag corner)
- Collapse unused sections
- Minimum size is 1200×800

**"Can't see all detected items"**
- Scroll in Detection Preview window
- Items sorted by count (most first)
- Up to 50 items displayed efficiently

---

## Performance Notes

**Detection Preview:**
- Manual scan: ~1-2 seconds for 40 templates
- Auto-refresh: 3 second intervals
- Image loading: Cached after first load
- Memory: ~50MB for 40 thumbnails

**Recommendations:**
- Use manual scan during setup
- Enable auto-refresh only when monitoring
- Disable auto-refresh during active merging
- Clear detections after finished (rescan)

---

## Future Enhancements

Planned for next versions:

1. **Interactive detection map**
   - Click item card to highlight on screen
   - Draw bounding boxes over game
   - Zoom to specific detections

2. **Detection history chart**
   - Track item counts over time
   - Plot merge efficiency
   - Export statistics

3. **Quick presets**
   - Save/load detection configs
   - One-click switching
   - Share configs with community

4. **Enhanced auto-refresh**
   - Configurable interval (1-10s)
   - Smart refresh (only when changed)
   - Pause during active merge

---

**Enjoy the new UI!** Feedback welcome for v2.5 improvements. 🚀



