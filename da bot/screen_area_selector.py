"""Screen region capture helpers for Kishor Farm Merger Pro."""

import threading
import time

try:
    import tkinter as tk
    from tkinter import ttk
    TK_AVAILABLE = True
except Exception:
    tk = None
    ttk = None
    TK_AVAILABLE = False

try:
    from pynput import mouse
except Exception:
    mouse = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

from pyautogui_safe import pyautogui

class ScreenAreaSelector:
    def __init__(self):
        self.root = None
        self.canvas = None
        self.listener = None
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.selection_complete = False
        self.coordinates = None
        
        self._headless = not (TK_AVAILABLE and mouse and Image and ImageTk)
        if self._headless:
            width, height = pyautogui.size()
            self.coordinates = (0, 0, width, height)
            print("[warn] tkinter or display dependencies unavailable; using full-screen area.")
            return
        
        # Run in a separate thread to prevent blocking
        self._run_selector()

    def _run_selector(self):
        """Run the selection interface"""
        try:
            self.root = tk.Tk()
            self.root.overrideredirect(True)
            self.root.wm_attributes("-topmost", True)
            self.root.wm_attributes("-alpha", 0.3)
            
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            
            self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0, cursor="cross")
            self.canvas.pack(fill=tk.BOTH, expand=True)

            # Enhanced instruction text with background
            info_text = "Drag to select the area • ESC to cancel"
            text_bg = self.canvas.create_rectangle(
                screen_width//2 - 250, 30, 
                screen_width//2 + 250, 90, 
                fill="#2c3e50", outline=""
            )
            self.canvas.create_text(
                screen_width // 2, 60, 
                text=info_text, 
                font=("Segoe UI", 18, "bold"), 
                fill="white"
            )

            # Bind keyboard events
            self.root.bind("<Escape>", self._on_escape)
            
            self.listener = mouse.Listener(
                on_click=self.on_click, 
                on_move=self.on_move
            )
            self.listener.start()

            self.root.protocol("WM_DELETE_WINDOW", self._cleanup)
            self.root.mainloop()
            
        except Exception as e:
            print(f"Error in selector: {e}")
            self._cleanup()

    def _on_escape(self, event):
        """Handle ESC key to cancel"""
        self.selection_complete = False
        self._cleanup()

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.start_x = x
            self.start_y = y
            if self.canvas:
                self.rect = self.canvas.create_rectangle(
                    x, y, x, y, 
                    outline="#3498db", 
                    width=3,
                    dash=(5, 5)
                )
                # Add dimension text
                self.dim_text = self.canvas.create_text(
                    x, y - 20,
                    text="",
                    font=("Segoe UI", 12, "bold"),
                    fill="#3498db"
                )
        else:
            self.end_x, self.end_y = x, y
            self.selection_complete = True
            if self.listener:
                self.listener.stop()
            # Show preview before closing
            self.root.after(100, self._show_preview)

    def on_move(self, x, y):
        if self.rect and self.canvas:
            try:
                self.canvas.coords(self.rect, self.start_x, self.start_y, x, y)
                # Update dimension text
                width = abs(x - self.start_x)
                height = abs(y - self.start_y)
                dim_str = f"{width} × {height}"
                mid_x = (self.start_x + x) / 2
                self.canvas.coords(self.dim_text, mid_x, self.start_y - 20)
                self.canvas.itemconfig(self.dim_text, text=dim_str)
            except:
                pass

    def _show_preview(self):
        """Show preview window of selected area"""
        print(f"[debug] _show_preview called. selection_complete={self.selection_complete}, start={self.start_x},{self.start_y}, end={self.end_x},{self.end_y}")
        
        if not self.selection_complete:
            print("[debug] Selection not marked complete")
            self._cleanup()
            return
            
        if not all([self.start_x is not None, self.start_y is not None, self.end_x is not None, self.end_y is not None]):
            print("[debug] Missing coordinates")
            self._cleanup()
            return
            
        # Normalize coordinates
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        print(f"[debug] Normalized coordinates: ({x1},{y1}) to ({x2},{y2}), size={width}x{height}")
        
        # Ensure minimum size (reduced for resource tracking - coins/gems can be small)
        if width < 20 or height < 20:
            print(f"[warn] Selection too small: {width}x{height}. Minimum 20x20 pixels required. Please drag to select an area.")
            self._cleanup()
            return
        
        try:
            # Destroy selection overlay
            if self.canvas:
                self.canvas.destroy()
            self.root.withdraw()
            
            # Small delay to let overlay disappear
            time.sleep(0.1)
            
            # Capture screenshot of selected area
            screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
            
            # Create preview window
            self._show_preview_window(screenshot, x1, y1, x2, y2)
            
        except Exception as e:
            print(f"[error] Preview error: {e}")
            import traceback
            print(f"[error] Traceback: {traceback.format_exc()}")
            # On error, still save coordinates but don't show preview
            self.coordinates = (x1, y1, x2, y2)
            self._cleanup()

    def _show_preview_window(self, screenshot, x1, y1, x2, y2):
        """Display preview confirmation window"""
        print("[debug] _show_preview_window called")
        try:
            preview_win = tk.Toplevel(self.root)
            preview_win.title("Preview Selected Area")
            preview_win.wm_attributes("-topmost", True)
            print("[debug] Preview window created")
        except Exception as e:
            print(f"[error] Failed to create preview window: {e}")
            import traceback
            print(f"[error] Traceback: {traceback.format_exc()}")
            self.coordinates = (x1, y1, x2, y2)
            self._cleanup()
            return
        
        # Calculate preview size (max 800x600, maintain aspect ratio)
        img_width, img_height = screenshot.size
        max_width, max_height = 800, 600
        scale = min(max_width/img_width, max_height/img_height, 1.0)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize for preview
        preview_img = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(preview_img)
        
        # Main frame
        main_frame = ttk.Frame(preview_win, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Info label
        info_label = ttk.Label(
            main_frame,
            text=f"Selected Region: ({x1}, {y1}) → ({x2}, {y2}) | Size: {x2-x1}×{y2-y1}",
            font=("Segoe UI", 10)
        )
        info_label.pack(pady=(0, 10))
        
        # Image label
        img_label = tk.Label(main_frame, image=photo, relief=tk.SOLID, borderwidth=2)
        img_label.image = photo  # Keep reference
        img_label.pack(pady=5)
        
        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        def confirm():
            self.coordinates = (x1, y1, x2, y2)
            self.selection_complete = True
            # Stop listener immediately
            try:
                if self.listener and self.listener.running:
                    self.listener.stop()
            except:
                pass
            # Destroy preview window
            try:
                preview_win.destroy()
            except:
                pass
            # Cleanup and exit completely
            self.root.after(50, lambda: (self.root.quit(), self.root.destroy()))
        
        def cancel():
            self.coordinates = None
            self.selection_complete = False
            # Stop listener immediately
            try:
                if self.listener and self.listener.running:
                    self.listener.stop()
            except:
                pass
            # Destroy preview window
            try:
                preview_win.destroy()
            except:
                pass
            # Cleanup and exit completely
            self.root.after(50, lambda: (self.root.quit(), self.root.destroy()))
        
        # Handle window close button (X)
        preview_win.protocol("WM_DELETE_WINDOW", cancel)
        
        # Styled buttons
        confirm_btn = tk.Button(
            btn_frame, 
            text="✓ Confirm", 
            command=confirm,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="✗ Cancel",
            command=cancel,
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Center the window
        preview_win.update_idletasks()
        window_width = preview_win.winfo_width()
        window_height = preview_win.winfo_height()
        screen_width = preview_win.winfo_screenwidth()
        screen_height = preview_win.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        preview_win.geometry(f"+{x}+{y}")
        
        preview_win.focus_force()
        preview_win.grab_set()

    def _cleanup(self):
        """Properly cleanup all resources"""
        # Stop mouse listener first
        try:
            if hasattr(self, 'listener') and self.listener and self.listener.running:
                self.listener.stop()
        except:
            pass
        
        # Quit mainloop
        try:
            if self.root:
                self.root.quit()
        except:
            pass
        
        # Destroy root window
        try:
            if self.root:
                self.root.destroy()
        except:
            pass
        
        # Reset state
        self.selection_complete = False

    def get_coordinates(self):
        """Get the selected coordinates"""
        return self.coordinates
