# Repository Guidelines

## Project Structure & Module Organization
Work from the repository root. All shipping code lives in `farm_merger/`: `gui.py` owns the Dear PyGui interface and orchestrates runtime threads, `item_finder.py` wraps OpenCV image detection, while `screen_area_selector.py` and `merging_points_selector.py` capture on-screen geometry. The CLI-oriented automation flow resides in `main.py`. Assets sit under `farm_merger/img/`, and runtime preferences are stored in `farm_merger_config.json` (regenerated safely per user). Keep the launchers (`Farm Merger Pro.bat`, `run_farm_merger.bat`) aligned with the docs (`README.md`, `CHANGELOG.md`, `FIXES.md`, `UI_IMPROVEMENTS.md`).

## Build, Test, and Development Commands
Use Python 3.7+ on Windows. Recommended bootstrap:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r farm_merger\requirements.txt
```
Run the full GUI locally with `python farm_merger\gui.py`. The CLI workflow can be exercised from `farm_merger` via `python main.py --merge_count 5`. The professional launcher (`Farm Merger Pro.bat`) double-checks dependencies and is the fastest smoke test for non-developers.

## Coding Style & Naming Conventions
Match the existing Python style: four-space indentation, double quotes for UI strings, snake_case functions, and CamelCase classes. Prefer explicit imports anchored to `farm_merger`. When touching GUI layout code, group related Dear PyGui builder calls and leave terse comments only where flow control is non-obvious. Keep configuration keys lower snake_case to remain compatible with the current JSON schema.

## Testing Guidelines
There is no automated test harness yet; rely on targeted manual runs. Validate the detection pipeline after changes by loading a representative `img/` subset and triggering a merge from the GUI log pane. For CLI-only changes, script a dry run with `--merge_count 1` and confirm no blocking modal dialogs appear. Document any new manual regression steps in `FIXES.md` until we formalize PyTest coverage.

## Commit & Pull Request Guidelines
Commits should be concise, present-tense, and scoped to one concern (e.g., `fix: tighten slot detection tolerance`). Update `CHANGELOG.md` for user-visible changes and note operator-facing tweaks in `UI_IMPROVEMENTS.md`. Pull requests must include: purpose summary, test evidence (commands run and outcomes), relevant screenshots when UI shifts, and links to tracked issues or Trello cards. Flag configuration migrations and asset updates explicitly so downstream operators can re-record screen regions.

## Configuration & Operations Notes
Treat `farm_merger_config.json` as user-specific; do not ship personal coordinates or hotkeys. The `img/` directory acts as the detection dataset—keep filenames descriptive (`item_tierX.png`) and avoid replacing baseline assets without noting the resolution. Batch files assume repository-root execution; update their relative paths if you reorganize directories.
