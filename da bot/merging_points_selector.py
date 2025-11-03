"""Merge point selection tooling for Kishor Farm Merger Pro."""

import tkinter as tk
from tkinter import ttk
from pynput import mouse
from PIL import Image, ImageTk, ImageDraw
import pyautogui
import time

class MergingPointsSelector:
    def __init__(self, point_num):
        self.point_num = point_num
        self.root = None
        self.canvas = None
        self.listener = None
        self.points = []
        self.point_markers = []
        self.selection_complete = False
        
        self._run_selector()

    def _run_selector(self):
        """Run the point selection interface"""
        try:
            self.root = tk.Tk()
            self.root.overrideredirect(True)
            self.root.wm_attributes("-topmost", True)
            self.root.wm_attributes("-alpha", 0.3)
            
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")

            self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0, cursor="crosshair")
            self.canvas.pack(fill=tk.BOTH, expand=True)

            # Enhanced instruction with progress
            self._update_instruction_text()
            
            # Bind keyboard
            self.root.bind("<Escape>", self._on_escape)
            self.root.bind("<BackSpace>", self._on_undo)
            
            self.listener = mouse.Listener(on_click=self.on_click)
            self.listener.start()

            self.root.protocol("WM_DELETE_WINDOW", self._cleanup)
            self.root.mainloop()
            
        except Exception as e:
            print(f"Error in points selector: {e}")
            self._cleanup()

    def _update_instruction_text(self):
        """Update instruction text with progress"""
        if not self.canvas:
            return
            
        screen_width = self.root.winfo_screenwidth()
        
        # Clear previous instruction
        self.canvas.delete("instruction")
        
        remaining = self.point_num - len(self.points)
        if remaining > 0:
            text = f"Click {remaining} point{'s' if remaining > 1 else ''} • ESC: Cancel • Backspace: Undo"
            color = "#2c3e50"
        else:
            text = "Press any key or click to finish"
            color = "#27ae60"
        
        # Background box
        self.canvas.create_rectangle(
            screen_width//2 - 350, 20,
            screen_width//2 + 350, 100,
            fill=color, outline="", tags="instruction"
        )
        
        # Main text
        self.canvas.create_text(
            screen_width // 2, 50,
            text=text,
            font=("Segoe UI", 16, "bold"),
            fill="white",
            tags="instruction"
        )
        
        # Progress indicator
        if self.point_num > 1:
            progress_text = f"Progress: {len(self.points)}/{self.point_num}"
            self.canvas.create_text(
                screen_width // 2, 75,
                text=progress_text,
                font=("Segoe UI", 12),
                fill="white",
                tags="instruction"
            )

    def _on_escape(self, event):
        """Cancel selection"""
        self.points = []
        self.selection_complete = False
        self._cleanup()

    def _on_undo(self, event):
        """Undo last point"""
        if self.points:
            self.points.pop()
            if self.point_markers:
                marker = self.point_markers.pop()
                self.canvas.delete(marker["oval"])
                self.canvas.delete(marker["text"])
            self._update_instruction_text()

    def on_click(self, x, y, button, pressed):
        if not pressed:
            return
            
        if len(self.points) < self.point_num:
            self.points.append((x, y))
            
            # Create visual marker
            marker_id = len(self.points)
            oval = self.canvas.create_oval(
                x-10, y-10, x+10, y+10,
                fill="#e74c3c",
                outline="#c0392b",
                width=3
            )
            text = self.canvas.create_text(
                x, y,
                text=str(marker_id),
                font=("Segoe UI", 12, "bold"),
                fill="white"
            )
            
            self.point_markers.append({"oval": oval, "text": text})
            self._update_instruction_text()
            
            if len(self.points) == self.point_num:
                self.selection_complete = True
                if self.listener:
                    self.listener.stop()
                # Show preview after short delay
                self.root.after(500, self._show_preview)

    def _show_preview(self):
        """Show preview of selected points"""
        if not self.selection_complete or not self.points:
            self._cleanup()
            return
        
        try:
            # Hide selection overlay
            if self.canvas:
                self.canvas.destroy()
            self.root.withdraw()
            
            time.sleep(0.1)
            
            # Calculate bounding box
            xs = [p[0] for p in self.points]
            ys = [p[1] for p in self.points]
            margin = 100
            x1 = max(0, min(xs) - margin)
            y1 = max(0, min(ys) - margin)
            x2 = max(xs) + margin
            y2 = max(ys) + margin
            
            # Capture screenshot
            screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
            
            # Draw points on screenshot
            draw = ImageDraw.Draw(screenshot)
            for i, (px, py) in enumerate(self.points, 1):
                # Adjust coordinates relative to screenshot
                rel_x = px - x1
                rel_y = py - y1
                
                # Draw circle
                radius = 15
                draw.ellipse(
                    [rel_x-radius, rel_y-radius, rel_x+radius, rel_y+radius],
                    fill=(231, 76, 60),
                    outline=(192, 57, 43),
                    width=3
                )
                
                # Draw number
                text = str(i)
                # Simple text positioning (center of circle)
                bbox = draw.textbbox((rel_x, rel_y), text, anchor="mm")
                draw.text((rel_x, rel_y), text, fill="white", anchor="mm")
            
            self._show_preview_window(screenshot)
            
        except Exception as e:
            print(f"Preview error: {e}")
            self._cleanup()

    def _show_preview_window(self, screenshot):
        """Display preview confirmation window"""
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Preview Selected Points")
        preview_win.wm_attributes("-topmost", True)
        
        # Calculate preview size
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
        points_text = " • ".join([f"({x}, {y})" for x, y in self.points])
        info_label = ttk.Label(
            main_frame,
            text=f"Selected {len(self.points)} point(s): {points_text}",
            font=("Segoe UI", 10),
            wraplength=new_width
        )
        info_label.pack(pady=(0, 10))
        
        # Image label
        img_label = tk.Label(main_frame, image=photo, relief=tk.SOLID, borderwidth=2)
        img_label.image = photo
        img_label.pack(pady=5)
        
        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        def confirm():
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
            self.points = []
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
            text="✗ Cancel & Retry",
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
        
        # Center window
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
        try:
            if self.listener and self.listener.running:
                self.listener.stop()
        except:
            pass
        
        try:
            if self.root:
                self.root.quit()
        except:
            pass
        
        try:
            if self.root:
                self.root.destroy()
        except:
            pass

    def get_points(self):
        """Get the selected points"""
        return self.points
