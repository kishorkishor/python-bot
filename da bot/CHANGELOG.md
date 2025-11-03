# Farm Merger Pro - Changelog

## Version 2.4.1 - Ultra-Modern Glassmorphism UI

### 🎨 Complete UI Redesign
- **Glassmorphism Theme**: New ultra-modern design with smooth glass-like effects
- **Enhanced Color Palette**: Vibrant blue accents with perfect purple gradients
- **Smoother Animations**: Ultra-smooth rounded corners (18-24px) and transitions
- **Better Spacing**: Perfected padding and margins for professional look
- **Modern Typography**: Pure white text with perfect hierarchy

### 🖼️ Preview Window Fix
- **Fixed Close Button**: Preview windows now properly close when clicking X button
- **Added Protocol Handler**: `WM_DELETE_WINDOW` event now correctly handled
- **Smooth Exit**: Both area and point selectors exit cleanly on window close

### 🏷️ Better Button Labels
- **🎯 Collect**: Renamed from "📸 Capture Items" for clarity
- **🎮 Game UI**: Renamed from "📸 Capture UI" for better understanding
- **✂️ Cut Items**: Renamed from "📸 Producers" to match game terminology

### ⚡ Enhanced Theme Features
- **Tab Styling**: Smooth tab transitions with glassmorphism effects
- **Button Glow**: Enhanced 2.5px borders with subtle glow effects
- **Perfect Rounding**: 14-18px rounded corners throughout
- **Glass Panels**: Semi-transparent panels with beautiful borders
- **Hover States**: Smooth color transitions on all interactive elements

