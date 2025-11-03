# 📸 Screenshot UI Guide - Farm Merger Pro v2.4

## 🎯 Overview

The new screenshot interface provides **live preview** and **visual confirmation** for all screen selections. No more guessing if you got it right!

---

## 🖼️ Area Selection (Screen Region & Box Counter)

### Step-by-Step Guide

#### 1️⃣ **Click Selection Button**
Click "📐 Screen Area" or "Select Counter Region" in the main GUI.

#### 2️⃣ **Selection Overlay Appears**
```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│        ┌─────────────────────────────────────┐         │
│        │  Drag to select area • ESC: Cancel  │         │
│        └─────────────────────────────────────┘         │
│                                                           │
│                                                           │
│    Your screen turns semi-transparent white (30%)        │
│    Cursor changes to crosshair (+)                       │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

#### 3️⃣ **Drag to Select**
```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│     1024 × 768  ← Live dimensions!                       │
│     ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐                          │
│     │  Blue dashed outline    │                          │
│     │  (3px width)            │                          │
│     │  #3498db color          │                          │
│     │                         │                          │
│     └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘                          │
│                                                           │
│   Dimensions update in real-time as you drag!            │
└─────────────────────────────────────────────────────────┘
```

#### 4️⃣ **Preview Window**
```
┌───────────────────────────────────────────────────────┐
│  Preview Selected Area                            × │
├───────────────────────────────────────────────────────┤
│                                                         │
│  Selected Region: (100, 200) → (1124, 968)            │
│  Size: 1024×768                                        │
│                                                         │
│  ┌─────────────────────────────────────────────┐      │
│  │                                               │      │
│  │   [Your captured screenshot appears here]    │      │
│  │   Auto-scaled to fit (max 800×600)          │      │
│  │   Maintains aspect ratio                     │      │
│  │                                               │      │
│  └─────────────────────────────────────────────┘      │
│                                                         │
│         ┌──────────────┐  ┌──────────────┐            │
│         │ ✓ Confirm    │  │ ✗ Cancel     │            │
│         └──────────────┘  └──────────────┘            │
│         (Green button)     (Red button)                │
└───────────────────────────────────────────────────────┘
```

#### 5️⃣ **Confirm or Cancel**
- **✓ Confirm**: Accept the selection, returns to main GUI
- **✗ Cancel**: Discard and return to main GUI to try again

---

## 🎯 Point Selection (Merge Slots, Box Button)

### Step-by-Step Guide

#### 1️⃣ **Click Selection Button**
Click "🎯 Merging Slots" (for N points) or "📦 Box Button" (for 1 point)

#### 2️⃣ **Overlay with Instructions**
```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Click 3 points • ESC: Cancel • Backspace: Undo  │  │
│  │ Progress: 0/3                                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                           │
│   Your screen turns semi-transparent white (30%)         │
│   Cursor changes to crosshair                            │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

#### 3️⃣ **Click Points**
```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Click 1 point • ESC: Cancel • Backspace: Undo   │  │
│  │ Progress: 2/3                                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                           │
│         ⭕           ⭕                                    │
│         1            2            ← Red circles          │
│                                     with white numbers   │
│                                                           │
│  Click third point...                                    │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- ⭕ Red circular markers (10px radius)
- **1**, **2**, **3** White numbered labels
- **Backspace** key: Undo last point (removes marker)
- **ESC** key: Cancel entire selection

#### 4️⃣ **Automatic Preview**
After clicking the last point, preview appears automatically:

```
┌───────────────────────────────────────────────────────┐
│  Preview Selected Points                          × │
├───────────────────────────────────────────────────────┤
│                                                         │
│  Selected 3 point(s):                                  │
│  (150, 300) • (450, 300) • (750, 300)                 │
│                                                         │
│  ┌─────────────────────────────────────────────┐      │
│  │                                               │      │
│  │        ⭕        ⭕        ⭕                    │      │
│  │        1         2         3                  │      │
│  │                                               │      │
│  │  [Screenshot with enhanced markers]          │      │
│  │  Markers: 15px radius, bright red            │      │
│  │  100px margin around points                  │      │
│  │                                               │      │
│  └─────────────────────────────────────────────┘      │
│                                                         │
│    ┌──────────────┐  ┌─────────────────────┐          │
│    │ ✓ Confirm    │  │ ✗ Cancel & Retry    │          │
│    └──────────────┘  └─────────────────────┘          │
│    (Green button)     (Red button)                     │
└───────────────────────────────────────────────────────┘
```

#### 5️⃣ **Confirm or Retry**
- **✓ Confirm**: Accept points, returns to main GUI
- **✗ Cancel & Retry**: Discard points and start over

---

## ⌨️ Keyboard Shortcuts

| Key | Action | When |
|-----|--------|------|
| **ESC** | Cancel selection | Anytime during selection |
| **Backspace** | Undo last point | During point selection only |

---

## 🎨 Visual Design

### Color Scheme
```
Selection Overlay:   White, 30% opacity
Selection Outline:   #3498db (Bright Blue), dashed
Dimension Text:      #3498db (Bright Blue)
Instruction BG:      #2c3e50 (Dark Blue-Gray)
Instruction Text:    White

