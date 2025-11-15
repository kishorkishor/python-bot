"""Unified GUI Integration - Automation & Testing

Adds Automation and Tests tabs directly to gui_flet.py
Everything in one intuitive interface!
"""

import flet as ft
import threading
import time
import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Detection overlay import
try:
    from detection_overlay import get_overlay
    OVERLAY_AVAILABLE = True
except ImportError:
    OVERLAY_AVAILABLE = False
    get_overlay = None

# Try to import automation
try:
    from automation_orchestrator import AutomationOrchestrator
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False
    AutomationOrchestrator = None

# Color constants (matching gui_flet.py)
ACCENT_BLUE = "#58B2FF"
SUCCESS_GREEN = "#4CD964"
WARNING_ORANGE = "#FFB800"
DANGER_RED = "#FF5A5F"
TEXT_PRIMARY = "#FFFFFF"
TEXT_MUTED = "#B4BED2"
TEXT_SUBTLE = "#828CA0"
GLASS_BG = "rgba(52, 58, 82, 0.4)"
GLASS_BORDER = "rgba(160, 200, 255, 0.3)"
PURPLE = "#A05AFF"


def hex_with_opacity(color, opacity):
    """Convert hex color to rgba with opacity."""
    if color.startswith("#"):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        return f"rgba({r}, {g}, {b}, {opacity})"
    return color


def create_glass_card(content, padding=16, margin=None):
    """Create a glassmorphism card."""
    return ft.Container(
        content=content,
        padding=padding,
        margin=margin or ft.margin.all(0),
        bgcolor=hex_with_opacity("#FFFFFF", 0.1),
        border=ft.border.all(1, GLASS_BORDER),
        border_radius=12,
    )