### 🎯 Visual Improvements
- **Status Indicators**: Cleaner, more visible status messages
- **Better Contrast**: Pure white text (#FFFFFF) for maximum readability
- **Color-Coded Actions**: Green (success), Orange (warning), Red (danger)
- **Professional Polish**: Every element refined for premium feel

### ✨ User Experience
- **Smoother Interactions**: All buttons and controls feel more responsive
- **Better Visual Hierarchy**: Clear distinction between sections
- **Modern Icons**: Updated emojis and icons for better clarity
- **Professional Appearance**: App looks and feels like premium software

### 📊 Technical Details
- **Updated Theme Engine**: Enhanced DearPyGUI theme configuration
- **Better Button Themes**: Refined `create_button_theme()` function
- **Improved Colors**: Carefully tuned RGBA values for perfect appearance
- **Enhanced Fonts**: Optimized font sizes (18px primary, 24px headers, 34px hero)

## Version 2.4 - Enhanced Screenshot UI & Stability Fix

### 🎯 Revolutionary Screenshot Interface
- **Live Preview System**: After selecting regions/points, see exactly what you captured before confirming
- **Interactive Selection**: Real-time dimension display (width × height) while dragging
- **Smart Confirmation**: Preview window with Confirm/Cancel buttons - no more guessing if you got it right!
- **Undo Support**: Press Backspace to undo the last point selection (for merging points)
- **ESC to Cancel**: Press ESC anytime to abort and retry the selection
- **Professional Styling**: Modern UI with color-coded instructions and styled buttons

### 🔧 Screenshot Selector Features
**Area Selection** (for game region & box counter):
- Drag to select rectangular area
- Live dimensions displayed while selecting
- Blue dashed outline with smooth animation
- Preview shows captured screenshot with confirm/cancel options
- Coordinates and size info displayed: `(x1, y1) → (x2, y2) | Size: W×H`

**Point Selection** (for merge spots & box button):
- Click to place numbered markers (1, 2, 3...)
- Progress counter: "Click 2 points • ESC: Cancel • Backspace: Undo"
- Red circular markers with white numbers
- Preview shows screenshot with all points marked
- Undo last point with Backspace key
- Coordinates listed for each point

### 🐛 Critical Bug Fixes
- **Fixed Self-Loop Issue**: Completely rewrote selector cleanup logic to prevent infinite loops
- **Proper Tkinter Management**: Fixed mainloop blocking that prevented return to main GUI
- **Resource Cleanup**: Added comprehensive cleanup with try-catch blocks
- **No More Hanging**: Selectors now properly destroy and return control
- **Memory Leaks Fixed**: Proper listener stopping and window destruction

### ⚙️ Technical Improvements
- **Non-Blocking Architecture**: Selectors no longer freeze the main application
- **Exception Handling**: Comprehensive error catching prevents crashes
- **Preview Window Centering**: Preview windows automatically centered on screen
- **Image Scaling**: Intelligent scaling maintains aspect ratio (max 800×600)
- **Visual Feedback**: Status changes reflected in UI colors (dark blue → green when complete)
- **Added pynput**: Dependency properly added to requirements.txt

### 🎨 UI/UX Enhancements
- **Modern Design**: Segoe UI font, rounded buttons, professional color scheme
- **Color Coding**: 
  - Blue (#3498db) for selection outlines
  - Green (#27ae60) for confirm buttons
  - Red (#e74c3c) for cancel/markers
  - Dark (#2c3e50) for instruction backgrounds
- **Button Styling**: Flat design with hover states and cursor changes
- **Cross Cursor**: Selection areas show crosshair cursor for precision
- **Top-Most Windows**: All selector windows stay on top for visibility

### 🚀 User Experience
- **See Before You Commit**: No more trial and error - see exactly what you selected
- **Quick Corrections**: Cancel and retry if selection isn't perfect
- **Clear Instructions**: On-screen guidance with keyboard shortcuts
- **Professional Feel**: Polished interface matches modern application standards
- **Confidence Building**: Visual confirmation reduces user anxiety about selections

## Version 2.3 - Intelligent Detection Upgrade 

### Template Metadata & Grid Discovery
- **Catalog Driven**: New `img/catalog.json` controls thresholds, priorities, and reference templates.
- **Auto Grid Detection**: Board scanner estimates rows/cols and updates the planner on each pass.
- **Manual Overrides**: Toggle auto-detect off to lock custom grids; overrides persist in config.

### Live Box Counter & Automation Sync
- **OCR Integration**: Optional counter capture powered by Tesseract/pytesseract keeps counts in sync.
- **Runtime Refresh**: Merge loop polls OCR every second and preloads values before new runs.
- **Fallback Ready**: UI reverts to manual entry when OCR is unavailable.

### UI & UX Updates
- **Status Panels**: Mode text reflects OCR availability and highlights detected counts.
- **Theme Polish**: Advanced planner surfaces detection status with contextual colours.
- **Logging Hook**: Merge logs now feed box counter updates for consistent telemetry.

## Version 2.2 - Production Performance Upgrade 

### ⚡ Instant Response & Performance
- **Instant Toggle**: Press = key to instantly start/stop merge process (no delays!)
- **Faster Execution**: Reduced all delays by 50-80% for snappy performance
- **Optimized Polling**: UI updates 5x faster (0.1s vs 0.5s intervals)
- **Smart Termination**: Instant process termination with force-kill fallback
- **Batch Processing**: Log messages processed in batches for better performance
- **Production Ready**: System optimized for continuous use with minimal resource usage

### 🎯 User Experience Improvements
- **One-Key Control**: = key toggles start/stop instantly
- **Clear Status**: Button shows "▶ Enable = Toggle" and "⏹ Disable"
- **Visual Feedback**: Instant UI updates with status indicators
- **Faster Merging**: Reduced drag delays from 0.1s to 0.05s
- **Quick Box Clicks**: Box clicking optimized to 0.3s intervals
- **Responsive UI**: All operations feel instant and snappy

### 🎯 Zero-Box Support & Smart Logic
- **Works with 0 boxes**: System continues without clicking box button when no boxes available
- **Smart Box Logic**: Only clicks when boxes are available (1+)
- **Flexible Usage**: Handles any box count (0, 1, 5, 100+)
- **Status Indicators**: Real-time box availability status with clear warnings
- **Continuous Operation**: Never stops due to box count - only stops when you press =

### 🛠️ Production Features
- **Enhanced Batch Files**: Professional launcher with full dependency validation
- **Auto-Install Dependencies**: Automatically installs missing packages
- **Startup Validation**: Checks for img folder and image files on launch
- **Requirements File**: Easy dependency management with requirements.txt
- **Better Error Handling**: Comprehensive validation with helpful error messages
- **Progress Indicators**: Beautiful startup sequence with step-by-step feedback

### 🎨 UI/UX Enhancements
- **Status Indicators**: Real-time box availability status with emoji warnings
- **Better Error Messages**: Clear, actionable error descriptions with emoji indicators
- **Professional Launcher**: Beautiful startup sequence with progress indicators
- **Smart Validation**: Prevents common configuration errors before they happen
- **Enhanced Feedback**: Startup messages show system status and readiness

## Version 2.1 - Advanced Features Upgrade

### 🎯 Advanced Sorting Improvements
- **Manual Slot Selection**: New "Manual Select" button lets you click each slot position yourself
- **Step-by-Step Workflow**: Clear 4-step process (Configure Grid → Detect Slots → Review → Sort)
- **Better Visual Feedback**: Icon-based buttons (📋 Generate Plan, ▶ Execute Sort)
- **Cleaner Tables**: Reduced clutter with icons (✓/✗ for status, ★ for item levels)
- **Summary Stats**: Live counts showing total/occupied/enabled slots and plan moves
- **Improved Detection**: Both auto-scan and manual selection modes for slot detection
- **Scrollable Tables**: Tables now have fixed heights with scrolling for better layout

### 🎨 UI/UX Enhancements
- **Larger Box Count Display**: Box counter now uses larger header font and is more visible
- **Better Color Coding**: Red at 0 boxes, orange at 1-3, green at 4+
- **Wider Layout**: Increased window size to 950×720 for better content visibility
- **Clearer Labels**: Simplified button text with intuitive icons and descriptions
- **Compact Actions**: Single-icon buttons (🔄 toggle, 📍 adjust, ↺ reset) save space

### 🔧 Functional Upgrades
- **Smart Item Display**: Item names show star ratings (★★★) instead of technical filenames
- **Real-time Updates**: All summaries update immediately when changes are made
- **Better Logging**: Clearer messages with checkmarks (✓) and emojis for status
- **Flexible Box Usage**: System now works with ANY box count > 0
  - If you have 1 box, it clicks once and stops
  - If you have 3 boxes, it clicks 3 times and stops
  - If you have 5+ boxes, it clicks 5 times per cycle
  - Only stops when boxes reach exactly 0 (not at 5 anymore!)
- **Smart Color Warnings**: Red at 0, Orange at 1-3, Green at 4+

## Version 2.0 - Major UI Overhaul

### 🎨 Visual Improvements
- **Modern Dark Theme**: Professional color scheme with dark backgrounds and vibrant accents
- **Rounded Corners**: Smooth, modern design with rounded UI elements
- **Better Typography**: Clear, hierarchical text with proper sizing and colors
- **Professional Branding**: New header with emoji icon and developer credit
- **Status Indicators**: Checkmarks (✓) show when selections are complete
- **Color-Coded Buttons**: Green for start, red for stop, blue for actions

### 🔧 Functionality Enhancements
- **Auto-Save Configuration**: All settings automatically saved to JSON file
- **Auto-Load on Startup**: Previous settings restored when app launches
- **Resizable Window**: Scalable UI that adapts to different screen sizes
- **Responsive Layout**: Elements adjust to window size changes
- **Advanced Slot Controls**: Board scans now auto-fill slot centers, with Adjust/Reset tools for manual fine-tuning
- **Better Default Values**: 
  - Zoom level: 1.2x (was 1.0)
  - Box amount: 6 (was 0)
  - Drag duration: 0.55s (was 0.25s)

### 🐛 Bug Fixes
- **Fixed**: Stop button now signals the merge monitor reliably and removes the registered hotkey
- **Fixed**: Start button not visible (child window was too tall)
- **Fixed**: UI elements being cut off at bottom of window
- **Fixed**: Hotkey registration now properly saves to config
- **Improved**: Button labels now show meaningful text instead of blank
- **Improved**: Better feedback when selecting areas and points

### 🚀 User Experience
- **One-Click Launch**: Added batch files for easy startup
- **Error Checking**: Professional launcher checks for Python installation
- **Helpful Tooltips**: Descriptive text for every control
- **Live Feedback**: Activity log shows all important actions
- **Better Spacing**: Improved visual hierarchy and organization

### 📁 New Files
- `Farm Merger Pro.bat` - Professional launcher with error checking
- `run_farm_merger.bat` - Simple launcher
- `farm_merger_config.json` - Auto-generated configuration file
- `README.md` - Comprehensive documentation
- `CHANGELOG.md` - This file

### 🎯 Configuration Persistence
All these settings are now saved automatically:
- Merge count selection
- Screen area coordinates
- Merging point locations
- Box button position
- Start and pause hotkeys
- Game zoom level
- Drag duration
- Box amount

---

## Version 1.0 - Initial Release

Basic functionality:
- Image recognition using OpenCV
- Drag and drop merging
- Hotkey controls
- Basic GUI with DearPyGUI
- Screen area selection
- Merging points configuration

---

*Developed by Kishor with precision and attention to detail*

