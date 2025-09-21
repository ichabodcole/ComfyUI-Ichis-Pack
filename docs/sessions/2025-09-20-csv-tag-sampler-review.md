# Context
- Reviewing `ICHIS_Tag_Sampler` (formerly `ICHIS_CSV_Tag_Sampler`) for potential modular redesign supporting tag file loaders and dynamic category selection inputs.

# Scope & Objectives
- Assess current node capabilities and ComfyUI constraints around dynamic selects.
- Outline strategy for modular tag loader + category selector workflow without implementing code.
- Identify open questions or prerequisites for dynamic input support.

# Plan
1. Review existing `ICHIS_Tag_Sampler` (legacy `ICHIS_CSV_Tag_Sampler`) implementation and related files for current capabilities.
2. Assess ComfyUI support for dynamic selects/inputs and relevant patterns in repo or known modules.
3. Formulate modular strategy and recommendations for tag loader and category selection workflow.

# Environment
- Repo: `ComfyUI_Ichis_Pack` (local workspace write access).
- Date: 2025-09-20.
- Network access restricted; no external fetch without approval.
- ComfyUI node framework baseline, Python 3.8+ assumptions per project guidelines.

# Findings Log
- 2025-09-20 09:05 — Reviewed `nodes/tag_sampler.py` (`ICHIS_Tag_Sampler`); node loads CSV/JSON synchronously, expects manual category string filter, no cached metadata or UI-driven category discovery.
- 2025-09-20 09:20 — Confirmed tests (`tests/test_csv_tag_sampler*.py`) focus on path parsing/sampling but not UI integration, reinforcing need for separate loader abstraction.
- 2025-09-20 09:35 — Looked into ComfyUI dynamic input patterns (folder listing refresh, Cozy dynamic inputs example, docs on dynamic widgets); dynamic select content must come from UI state or custom JS extension, not just class-level `INPUT_TYPES`.
- 2025-09-20 10:40 — Implemented `TagMetadata` utilities plus loader/select nodes producing structured payloads and cache signatures for downstream nodes.
- 2025-09-20 11:05 — Refactored sampler to consume metadata/selection first, retaining `file_path` fallback for legacy graphs.
- 2025-09-20 11:20 — Added unit tests covering loader caching, category selection, and end-to-end sampling via metadata.
- 2025-09-20 11:35 — `python3 -m pytest` unavailable locally (pytest not installed; requirements include torch, so tests deferred pending environment setup).
- 2025-09-20 12:00 — Cloned `cozy_ex_dynamic` example to review dynamic input JS hook (`beforeRegisterNodeDef` adding/removing slots on connection events).
- 2025-09-20 12:30 — Extended Tag Category Select outputs to include category tags list and added optional `category_list` consumption in sampler.
- 2025-09-20 12:45 — Prototyped `web/tag_category_select.js` extension to manage combo widgets and populate options from loader metadata when available (updated path to ComfyUI `scripts/app.js`, guarded LiteGraph usage, added debug widget/logs).
- 2025-09-20 13:10 — Exported `WEB_DIRECTORY` via package `__init__` so ComfyUI loads the new JS assets.
- 2025-09-20 13:40 — Added PromptServer broadcast in `ICHIS_Tag_File_Loader` and JS listener to receive category updates via `ichis-tag-loader` event.
- 2025-09-20 13:55 — JS listener now auto-selects first category on update, syncs hidden widget + widgets_values, tracks selector instances, and matches loader broadcasts by unique id or file path for reliability.
- 2025-09-20 14:05 — Simplified Tag Category Select to focus on manual selections (removed all/manual toggle) and default to first category when empty so outputs mirror chosen categories only; added sync debug logging, newline-aware category parsing, and removed delimiter handling in favor of newline-separated categories.
- 2025-09-20 14:30 — Experimented with compact `ICHIS_Tag_Sampler` node (loader + selector + sampler) to compare approaches.
- 2025-09-20 14:40 — Added lessons-learned and recipe docs capturing dynamic UI guidance.
- 2025-09-20 14:50 — Retired compact sampler experiment and refocused `ICHIS_Tag_Sampler` on metadata-only inputs.
- 2025-09-20 15:00 — Trimmed sampler interface: removed inline category/delimiter fields so it strictly consumes loader/selector outputs.

# Fixes Applied
- Added `nodes/tag_data_utils.py` with shared parsing, caching signatures, and helpers.
- Created `ICHIS_Tag_File_Loader` and `ICHIS_Tag_Category_Select` nodes plus registration entries.
- Refactored `ICHIS_Tag_Sampler` to prioritize metadata inputs while keeping legacy fallback.
- Expanded test suite with loader, selector, and metadata-driven sampler coverage.
- Added combo widget JS scaffold for Tag Category Select and exposed category tag outputs for downstream wiring.
- Documented dynamic UI approach (`docs/lessons/dynamic-node-ui-lessons.md`, `docs/recipes/dynamic-select-loader.md`).
- Simplified `ICHIS_Tag_Sampler` to consume loader metadata only; removed provisional compact node artifacts.

# Open Questions
- Ideal UI/JS hook to repopulate combo boxes automatically once metadata payload updates.
- Whether to expose cache invalidation controls beyond the current boolean `refresh` toggle (e.g., TTL or file watcher).

# Lessons Learned
- Centralizing parsing into reusable utilities simplifies keeping loader, selector, and sampler aligned while enabling future UI enhancements.

# Next Steps
- Harden JS extension with better detection/removal controls for category widgets (e.g., "–" button, drag to reorder).
- Evaluate metadata payload size for large tag sets and consider compression or paging strategies if needed.
- Communicate deprecation timeline for direct `file_path` usage now that the sampler is metadata-only.
