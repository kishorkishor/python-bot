# Template Collector Fix - November 2025

## Issue Fixed

**Error**: `_tkinter.TclError: window ".!_querystring" was deleted before its visibility changed`

**Cause**: The template collector was calling `tkinter.simpledialog.askstring()` from a mouse listener callback thread, which caused threading conflicts with tkinter's main loop.

## Solution

### 1. Thread-Safe Click Handling

**Before**:
```python
def on_click(self, x, y, button, pressed):
    if button == mouse.Button.left:
        self.capture_at_position(x, y)  # Called directly from listener thread
```

**After**:
```python
def on_click(self, x, y, button, pressed):
    if button == mouse.Button.left:
        self.click_queue.put((x, y))  # Add to queue for main thread

def process_click_queue(self):
    """Process clicks from the queue in the main thread"""
    while not self.click_queue.empty():
        x, y = self.click_queue.get_nowait()
        self.capture_at_position(x, y)
    self.root.after(100, self.process_click_queue)
```

### 2. Custom Dialog Instead of simpledialog

**Before**:
```python
name = simpledialog.askstring(
    "Template Name",
    "Name this template:",
    parent=None  # This was causing the threading issue
)
```

**After**:
```python
# Create a custom dialog with proper parent handling
dialog = tk.Toplevel()
dialog.title("Template Name")
# ... custom dialog implementation
dialog.wait_window()  # Wait for dialog to close
```

### 3. Right-Click Exit Fix

**Before**:
```python
if button == mouse.Button.right:
    self.cleanup()  # Called from listener thread
```

**After**:
```python
if button == mouse.Button.right:
    self.root.after(0, self.cleanup)  # Schedule in main thread
```

## New Features Added

### 1. Live Preview

Shows a preview of the captured image in the top-right corner:

```python
def show_preview(self, screenshot):
    """Show a preview of the captured image"""
    preview_size = 200
    img = screenshot.copy()
    img.thumbnail((preview_size, preview_size), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    self.preview_label.config(image=photo)
```

### 2. Smart Suggestions

After each capture, shows a helpful suggestion for what to capture next:

```python
def get_suggestion(self):
    """Get a suggestion for what to capture next"""
    suggestions = {
        "items": [
            "💡 Suggestion: Capture different tiers (cow1, cow2, cow3)",
            "💡 Suggestion: Capture items in 'ready' state with sparkles",
            # ...
        ],
        "ui_elements": [
            "💡 Suggestion: Capture the 'close' button (X) from popups",
            # ...
        ],
        # ... more categories
    }
```

Examples:
- **Items**: "💡 Suggestion: Capture different tiers of the same item (cow1, cow2, cow3)"
- **UI Elements**: "💡 Suggestion: Capture the 'close' button (X) from popups"
- **Producers**: "💡 Suggestion: Make sure the producer has goods ready (sparkles visible)"
- **Orders**: "💡 Suggestion: Capture individual order items from the order board"

### 3. Session Summary

When you exit the collector, it shows a complete summary:

```
============================================================
TEMPLATE COLLECTOR - SESSION SUMMARY
============================================================
Total captured: 5 templates
Saved to: img/ui_elements/

Captured templates:
  1. close_button.png → img/ui_elements/close_button.png
  2. ok_button.png → img/ui_elements/ok_button.png
  3. claim_button.png → img/ui_elements/claim_button.png
  4. energy_icon.png → img/ui_elements/energy_icon.png
  5. coin_icon.png → img/ui_elements/coin_icon.png

💡 Next steps:
  1. Test templates in the Detection tab
  2. Adjust threshold if needed (0.70-0.85)
  3. Capture more variations if detection fails
============================================================
```

### 4. Template Tracking

The collector now tracks all captured templates in a list:

```python
self.captured_templates = []  # Track what was captured

# After saving:
self.captured_templates.append({
    "name": name,
    "path": filepath,
    "image": screenshot
})
```

## Usage

The template collector now works flawlessly:

1. **Launch**: `python template_collector.py` or use GUI button
2. **Click**: Left-click on game elements to capture
3. **Preview**: See what you captured in top-right corner
4. **Name**: Enter a name in the dialog
5. **Suggestion**: Get a helpful suggestion for what to capture next
6. **Exit**: Right-click or press ESC
7. **Summary**: Review all captured templates

## Technical Details

### Threading Model

- **Mouse Listener Thread**: Detects clicks and adds to queue
- **Main Thread**: Processes queue, shows dialogs, updates UI
- **Queue**: `queue.Queue()` for thread-safe communication

### Dialog Improvements

- Custom `tk.Toplevel()` dialog instead of `simpledialog`
- Proper parent handling
- Enter key to save, Escape to cancel
- Always on top for visibility

### Error Handling

- Try-except blocks for screenshot capture
- Graceful handling of dialog cancellation
- Safe cleanup of resources

## Testing

Tested scenarios:
- ✅ Multiple rapid clicks
- ✅ Dialog cancellation
- ✅ Right-click exit during dialog
- ✅ ESC key exit
- ✅ Long capture sessions (20+ templates)
- ✅ Different categories (items, ui_elements, producers, orders)

## Compatibility

- **Python**: 3.7+
- **OS**: Windows 10/11
- **Dependencies**: tkinter, pynput, pyautogui, PIL

## Known Limitations

None! The threading issue is fully resolved.

## Future Enhancements

Potential improvements:
- [ ] Undo last capture
- [ ] Edit template name after saving
- [ ] Batch rename templates
- [ ] Auto-suggest names based on image content
- [ ] Template quality checker

---

**Fixed**: November 1, 2025  
**Status**: ✅ Fully Working  
**Breaking Changes**: None (backward compatible)