def create_glass_button(text, on_click=None, width=None, height=50, color=ACCENT_BLUE, icon=None):
    """Create a glassmorphism button."""
    button_content = []
    if icon:
        button_content.append(ft.Icon(icon, color=color, size=20))
    button_content.append(ft.Text(text, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600))
    
    return ft.ElevatedButton(
        content=ft.Row(button_content, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        on_click=on_click,
        width=width,
        height=height,
        bgcolor=hex_with_opacity(color, 0.3),
        color=color,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )


def create_automation_tab(page, orchestrator, status_ref, log_callback, area_getter, config_getter):
    """Create Automation tab content."""
    
    # UI References
    automation_status_ref = ft.Ref[ft.Text]()
    automation_stats_ref = ft.Ref[ft.Column]()
    auto_refresh_enabled = [False]
    
    # Switches
    collect_resources_switch = ft.Ref[ft.Switch]()
    fulfill_orders_switch = ft.Ref[ft.Switch]()
    handle_popups_switch = ft.Ref[ft.Switch]()
    auto_merge_switch = ft.Ref[ft.Switch]()
    expand_land_switch = ft.Ref[ft.Switch]()
    repair_buildings_switch = ft.Ref[ft.Switch]()
    
    def update_status(status, color=ACCENT_BLUE):
        try:
            if automation_status_ref.current:
                automation_status_ref.current.value = status
                automation_status_ref.current.color = color
                try:
                    page.update()
                except:
                    pass  # Page might not be ready
        except Exception as e:
            log_message(f"Error updating status: {e}", "error")
    
    def log_message(msg, level="info"):
        if log_callback:
            log_callback(msg, level)
    
    def update_statistics():
        if not automation_stats_ref.current or not orchestrator:
            return
        
        stats = orchestrator.get_statistics()
        stats_text = [
            f"Runtime: {int(stats.get('runtime', 0))}s",
            f"Actions: {stats.get('actions_executed', 0)}",
            f"Errors: {stats.get('errors', 0)}",
            f"Last Action: {stats.get('last_action', 'None')}",
        ]
        
        if 'collector' in stats:
            collector_stats = stats['collector']
            stats_text.append(f"Collections: {collector_stats.get('total_collections', 0)}")
        
        if 'order_manager' in stats:
            order_stats = stats['order_manager']
            stats_text.append(f"Orders: {order_stats.get('fulfilled_orders', 0)}")
            stats_text.append(f"Coins: {order_stats.get('total_coins_earned', 0)}")
        
        if 'energy_manager' in stats:
            energy_stats = stats['energy_manager']
            energy = energy_stats.get('current_energy', 'N/A')
            stats_text.append(f"Energy: {energy}")
        
        try:
            if automation_stats_ref.current:
                automation_stats_ref.current.controls = [
                    ft.Text(line, size=12, color=TEXT_MUTED) for line in stats_text
                ]
                try:
                    page.update()
                except:
                    pass  # Page might not be ready
        except Exception as e:
            log_message(f"Error updating statistics: {e}", "error")
    
    def start_automation(e):
        if not orchestrator:
            log_message("Automation not available", "error")
            return
        
        game_area = area_getter()
        if not game_area:
            log_message("Please configure screen area first!", "error")
            return
        
        config = config_getter()
        regions = config.get('regions', {})
        
        orchestrator.set_game_regions(
            game_area=game_area,
            order_board_region=regions.get('order_board'),
            energy_region=regions.get('energy_display'),
            coin_region=regions.get('coin_display')
        )
        
        automation_config = {
            'automation': {
                'collect_resources': collect_resources_switch.current.value if collect_resources_switch.current else True,
                'fulfill_orders': fulfill_orders_switch.current.value if fulfill_orders_switch.current else True,
                'handle_popups': handle_popups_switch.current.value if handle_popups_switch.current else True,
                'auto_merge': auto_merge_switch.current.value if auto_merge_switch.current else True,
                'expand_land': expand_land_switch.current.value if expand_land_switch.current else False,
                'repair_buildings': repair_buildings_switch.current.value if repair_buildings_switch.current else False,
            }
        }
        orchestrator.update_config(automation_config)
        
        if orchestrator.start():
            update_status("Running", SUCCESS_GREEN)
            log_message("Automation started!", "success")
        else:
            update_status("Failed", DANGER_RED)
            log_message("Failed to start automation", "error")
    
    def stop_automation(e):
        if orchestrator:
            orchestrator.stop()
            update_status("Stopped", TEXT_MUTED)
            log_message("Automation stopped", "info")
    
    def pause_automation(e):
        if orchestrator:
            orchestrator.pause()
            update_status("Paused", WARNING_ORANGE)
            log_message("Automation paused", "info")
    
    def resume_automation(e):
        if orchestrator:
            orchestrator.resume()
            update_status("Running", SUCCESS_GREEN)
            log_message("Automation resumed", "info")
    
    def toggle_auto_refresh(e):
        auto_refresh_enabled[0] = e.control.value
        if auto_refresh_enabled[0]:
            def auto_refresh_loop():
                while auto_refresh_enabled[0]:
                    if orchestrator and orchestrator.is_running:
                        update_statistics()
                    time.sleep(5)
            threading.Thread(target=auto_refresh_loop, daemon=True).start()
            log_message("Auto-refresh enabled", "info")
        else:
            log_message("Auto-refresh disabled", "info")
    
    # Create status column first
    status_column = ft.Column(
        controls=[
            ft.Text("Status", size=16, weight=ft.FontWeight.W_600, color=ACCENT_BLUE),
            ft.Text("Stopped", size=18, color=SUCCESS_GREEN, ref=automation_status_ref, weight=ft.FontWeight.W_600),
        ],
        spacing=8,
        tight=False,
    )
    
    return ft.Container(
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Automation Control", size=24, weight=ft.FontWeight.W_700, color=PURPLE),
                ft.Text("Full automation system", size=12, color=TEXT_MUTED),
                ft.Divider(height=1, color=GLASS_BORDER),
                ft.Container(height=16),
                
                create_glass_card(status_column),
                ft.Container(height=12),
                
                ft.Row(
                    controls=[
                        create_glass_button("▶ Start", on_click=start_automation, color=SUCCESS_GREEN, icon=ft.Icons.PLAY_ARROW),
                        create_glass_button("⏸ Pause", on_click=pause_automation, color=WARNING_ORANGE, icon=ft.Icons.PAUSE),
                        create_glass_button("▶ Resume", on_click=resume_automation, color=SUCCESS_GREEN, icon=ft.Icons.PLAY_ARROW),
                        create_glass_button("⏹ Stop", on_click=stop_automation, color=DANGER_RED, icon=ft.Icons.STOP),
                    ],
                    spacing=12,
                ),
                ft.Container(height=24),
                
                ft.Text("Features", size=18, weight=ft.FontWeight.W_600, color=PURPLE),
                ft.Container(height=8),
                create_glass_card(
                    ft.Column(
                        controls=[
                            ft.Switch(label="Collect Resources", value=True, ref=collect_resources_switch, label_style=ft.TextStyle(color=TEXT_PRIMARY)),
                            ft.Switch(label="Fulfill Orders", value=True, ref=fulfill_orders_switch, label_style=ft.TextStyle(color=TEXT_PRIMARY)),
                            ft.Switch(label="Handle Popups", value=True, ref=handle_popups_switch, label_style=ft.TextStyle(color=TEXT_PRIMARY)),
                            ft.Switch(label="Auto Merge", value=True, ref=auto_merge_switch, label_style=ft.TextStyle(color=TEXT_PRIMARY)),
                            ft.Switch(label="Expand Land", value=False, ref=expand_land_switch, label_style=ft.TextStyle(color=TEXT_PRIMARY)),
                            ft.Switch(label="Repair Buildings", value=False, ref=repair_buildings_switch, label_style=ft.TextStyle(color=TEXT_PRIMARY)),
                        ],
                        spacing=12,
                    ),
                ),
                ft.Container(height=24),
                
                ft.Text("Statistics", size=18, weight=ft.FontWeight.W_600, color=PURPLE),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Column(
                        ref=automation_stats_ref,
                        controls=[ft.Text("No data yet", size=12, color=TEXT_MUTED)],
                        spacing=8,
                        tight=False,
                    ),
                    padding=16,
                    bgcolor=hex_with_opacity("#FFFFFF", 0.1),
                    border=ft.border.all(1, GLASS_BORDER),
                    border_radius=12,
                ),
                ft.Container(height=12),
                create_glass_button("Refresh Statistics", on_click=lambda e: update_statistics(), width=None, color=ACCENT_BLUE),
                ft.Switch(label="Auto-refresh (every 5s)", value=False, on_change=toggle_auto_refresh, label_style=ft.TextStyle(color=TEXT_PRIMARY)),
            ],
            spacing=12,
        ),
        padding=20,
        visible=False,
        expand=True,
    )


