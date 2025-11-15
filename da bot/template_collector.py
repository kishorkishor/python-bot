"""Smart template collector for Farm Merger Pro - Click items to capture them."""

import os
import tkinter as tk
from tkinter import ttk
from pynput import mouse
from pyautogui_safe import pyautogui
from PIL import Image, ImageTk
import time
import queue
import threading


class TemplateCollector:
    """
    Click-to-capture tool that mimics how existing templates were created.
    User clicks on an item in the game, tool auto-crops a square around it.
    """
    
    def __init__(self, category="items", crop_size=50):
        """
        Args:
            category: Subfolder in img/ to save templates
            crop_size: Size of square crop around click point (default 50px)
        """
        self.category = category
        self.crop_size = crop_size
        self.save_path = os.path.join("img", category)
        os.makedirs(self.save_path, exist_ok=True)
        
        self.root = None
        self.canvas = None
        self.listener = None
        self.click_count = 0
        self.instructions = None
        self.click_queue = queue.Queue()
        self.preview_label = None
        self.captured_templates = []  # Track what was captured
        self.dialog_assets = []  # Keep references alive for PhotoImage objects
        
    def start_capture_mode(self):
        """Launch transparent overlay - user clicks items to capture them"""
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.3)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instructions = (
            f"TEMPLATE COLLECTOR - {self.category}\n\n"
            f"Click on items to capture them as templates\n"
            f"Crop size: {self.crop_size}x{self.crop_size} pixels\n\n"
            f"Controls:\n"
            f"  Left Click = Capture template\n"
            f"  Right Click = Exit collector\n"
            f"  ESC = Exit collector"
        )
        
        self.instructions = self.canvas.create_text(
            screen_width // 2, 80,
            text=instructions,
            font=("Arial", 20, "bold"),
            fill="white",
            justify="center"
        )
        
        # Preview area for showing what was captured
        self.preview_label = tk.Label(self.root, bg="black", fg="white")
        self.preview_label.place(x=screen_width - 250, y=20)
        
        # ESC key to exit
        self.root.bind("<Escape>", lambda e: self.cleanup())
        
        # Mouse listener for clicks
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()
        
        # Process click queue
        self.process_click_queue()
        
        self.root.mainloop()
    
    def on_click(self, x, y, button, pressed):
        """Handle mouse clicks - capture or exit"""
        if not pressed:
            return
        
        if button == mouse.Button.right:
            # Right click = exit
            self.root.after(0, self.cleanup)
            return
        
        if button == mouse.Button.left:
            # Left click = capture template - add to queue for main thread processing
            self.click_queue.put((x, y))
    
    def process_click_queue(self):
        """Process clicks from the queue in the main thread"""
        # Safety check: ensure window still exists
        if not self.root or not self.root.winfo_exists():
            return
            
        try:
            while not self.click_queue.empty():
                x, y = self.click_queue.get_nowait()
                self.capture_at_position(x, y)
        except queue.Empty:
            pass
        
        # Schedule next check
        if self.root:
            self.root.after(100, self.process_click_queue)
    
    def capture_at_position(self, x, y):
        """Capture a square crop around the clicked position"""
        # Calculate crop boundaries (centered on click)
        half_size = self.crop_size // 2
        
        left = x - half_size
        top = y - half_size
        
        # Take screenshot of the crop area
        try:
            screenshot = pyautogui.screenshot(region=(left, top, self.crop_size, self.crop_size))
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return
        
        # Show visual feedback on canvas
        self.show_capture_feedback(x, y)
        
        # Show preview of what was captured
        self.show_preview(screenshot)
        
        # Prompt for template name using enhanced dialog
        self.root.withdraw()
        dialog_result = self.prompt_template_name(screenshot)
        
        # Safety check before deiconify
        if self.root and self.root.winfo_exists():
            self.root.deiconify()
        else:
            return  # Window was closed, abort capture
        
        if dialog_result.get("cancelled"):
            self.update_instructions("Cancelled - exiting collector")
            self.cleanup()
            return
        
        name = dialog_result.get("name")
        
        if name and name.strip():
            # Clean the name (remove spaces, special chars)
            name = name.strip().replace(" ", "_").lower()
            if not name.endswith(".png"):
                name += ".png"
            
            # Save the template
            filepath = os.path.join(self.save_path, name)
            screenshot.save(filepath)
            
            self.click_count += 1
            self.captured_templates.append({"name": name, "path": filepath, "image": screenshot})
            
            print(f"? Saved: {filepath}")
            
            # Update instructions with success message and show suggestion
            suggestion = self.get_suggestion()
            self.update_instructions(f"? Saved: {name}\n{self.click_count} templates captured\n\n{suggestion}")
        else:
            self.update_instructions("Awaiting next capture... Left click an item or press ESC to exit.")

    def list_existing_templates(self, limit=60):
        """Return existing template filenames for the current category."""
        try:
            names = [
                name
                for name in os.listdir(self.save_path)
                if name.lower().endswith(".png")
            ]
        except FileNotFoundError:
            return []

        names.sort(key=str.lower)
        return names[:limit]

    def build_name_suggestions(self, existing_names):
        """Generate auto-complete suggestions based on existing templates."""
        suggestions = []
        next_index = len(existing_names) + 1
        default_name = f"{self.category}_{next_index}"
        suggestions.append(default_name)

        bases = []
        for name in existing_names:
            base = os.path.splitext(name)[0]
            if base not in bases:
                bases.append(base)

        for base in bases:
            if base not in suggestions:
                suggestions.append(base)
            candidate = f"{base}_{next_index}"
            if candidate not in suggestions:
                suggestions.append(candidate)

        generic = [
            f"{self.category}_template",
            f"{self.category}_item",
            f"{self.category}_{time.strftime('%H%M')}",
        ]
        for candidate in generic:
            if candidate not in suggestions:
                suggestions.append(candidate)

        filtered = []
        seen = set()
        for name in suggestions:
            if name and name not in seen:
                filtered.append(name)
                seen.add(name)

        return filtered[:16]

    def prompt_template_name(self, screenshot):
        """Display a modern dialog prompting for the template name."""
        result = {"name": None, "cancelled": False}
        self.dialog_assets = []

        dialog = tk.Toplevel(self.root)
        dialog.title("Save Template")
        dialog.configure(bg="#10121C")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        dialog.transient(self.root)

        style = ttk.Style(dialog)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Glass.TFrame", background="#10121C")
        style.configure("Glass.TLabel", background="#10121C", foreground="#E5ECFF")
        style.configure("GlassMuted.TLabel", background="#10121C", foreground="#9AA2B5")
        style.configure("GlassAccent.TLabel", background="#10121C", foreground="#58B2FF")
        style.configure("GlassDanger.TLabel", background="#10121C", foreground="#FF5A5F")
        style.configure("GlassSuccess.TLabel", background="#10121C", foreground="#4CD964")
        style.configure("Glass.TButton", padding=6)

        container = ttk.Frame(dialog, style="Glass.TFrame", padding=18)
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(7, weight=1)

        ttk.Label(
            container,
            text=f"Saved to img/{self.category}/",
            style="GlassMuted.TLabel",
            font=("Segoe UI", 11),
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(
            container,
            text="New capture",
            style="GlassAccent.TLabel",
            font=("Segoe UI Semibold", 12),
        ).grid(row=1, column=0, sticky="w", pady=(12, 4))

        preview_frame = ttk.Frame(container, style="Glass.TFrame")
        preview_frame.grid(row=2, column=0, sticky="w")

        capture_preview = screenshot.copy()
        capture_preview.thumbnail((160, 160), Image.Resampling.LANCZOS)
        capture_photo = ImageTk.PhotoImage(capture_preview)
        self.dialog_assets.append(capture_photo)

        tk.Label(
            preview_frame,
            image=capture_photo,
            bg="#10121C",
        ).pack(anchor="w")

        ttk.Label(
            container,
            text="Template name",
            style="GlassAccent.TLabel",
            font=("Segoe UI Semibold", 12),
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(18, 4))

        name_var = tk.StringVar()
        name_entry = ttk.Entry(container, textvariable=name_var, font=("Segoe UI", 12), width=36)
        name_entry.grid(row=4, column=0, columnspan=2, sticky="we")
        name_entry.focus_set()

        status_label = ttk.Label(
            container,
            text="Tip: Use arrow keys to browse suggestions or double-click an existing template.",
            style="GlassMuted.TLabel",
            font=("Segoe UI", 10),
        )
        status_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(4, 8))

        ttk.Label(
            container,
            text="Suggestions",
            style="GlassAccent.TLabel",
            font=("Segoe UI Semibold", 12),
        ).grid(row=6, column=0, sticky="w")

        suggestions = self.build_name_suggestions(self.list_existing_templates())
        
        # Auto-select the first (best) suggestion
        default_name = suggestions[0] if suggestions else f"{self.category}_1"
        name_var.set(default_name)
        
        suggestion_list = tk.Listbox(
            container,
            height=6,
            activestyle="none",
            bg="#151C2E",
            fg="#E5ECFF",
            highlightthickness=0,
            relief="flat",
            selectbackground="#58B2FF",
        )
        suggestion_list.grid(row=7, column=0, sticky="nsew", pady=(4, 0))
        for item in suggestions:
            suggestion_list.insert(tk.END, item)
        
        # Select first item by default
        if suggestions:
            suggestion_list.selection_set(0)
            suggestion_list.see(0)

        ttk.Label(
            container,
            text="Existing templates",
            style="GlassAccent.TLabel",
            font=("Segoe UI Semibold", 12),
        ).grid(row=6, column=1, sticky="w")

        existing_list = tk.Listbox(
            container,
            height=6,
            activestyle="none",
            bg="#151C2E",
            fg="#E5ECFF",
            highlightthickness=0,
            relief="flat",
            selectbackground="#A05AFF",
        )
        existing_list.grid(row=7, column=1, sticky="nsew", pady=(4, 0))

        existing_previews = {}
        existing_names = self.list_existing_templates(limit=60)
        for name in existing_names:
            existing_list.insert(tk.END, name)
            path = os.path.join(self.save_path, name)
            try:
                with Image.open(path) as img:
                    thumb = img.copy()
                thumb.thumbnail((120, 120), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(thumb)
                self.dialog_assets.append(photo)
                existing_previews[name] = photo
            except Exception:
                continue

        preview_caption = ttk.Label(
            container,
            text="Existing preview",
            style="GlassMuted.TLabel",
            font=("Segoe UI", 10),
        )
        preview_caption.grid(row=8, column=1, sticky="w", pady=(12, 4))

        existing_preview_label = tk.Label(container, bg="#10121C")
        existing_preview_label.grid(row=9, column=1, sticky="w")

        def apply_suggestion(index):
            if 0 <= index < suggestion_list.size():
                selection = suggestion_list.get(index)
                name_var.set(selection)
                name_entry.icursor(tk.END)
                status_label.config(
                    text="Suggestion applied. Press Enter to save.",
                    style="GlassSuccess.TLabel",
                )

        def on_suggestion_select(_event=None):
            selection = suggestion_list.curselection()
            if selection:
                apply_suggestion(selection[0])

        def on_existing_select(_event=None):
            selection = existing_list.curselection()
            if not selection:
                return
            chosen = existing_list.get(selection[0])
            base = os.path.splitext(chosen)[0]
            name_var.set(base)
            name_entry.icursor(tk.END)
            preview = existing_previews.get(chosen)
            if preview:
                existing_preview_label.configure(image=preview)
                existing_preview_label.image = preview
            status_label.config(
                text="Existing template selected as base.",
                style="GlassSuccess.TLabel",
            )

        suggestion_list.bind("<<ListboxSelect>>", on_suggestion_select)
        existing_list.bind("<<ListboxSelect>>", on_existing_select)

        def focus_suggestions(_event=None):
            if suggestion_list.size():
                suggestion_list.focus_set()
                suggestion_list.selection_clear(0, tk.END)
                suggestion_list.selection_set(0)
                suggestion_list.activate(0)
                apply_suggestion(0)
            return "break"

        name_entry.bind("<Down>", focus_suggestions)

        def suggestion_navigation(event):
            key = event.keysym
            cur = suggestion_list.curselection()
            if not cur:
                return
            index = cur[0]
            if key == "Up" and index > 0:
                suggestion_list.selection_clear(0, tk.END)
                suggestion_list.selection_set(index - 1)
                suggestion_list.activate(index - 1)
                apply_suggestion(index - 1)
            elif key == "Down" and index < suggestion_list.size() - 1:
                suggestion_list.selection_clear(0, tk.END)
                suggestion_list.selection_set(index + 1)
                suggestion_list.activate(index + 1)
                apply_suggestion(index + 1)
            return "break"

        suggestion_list.bind("<Up>", suggestion_navigation)
        suggestion_list.bind("<Down>", suggestion_navigation)

        def on_save(_event=None):
            entered = name_var.get().strip()
            if not entered:
                # If empty, use the first suggestion as fallback
                if suggestions:
                    entered = suggestions[0]
                else:
                    entered = default_name
            
            result["name"] = entered
            dialog.destroy()

        def on_cancel(_event=None):
            result["cancelled"] = True
            dialog.destroy()

        suggestion_list.bind("<Return>", on_save)
        existing_list.bind("<Return>", on_save)
        existing_list.bind("<Escape>", on_cancel)

        def on_existing_double(_event=None):
            on_existing_select()
            on_save()

        suggestion_list.bind("<Double-Button-1>", on_save)
        existing_list.bind("<Double-Button-1>", on_existing_double)

        button_row = ttk.Frame(container, style="Glass.TFrame")
        button_row.grid(row=10, column=0, columnspan=2, sticky="e", pady=(20, 0))

        ttk.Button(
            button_row,
            text="Cancel",
            command=on_cancel,
            style="Glass.TButton",
        ).pack(side="right", padx=(8, 0))

        ttk.Button(
            button_row,
            text="Save",
            command=on_save,
            style="Glass.TButton",
        ).pack(side="right")

        dialog.bind("<Escape>", on_cancel)
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)

        dialog.update_idletasks()
        width, height = 580, 500
        x = (dialog.winfo_screenwidth() - width) // 2
        y = (dialog.winfo_screenheight() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        dialog.wait_window()
        return result

    def show_capture_feedback(self, x, y):
        """Draw a box showing what was captured"""
        half_size = self.crop_size // 2
        
        # Draw rectangle around captured area
        rect = self.canvas.create_rectangle(
            x - half_size, y - half_size,
            x + half_size, y + half_size,
            outline="green", width=3
        )
        
        # Remove after 500ms
        self.root.after(500, lambda: self.canvas.delete(rect))
    
    def show_preview(self, screenshot):
        """Show a preview of the captured image"""
        try:
            # Resize for preview (max 200x200)
            preview_size = 200
            img = screenshot.copy()
            img.thumbnail((preview_size, preview_size), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update preview label
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error showing preview: {e}")
    
    def get_suggestion(self):
        """Get a suggestion for what to capture next"""
        suggestions = {
            "items": [
                "?? Suggestion: Capture different tiers of the same item (cow1, cow2, cow3)",
                "?? Suggestion: Capture items in 'ready' state with sparkles/goods visible",
                "?? Suggestion: Try capturing higher-tier merged items for better detection",
                "?? Suggestion: Capture items at the same zoom level for consistency"
            ],
            "ui_elements": [
                "?? Suggestion: Capture the 'close' button (X) from popups",
                "?? Suggestion: Capture 'OK' and 'Claim' buttons",
                "?? Suggestion: Capture the energy icon and coin icon",
                "?? Suggestion: Capture repair and expand buttons"
            ],
            "producers": [
                "?? Suggestion: Make sure the producer has goods ready (sparkles visible)",
                "?? Suggestion: Capture all producer types: cow, chicken, pig, sheep, wheat, corn",
                "?? Suggestion: Capture producers at the same level for consistency"
            ],
            "orders": [
                "?? Suggestion: Capture individual order items from the order board",
                "?? Suggestion: Capture the coin reward indicator",
                "?? Suggestion: Capture order completion checkmarks"
            ]
        }
        
        category_suggestions = suggestions.get(self.category, [
            "?? Suggestion: Keep capturing similar items for better coverage",
            "?? Suggestion: Try different variations of the same element"
        ])
        
        import random
        return random.choice(category_suggestions)
    
    def update_instructions(self, additional_text):
        """Update instruction text with status message"""
        screen_width = self.root.winfo_screenwidth()
        
        instructions = (
            f"TEMPLATE COLLECTOR - {self.category}\n\n"
            f"Click on items to capture them as templates\n"
            f"Crop size: {self.crop_size}x{self.crop_size} pixels\n\n"
            f"{additional_text}\n\n"
            f"Left Click = Capture | Right Click = Exit | ESC = Exit"
        )
        
        self.canvas.itemconfig(self.instructions, text=instructions)
    
    def cleanup(self):
        """Stop listener and close window"""
        if self.listener:
            self.listener.stop()
        if self.root:
            self.root.quit()
            self.root.destroy()
        
        print(f"\n{'='*60}")
        print(f"TEMPLATE COLLECTOR - SESSION SUMMARY")
        print(f"{'='*60}")
        print(f"Total captured: {self.click_count} templates")
        print(f"Saved to: {self.save_path}\n")
        
        if self.captured_templates:
            print("Captured templates:")
            for i, template in enumerate(self.captured_templates, 1):
                print(f"  {i}. {template['name']} ? {template['path']}")
            print()
        
        print("?? Next steps:")
        print("  1. Test templates in the Detection tab")
        print("  2. Adjust threshold if needed (0.70-0.85)")
        print("  3. Capture more variations if detection fails")
        print(f"{'='*60}\n")


class BatchTemplateCollector:
    """Helper to collect multiple templates in sequence with prompts"""
    
    def __init__(self, category="items", crop_size=50):
        self.category = category
        self.crop_size = crop_size
    
    def collect_checklist(self, items_needed):
        """
        Collect templates from a checklist.
        
        Args:
            items_needed: List of item names to collect
            
        Example:
            collector.collect_checklist([
                "cow1", "cow2", "cow3",
                "chicken1", "chicken2", "chicken3"
            ])
        """
        print(f"\n{'='*60}")
        print(f"BATCH TEMPLATE COLLECTION - {self.category}")
        print(f"{'='*60}\n")
        print(f"You will capture {len(items_needed)} templates.")
        print(f"Each time, click on the item when prompted.\n")
        
        for idx, item_name in enumerate(items_needed, 1):
            print(f"\n[{idx}/{len(items_needed)}] Next: {item_name}")
            input(f"    Press ENTER when ready to capture '{item_name}'...")
            
            collector = TemplateCollector(self.category, self.crop_size)
            collector.start_capture_mode()
            
            # After collector closes, continue to next
            print(f"    ? Captured {item_name}")
        
        print(f"\n{'='*60}")
        print(f"? All {len(items_needed)} templates collected!")
        print(f"{'='*60}\n")


def collect_game_items(crop_size=50):
    """Collect game item templates (animals, crops) - matches existing style"""
    items_needed = [
        # Tier 1 items (if missing)
        "cow1", "chicken1", "pig1", "sheep1", "goat1",
        "wheat1", "corn1", "carrot1", "soybean1", "sunflower1", "sugar1",
        
        # Ready state items (with goods/sparkles)
        "cow1_ready", "chicken1_ready", "pig1_ready",
        
        # Higher tiers if needed
        "cow4", "chicken4", "wheat4"
    ]
    
    collector = BatchTemplateCollector("items", crop_size)
    
    print("\nThis will help you collect game item templates.")
    print("Position your game window so items are visible.")
    print("You'll click on each item when prompted.\n")
    
    choice = input("Start batch collection? (y/n): ").lower()
    if choice == 'y':
        collector.collect_checklist(items_needed)
    else:
        # Free-form collection
        print("\nFree-form mode: Click any items you want to capture.")
        print("Right-click or press ESC when done.\n")
        input("Press ENTER to start...")
        
        tc = TemplateCollector("items", crop_size)
        tc.start_capture_mode()


def collect_ui_elements(crop_size=60):
    """Collect UI button templates (larger items)"""
    ui_elements = [
        "claim_button",
        "close_button",
        "ok_button",
        "collect_button",
        "expand_button",
        "repair_button",
        "energy_icon",
        "coin_icon"
    ]
    
    collector = BatchTemplateCollector("ui_elements", crop_size)
    
    print("\nThis will help you collect UI element templates.")
    print("Position your game so UI buttons are visible.\n")
    
    choice = input("Start UI collection? (y/n): ").lower()
    if choice == 'y':
        collector.collect_checklist(ui_elements)
    else:
        print("\nFree-form mode: Click any UI elements you want.\n")
        input("Press ENTER to start...")
        
        tc = TemplateCollector("ui_elements", crop_size)
        tc.start_capture_mode()


def collect_producers_ready(crop_size=50):
    """Collect templates for producers in 'ready to collect' state"""
    producers = [
        "cow_ready",
        "chicken_ready", 
        "pig_ready",
        "sheep_ready",
        "goat_ready",
        "wheat_ready",
        "corn_ready"
    ]
    
    os.makedirs("img/producers", exist_ok=True)
    
    collector = BatchTemplateCollector("producers", crop_size)
    
    print("\nCollect producers showing 'ready' indicators (sparkles/goods).")
    print("Make sure items have goods ready before capturing!\n")
    
    choice = input("Start producer collection? (y/n): ").lower()
    if choice == 'y':
        collector.collect_checklist(producers)
    else:
        print("\nFree-form mode.\n")
        input("Press ENTER to start...")
        
        tc = TemplateCollector("producers", crop_size)
        tc.start_capture_mode()


if __name__ == "__main__":
    print("="*60)
    print("FARM MERGER PRO - TEMPLATE COLLECTOR")
    print("="*60)
    print("\nWhat do you want to collect?\n")
    print("1. Game Items (animals, crops) - 50x50px")
    print("2. UI Elements (buttons, icons) - 60x60px")
    print("3. Producers (ready state) - 50x50px")
    print("4. Custom (specify category and size)")
    print("5. Free Mode (just click and capture)")
    print()
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        collect_game_items(crop_size=50)
    elif choice == "2":
        collect_ui_elements(crop_size=60)
    elif choice == "3":
        collect_producers_ready(crop_size=50)
    elif choice == "4":
        category = input("Category name (e.g., orders, popups): ").strip()
        size = int(input("Crop size in pixels (e.g., 50): ").strip())
        
        tc = TemplateCollector(category, size)
        tc.start_capture_mode()
    elif choice == "5":
        size = int(input("Crop size in pixels (default 50): ").strip() or "50")
        
        tc = TemplateCollector("items", size)
        tc.start_capture_mode()
    else:
        print("Invalid choice")



