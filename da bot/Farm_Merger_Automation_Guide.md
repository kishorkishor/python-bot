# Kishor Farm Merger Pro - Automation Playbook

This guide captures everything the current tool already delivers, the shortcuts that make it shine, and a practical roadmap to push it to a fully automated farming companion. Keep it close while iterating on gameplay logic, GUI polish, and automation upgrades.

## Current Feature Stack (Shipping Today)

| Cluster | Capability | Where It Lives |
| --- | --- | --- |
| Instant control | `=` hotkey toggles start/stop, separate pause handle, responsive multiprocess loop | `gui.py` (`toggle_merge_process`, `start_merge_process`), `main.py` |
| Zero-box intelligence | Continues merging even with 0 boxes, throttles clicks to 1-5 per refill, live counter auto-decrements | `gui.py:start_merge`, `perform_box_clicks_at_point`, `update_log_message` |
| Image detection | OpenCV template matching, per-template thresholds, auto zoom-factor calibration across reference crops | `item_finder.py:ImageFinder`, `gui.py:calculate_resize_factor_callback` |
| Template catalog | JSON-driven thresholds, priorities, and reference samples for adaptive scans | img/catalog.json, item_finder.TemplateCatalog |
| Live box counter | OCR-powered counter capture with Tesseract checks and UI sync | gui.py:read_box_count_from_region, maybe_update_box_count_from_ocr, update_box_amount_ui |
| Screen geometry | Tk overlays for area capture and merge slot recording, board grid math with manual overrides | `screen_area_selector.py`, `merging_points_selector.py`, `gui.py:detect_board_layout` |
| Sorting brain | Auto-scan or manual grid input, duplicate tracking, deterministic regroup plan with buffer logic | `gui.py:detect_board_layout`, `generate_auto_sort_plan`, `run_sort_plan_callback` |
| Config profiles | Autosave on change, manual save/load, JSON schema keeps keys lower snake_case | `gui.py:save_config`, `load_config`, `farm_merger_config.json` |
| Logging & UX | Accent-themed Dear PyGui interface, queue-driven log window, color-coded status cards for boxes | `gui.py:setup_app_theme`, `add_log_output`, `update_log_message` |
| CLI fallback | Headless sort loop with keyboard listener for quick smoke tests and automation scripts | `main.py` |

## Power User Tricks Already Available
- Flip the **Auto-discover grid** toggle to compare catalog-driven scans vs. manual overrides without losing data.
- Capture the **Select counter area** after setting boxes to keep OCR in sync; hit Clear to fall back to manual input instantly.

- Hit **`Auto calculate`** before scanning; `ImageFinder.find_best_resize_factor` sweeps 0.8-2.0 zoom to tighten match confidence without hand-tuning.
- Use **Advanced -> Auto Scan** immediately after setting the playfield; it backfills slot metadata and flags duplicates, making the generated plan more accurate.
- Toggle **Manual Select** when auto-scan misses diagonally stacked items; once recorded, overrides persist via autosave.
- Keep an eye on the **log header icons**: `[info]` vs `[warn]` call-outs show up in real time and trigger box depletion failsafes.
- The **professional launcher** (`Farm Merger Pro.bat`) double-checks Python, virtualenv, and missing packages--great preflight for operators before you push changes.
- `main.py --merge_count 1` is a fast, non-GUI verification step when iterating on detection thresholds or drag timing.

## Roadmap to Full Automation

### Phase 1 - Robust Detection & State Awareness (Delivered in v2.3)
- [x] Dynamic board discovery feeds auto-scan with catalog metadata and updates the planner automatically.
- [x] Template metadata registry lives in img/catalog.json with priorities, rarities, and reference samples.
- [x] Live box counter integrates Tesseract OCR with UI fallbacks for manual entry.

### Phase 2 - Continuous Merge Orchestration
1. **Self-healing merge loop**  
   - When `perform_merge_cycle` returns False twice consecutively, trigger a scan refresh and optionally re-run `generate_auto_sort_plan`.  
   - Add a watchdog that restarts the process if the worker dies unexpectedly.
2. **Priority-based dragging**  
   - Sort `template_centers` by template metadata (rarity, desired target slot) before drag operations, letting rare items skip the buffer queue.
3. **Background slot calibration**  
   - Schedule a periodic `scan_board_button_callback` while idle to keep slot coordinates aligned with camera shifts.
4. **Integrated CLI sync**  
   - Share configuration via a thin wrapper module so CLI runs reuse GUI-calculated zoom, area, and slot data.

### Phase 3 - Operator UX & Telemetry
1. **Session timeline**  
   - Append merge events to a rolling JSON log (`logs/session-YYYYMMDD.json`) for replay and debugging.
2. **Remote preset library**  
   - Allow downloading curated `farm_merger_config.json` presets from a URL if network is available, gated behind an opt-in toggle.
3. **Health dashboard**  
   - Expose current FPS, merge speed, and success rate in a minimal overlay or embedded plot (Dear PyGui `plot_axis` widgets).

## GUI Vision & Styling Ideas

- **Command Deck Layout**: Convert the top of the right column into three glassmorphism tiles--`Run State`, `Boxes`, `Detected Slots`--each using the accent gradients already defined (`ACCENT_COLOR`, `SECONDARY_ACCENT`).
- **Mini Grid Preview**: Render the board inside a `dpg.drawlist` showing slot status, duplicates, and next target. Apply warm accent to the active move.
- **Quick Actions Ribbon**: Place compact icon buttons (start, pause, rescan, auto-sort) under the hero title for touch-friendly control.
- **Contextual Help Chips**: Swap static helper text for collapsible info chips--hover reveals short tooltips, click opens extended markdown via Dear PyGui `md` widget.
- **Dark Neon Variant**: Offer a theme toggle that inverts the palette (charcoal + cyan) by reusing `create_button_theme` with alternative tuples.

## Implementation Notes & Gotchas

- Keep `farm_merger_config.json` user-specific--never commit personal coordinates. Ship defaults through code.
- Make new assets descriptive (`img/dairy_super.png`) and document additions in `CHANGELOG.md` + `FIXES.md`.
- Long-running automation should always ensure `pyautogui.mouseUp()` at critical transitions (remove stale drag states before early exits).
- When expanding multiprocessing, guard UI callbacks (`dpg`) carefully--only the main process should mutate the GUI state.
- Install Tesseract OCR locally (and update `pytesseract.pytesseract.tesseract_cmd` if the binary is not on PATH).
- For OCR-driven box counting, cache the cropped region and reuse it to avoid capturing full-screen frames every tick.

## Manual QA Checklist After Each Iteration

1. `Farm Merger Pro.bat` -> verify dependency checks pass and GUI opens.
2. Select screen area, merge points, box button; ensure autosave updates status text.
3. Enable **Auto-discover grid**, run Auto Scan, and confirm the grid summary updates.
4. Capture the box counter region and verify OCR updates the display; clear to confirm manual fallback.
5. Start merge loop with `=`; observe box counter decrements and stop after depletion.
6. Re-run Advanced -> Generate Plan; execute to ensure drag offsets respect overrides.
7. Perform `python main.py --merge_count 1` in `farm_merger/` to confirm CLI remains functional.

Iterate on these steps as you layer in automation--document new quirks in `FIXES.md`, and keep the playbook synced with major feature drops.