def create_tests_tab(page, log_callback):
    """Create Tests tab content."""
    
    # Get test directory - try multiple possible locations
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try different possible paths
    possible_paths = [
        os.path.join(current_file_dir, 'test_agents'),  # Same dir as this file
        os.path.join(os.path.dirname(current_file_dir), 'test_agents'),  # Parent dir
        os.path.join(current_file_dir, 'da bot', 'test_agents'),  # Nested
        'test_agents',  # Current working directory
    ]
    
    test_dir = None
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and os.path.isdir(abs_path):
            test_dir = abs_path
            break
    
    if not test_dir:
        # Default to same directory as this file
        test_dir = os.path.join(current_file_dir, 'test_agents')
        # Create it if it doesn't exist
        os.makedirs(test_dir, exist_ok=True)
    else:
        test_dir = os.path.abspath(test_dir)
    
    results_dir = os.path.join(test_dir, 'results')
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    
    # Log the resolved path
    if log_callback:
        log_callback(f"[info] Test directory: {test_dir}", "info")
        if os.path.exists(test_dir):
            files = [f for f in os.listdir(test_dir) if f.endswith('.py')]
            log_callback(f"[info] Found {len(files)} test files", "info")
    
    # UI References
    test_status_ref = ft.Ref[ft.Text]()
    test_output_ref = ft.Ref[ft.Column]()
    results_list_ref = ft.Ref[ft.Column]()
    progress_text_ref = ft.Ref[ft.Text]()
    is_running = [False]
    error_buffer = []
    
    available_tests = {
        "Basic Merging": "test_basic_merging.py",
        "Resource Collection": "test_resource_collection.py",
        "Order Fulfillment": "test_order_fulfillment.py",
        "State Machine": "test_state_machine.py",
        "GUI Integration": "test_gui_integration.py",
        "Flet Automation": "test_flet_automation.py",
    }
    
    def log_message(msg, level="info"):
        if log_callback:
            log_callback(msg, level)
    
    def update_status(status, color=ACCENT_BLUE):
        try:
            if test_status_ref.current:
                test_status_ref.current.value = status
                test_status_ref.current.color = color
                try:
                    page.update()
                except:
                    pass  # Page might not be ready
        except Exception as e:
            log_message(f"Error updating status: {e}", "error")
    
    def add_output(text, color=TEXT_PRIMARY):
        try:
            if test_output_ref.current:
                test_output_ref.current.controls.append(ft.Text(text, size=11, color=color, selectable=True))
                if color == DANGER_RED:
                    error_buffer.append(text.rstrip())
                try:
                    page.update()
                except:
                    pass  # Page might not be ready
        except Exception as e:
            log_message(f"Error adding output: {e}", "error")
    
    def clear_output():
        try:
            if test_output_ref.current:
                test_output_ref.current.controls.clear()
                error_buffer.clear()
                try:
                    page.update()
                except:
                    pass  # Page might not be ready
        except Exception as e:
            log_message(f"Error clearing output: {e}", "error")
    
    def copy_error_output(e=None):
        if not error_buffer:
            update_status("No errors to copy", WARNING_ORANGE)
            log_message("No test errors available to copy", "warning")
            return
        
        payload = "\n".join(error_buffer).strip()
        if not payload:
            update_status("No errors to copy", WARNING_ORANGE)
            log_message("Error log was empty", "warning")
            return
        
        try:
            if hasattr(page, "set_clipboard"):
                page.set_clipboard(payload)
                update_status("Errors copied to clipboard", SUCCESS_GREEN)
                log_message("Copied failing test output to clipboard", "success")
            else:
                log_message("Clipboard not available on this page", "warning")
        except Exception as exc:
            log_message(f"Failed to copy errors: {exc}", "error")
            update_status("Copy failed", DANGER_RED)
    
    def run_test(test_name):
        if is_running[0]:
            return
        
        test_file = available_tests.get(test_name)
        if not test_file:
            log_message(f"Unknown test: {test_name}", "error")
            return
        
        test_path = os.path.join(test_dir, test_file)
        if not os.path.exists(test_path):
            log_message(f"Test file not found: {test_path}", "error")
            log_message(f"Looking in: {test_dir}", "info")
            log_message(f"Available files: {os.listdir(test_dir) if os.path.exists(test_dir) else 'Directory does not exist'}", "info")
            return
        
        def run():
            is_running[0] = True
            update_status(f"Running: {test_name}...", WARNING_ORANGE)
            clear_output()
            add_output(f"Starting test: {test_name}\n", ACCENT_BLUE)
            
            try:
                # Use absolute path and ensure we're in the right directory
                abs_test_path = os.path.abspath(test_path)
                abs_test_dir = os.path.abspath(test_dir)
                
                if not os.path.exists(abs_test_path):
                    add_output(f"ERROR: Test file not found: {abs_test_path}\n", DANGER_RED)
                    add_output(f"Test directory: {abs_test_dir}\n", DANGER_RED)
                    if os.path.exists(abs_test_dir):
                        add_output(f"Files in directory: {', '.join(os.listdir(abs_test_dir))}\n", DANGER_RED)
                    update_status(f"✗ {test_name} - FILE NOT FOUND", DANGER_RED)
                    is_running[0] = False
                    return
                
                result = subprocess.run(
                    [sys.executable, abs_test_path],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=abs_test_dir
                )
                
                if result.stdout:
                    add_output("\n--- OUTPUT ---\n", TEXT_SUBTLE)
                    add_output(result.stdout, TEXT_PRIMARY)
                
                if result.stderr:
                    add_output("\n--- ERRORS ---\n", TEXT_SUBTLE)
                    add_output(result.stderr, DANGER_RED)
                
                if result.returncode == 0:
                    update_status(f"✓ {test_name} - PASSED", SUCCESS_GREEN)
                else:
                    update_status(f"✗ {test_name} - FAILED", DANGER_RED)
                
            except Exception as e:
                add_output(f"\nError: {e}\n", DANGER_RED)
                update_status(f"Error: {test_name}", DANGER_RED)
            
            is_running[0] = False
            refresh_results()
        
        threading.Thread(target=run, daemon=True).start()
    
    def run_all_tests():
        if is_running[0]:
            return
        
        def run():
            is_running[0] = True
            update_status("Running all tests...", WARNING_ORANGE)
            clear_output()
            add_output("Starting all tests...\n", ACCENT_BLUE)
            
            passed = 0
            failed = 0
            
            for test_name in available_tests.keys():
                add_output(f"\n{'='*50}\n", TEXT_SUBTLE)
                add_output(f"Running: {test_name}\n", ACCENT_BLUE)
                
                test_file = available_tests[test_name]
                test_path = os.path.join(test_dir, test_file)
                abs_test_path = os.path.abspath(test_path)
                abs_test_dir = os.path.abspath(test_dir)
                
                if not os.path.exists(abs_test_path):
                    add_output(f"ERROR: Test file not found: {abs_test_path}\n", DANGER_RED)
                    failed += 1
                    continue
                
                try:
                    result = subprocess.run(
                        [sys.executable, abs_test_path],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        cwd=abs_test_dir
                    )
                    
                    if result.returncode == 0:
                        passed += 1
                        add_output(f"✓ PASSED\n", SUCCESS_GREEN)
                    else:
                        failed += 1
                        add_output(f"✗ FAILED\n", DANGER_RED)
                        if result.stderr:
                            add_output(result.stderr[:500] + "\n", DANGER_RED)
                
                except Exception as e:
                    failed += 1
                    add_output(f"✗ ERROR: {e}\n", DANGER_RED)
            
            add_output(f"\n{'='*50}\n", TEXT_SUBTLE)
            add_output(f"Summary: {passed} passed, {failed} failed\n", SUCCESS_GREEN if failed == 0 else DANGER_RED)
            
            if failed == 0:
                update_status("✓ All tests passed!", SUCCESS_GREEN)
            else:
                update_status(f"✗ {failed} tests failed", DANGER_RED)
            
            is_running[0] = False
            refresh_results()
        
        threading.Thread(target=run, daemon=True).start()
    
    def refresh_results():
        """Refresh results list - only call after page is loaded."""
        try:
            # Check if ref is available and control exists
            if not hasattr(results_list_ref, 'current') or not results_list_ref.current:
                log_message("Results list not ready yet", "warning")
                return
            
            result_files = sorted(Path(results_dir).glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]
            
            new_controls = []
            
            if not result_files:
                new_controls.append(ft.Text("No results yet", size=12, color=TEXT_MUTED))
            else:
                for result_file in result_files:
                    try:
                        with open(result_file, 'r') as f:
                            data = json.load(f)
                            success = data.get('success', False)
                            test_name = data.get('test_name', 'Unknown')
                            timestamp = data.get('timestamp', '')
                            
                            color = SUCCESS_GREEN if success else DANGER_RED
                            icon = "✓" if success else "✗"
                            
                            new_controls.append(
                                create_glass_card(
                                    ft.Row(
                                        controls=[
                                            ft.Text(f"{icon} {test_name}", size=14, color=color, weight=ft.FontWeight.W_600),
                                            ft.Text(timestamp, size=10, color=TEXT_SUBTLE),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),
                                    padding=12,
                                )
                            )
                    except Exception as e:
                        log_message(f"Error loading result file: {e}", "error")
            
            # Safely update controls - use page.update() instead of control.update()
            try:
                if results_list_ref.current:
                    results_list_ref.current.controls = new_controls
                    # Don't call page.update() here - let the caller do it
                    if hasattr(page, 'update'):
                        try:
                            page.update()
                        except:
                            pass  # Page might not be ready yet
            except Exception as e:
                log_message(f"Error updating results list: {e}", "error")
        except Exception as e:
            log_message(f"Error refreshing results: {e}", "error")
    
    # Create status column first
    status_column = ft.Column(
        controls=[
            ft.Text("Status", size=16, weight=ft.FontWeight.W_600, color=ACCENT_BLUE),
            ft.Text("Ready", size=18, color=SUCCESS_GREEN, ref=test_status_ref, weight=ft.FontWeight.W_600),
            ft.Text("", size=12, color=TEXT_MUTED, ref=progress_text_ref),
        ],
        spacing=8,
        tight=False,
    )
    
    # Create output column
    output_column = ft.Column(
        ref=test_output_ref,
        controls=[ft.Text("No output yet. Run a test to see results.", size=12, color=TEXT_MUTED)],
        scroll=ft.ScrollMode.AUTO,
        height=200,
        tight=False,
    )
    
    # Create results column - initialize with empty state
    results_column = ft.Column(
        ref=results_list_ref,
        controls=[ft.Text("Click 'Refresh Results' to load", size=12, color=TEXT_MUTED)],
        spacing=8,
        tight=False,
    )
    
    return ft.Container(
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Test Runner", size=24, weight=ft.FontWeight.W_700, color=PURPLE),
                ft.Text("Run tests and view results", size=12, color=TEXT_MUTED),
                ft.Divider(height=1, color=GLASS_BORDER),
                ft.Container(height=16),
                
                create_glass_card(status_column),
                ft.Container(height=12),
                
                ft.Text("Run Tests", size=18, weight=ft.FontWeight.W_600, color=PURPLE),
                ft.Container(height=8),
                ft.Row(
                    controls=[
                        create_glass_button(
                            test_name,
                            on_click=lambda e, name=test_name: run_test(name) if not is_running[0] else None,
                            width=150,
                            color=ACCENT_BLUE,
                        )
                        for test_name in list(available_tests.keys())[:3]
                    ],
                    spacing=12,
                    wrap=True,
                ),
                ft.Container(height=8),
                ft.Row(
                    controls=[
                        create_glass_button(
                            test_name,
                            on_click=lambda e, name=test_name: run_test(name) if not is_running[0] else None,
                            width=150,
                            color=ACCENT_BLUE,
                        )
                        for test_name in list(available_tests.keys())[3:]
                    ],
                    spacing=12,
                    wrap=True,
                ),
                ft.Container(height=12),
                create_glass_button("▶ Run All Tests", on_click=lambda e: run_all_tests() if not is_running[0] else None, width=None, color=SUCCESS_GREEN, icon=ft.Icons.PLAY_ARROW),
                ft.Container(height=24),
                
                ft.Text("Test Output", size=18, weight=ft.FontWeight.W_600, color=PURPLE),
                ft.Container(height=8),
                ft.Container(
                    content=output_column,
                    padding=16,
                    bgcolor=hex_with_opacity("#FFFFFF", 0.1),
                    border=ft.border.all(1, GLASS_BORDER),
                    border_radius=12,
                ),
                ft.Container(height=24),
                
                ft.Text("Results History", size=18, weight=ft.FontWeight.W_600, color=PURPLE),
                ft.Container(height=8),
                ft.Container(
                    content=results_column,
                    padding=16,
                    bgcolor=hex_with_opacity("#FFFFFF", 0.1),
                    border=ft.border.all(1, GLASS_BORDER),
                    border_radius=12,
                ),
                ft.Container(height=12),
                ft.Row(
                    controls=[
                        create_glass_button(
                            "Copy Errors",
                            on_click=copy_error_output,
                            width=150,
                            color=WARNING_ORANGE,
                            icon=ft.Icons.CONTENT_COPY,
                        ),
                        create_glass_button(
                            "Refresh Results",
                            on_click=lambda e: refresh_results(),
                            width=None,
                            color=ACCENT_BLUE,
                        ),
                    ],
                    spacing=12,
                    wrap=True,
                ),
            ],
            spacing=12,
        ),
        padding=20,
        visible=False,
        expand=True,
    )