Point Markers:       #e74c3c (Red)
Marker Outline:      #c0392b (Dark Red)
Marker Numbers:      White

Confirm Button:      #27ae60 (Green)
Cancel Button:       #e74c3c (Red)
Button Text:         White
```

### Typography
- **Font:** Segoe UI (Windows native)
- **Title:** 16-18pt bold
- **Body:** 10-12pt regular
- **Buttons:** 11pt bold
- **Markers:** 12pt bold

### Dimensions
- **Marker radius:** 10px (selection), 15px (preview)
- **Button padding:** 20px horizontal, 8px vertical
- **Preview max size:** 800×600 (maintains aspect ratio)
- **Margin around points:** 100px

---

## ✨ Features Comparison

### Before v2.4
```
❌ No preview - blind selection
❌ No undo - start over completely  
❌ No cancel - stuck with mistakes
❌ No dimensions - guessing size
❌ Gets stuck in loop
❌ Frozen UI
```

### After v2.4
```
✅ Full preview before confirming
✅ Backspace to undo points
✅ ESC to cancel anytime
✅ Live dimension display
✅ Smooth return to GUI
✅ Responsive interface
```

---

## 🚀 Quick Tips

1. **For precise selections:** Use the live dimensions to match exact pixel sizes
2. **Made a mistake?** Just press ESC and try again - it's instant!
3. **Adjusting points?** Use Backspace to remove the last point without starting over
4. **Preview unclear?** Click Cancel and try again with better positioning
5. **Multiple attempts:** No problem! The interface is designed for iteration

---

## 🐛 Troubleshooting

### Issue: Selection overlay doesn't appear
- **Solution:** Wait a moment, overlay appears in <100ms
- **Check:** Make sure no other windows are blocking

### Issue: Can't see dimensions while dragging
- **Solution:** Drag slower, dimensions update in real-time
- **Note:** Dimensions appear above the selection rectangle

### Issue: Preview window off-screen
- **Solution:** This shouldn't happen - windows auto-center
- **Workaround:** Press Cancel and try again

### Issue: GUI doesn't respond after preview
- **Solution:** Click either Confirm or Cancel button
- **Note:** Preview window has modal grab (blocks other windows)

### Issue: Undo doesn't work
- **Note:** Backspace only works for point selection, not area selection
- **Area selection:** Use ESC to cancel and restart

---

## 📊 Technical Specs

### Performance
- **Selection overlay:** <100ms to appear
- **Preview generation:** <200ms
- **Image scaling:** Smart algorithm maintains quality
- **Memory usage:** Minimal, cleanup after each operation
- **CPU usage:** Negligible during selection

### Compatibility
- **OS:** Windows 10/11
- **Python:** 3.7+
- **Dependencies:** tkinter, PIL/Pillow, pyautogui, pynput
- **Screen:** Any resolution, any DPI

### Limitations
- **Minimum selection:** 50×50 pixels
- **Maximum preview:** 800×600 (scaled from original)
- **Points margin:** 100px around all points
- **Multiple monitors:** Supported

---

## 🎓 Best Practices

### Area Selection
1. Position your game window in a fixed location
2. Select slightly larger than the actual game area
3. Use the preview to verify you got the full game board
4. Confirm only when borders look correct

### Point Selection  
1. Zoom the game appropriately before selecting
2. Click the center of each slot/button
3. Use the numbered markers to verify sequence
4. Check the preview to ensure points are centered
5. Use Backspace if you misclick

### General Tips
- Take your time - the interface won't timeout
- Use ESC freely - there's no penalty
- Trust the preview - what you see is what you get
- Save your config after successful selections

---

**Made with ❤️ by Kishor**  
**Version 2.4 - November 1, 2025**