def add_automation_and_tests_tabs(page, tab_containers, tab_names, status_ref, log_callback, area_getter, config_getter):
    """Add Automation and Tests tabs to existing GUI."""
    
    try:
        # Initialize orchestrator if available
        orchestrator = None
        if AUTOMATION_AVAILABLE:
            try:
                orchestrator = AutomationOrchestrator()
                orchestrator.set_callbacks(
                    status_callback=lambda s: None,
                    log_callback=log_callback
                )
                # Load config
                try:
                    config_file = "farm_merger_config.json"
                    if os.path.exists(config_file):
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                            orchestrator.update_config(config)
                except:
                    pass
            except Exception as e:
                log_callback(f"Failed to initialize orchestrator: {e}", "error")
        
        # Create tabs - wrap in try-except to catch any creation errors
        try:
            automation_tab = create_automation_tab(page, orchestrator, status_ref, log_callback, area_getter, config_getter)
            tab_containers.append(automation_tab)
        except Exception as e:
            log_callback(f"Failed to create automation tab: {e}", "error")
            import traceback
            log_callback(f"Traceback: {traceback.format_exc()}", "error")
        
        try:
            tests_tab = create_tests_tab(page, log_callback)
            tab_containers.append(tests_tab)
        except Exception as e:
            log_callback(f"Failed to create tests tab: {e}", "error")
            import traceback
            log_callback(f"Traceback: {traceback.format_exc()}", "error")
        
        return orchestrator
    
    except Exception as e:
        log_callback(f"Error adding automation tabs: {e}", "error")
        import traceback
        log_callback(f"Traceback: {traceback.format_exc()}", "error")
        return None

