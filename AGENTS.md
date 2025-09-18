# Repository Guidelines

## Project Structure & Module Organization

- `nodes/` — ComfyUI nodes (e.g., `aspect_ratio_plus.py`, `text_selector.py`, `extract_tags.py`). Register new nodes in `nodes/__init__.py` under `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`.
- `tests/` — unit tests (`test_*.py`) covering node behavior.
- `pyproject.toml` — pytest and coverage config; packaging via setuptools.
- `requirements.txt` — test/runtime deps; `setup_venv.sh` — optional dev setup via `uv`.

## Build, Test, and Development Commands

- Create venv (uv): `./setup_venv.sh` then `source .venv/bin/activate`.
- Create venv (pip): `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pip install -e .`.
- Run tests with coverage: `pytest` (configured to show term-missing for `nodes/`).
- Targeted test: `pytest -k text_selector -q`.
- Install into ComfyUI: clone this repo into `ComfyUI/custom_nodes/` and restart ComfyUI.

## Coding Style & Naming Conventions

- Python 3.8+; follow PEP 8 with 4‑space indents.
- Module files: snake_case (e.g., `my_new_node.py`).
- Node classes: `ICHIS_` prefix + PascalCase (e.g., `ICHIS_My_New_Node`).
- Docstrings: triple‑quoted, concise purpose + I/O description.
- Type hints encouraged for public methods.
- Keep imports lightweight at module import; heavy work inside functions.

## Testing Guidelines

- Framework: pytest (tests live in `tests/`, named `test_*.py`).
- Aim for ≥80% coverage on `nodes/` (see `pyproject.toml`).
- Prefer small, deterministic tests; avoid GPU‑dependent assertions. Use seeds where randomness exists (e.g., `seed=` args).
- Example: `pytest -q --maxfail=1` for quick iteration.

## Commit & Pull Request Guidelines

- Commits: clear, imperative summary (e.g., "Add ICHIS_Text_Splitter node"). Reference scope when helpful (`nodes/…`, `tests/…`).
- Include: rationale, behavior changes, and test updates.
- PRs: describe the feature/fix, link issues, include before/after examples or screenshots (if UI-ish), and note ComfyUI workflow usage.

## Agent-Specific Tips

- When adding a node: implement class, add to `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`, add unit tests, and update README if user-facing.
- Do not change existing node signatures without deprecation notes and test updates.

## Session Documentation Guidelines

### Purpose

- Keep work transparent and reproducible by maintaining a lightweight session log in `docs/sessions/`.
- Make minimal, targeted changes; prefer adapting tests/docs over altering app logic unless necessary.

### When Starting Work

- Create or update a session document in `docs/sessions/`:
  - File name: `YYYY-MM-DD-short-topic.md` (e.g., `2025-09-06-upgrade-test-fix-session.md`).
  - If a same-day session exists for the topic, continue in that file.
- Use the plan tool to outline steps if work spans multiple actions or files.

### Session Doc Structure

- Context — What changed and why we’re here.
- Scope & Objectives — What is in/out of scope and the goals.
- Plan — Short, verifiable steps (keep to 5–7 items).
- Environment — Runners, configs, and any important cautions.
- Findings Log — Timestamped notes as you discover issues.
- Fixes Applied — Bullet list of code/test/docs changes.
- Open Questions — Items needing decisions or follow‑up.
- Lessons Learned — Notes useful for future similar tasks.
- Next Steps — Optional checklist for the next pass.

### Style & Process

- Be concise and practical; prefer bullets over prose.
- Log what you ran and why only when it matters for replication.
- Update the session doc as you go (don’t wait until the end).
- Use `functions.update_plan` to keep the plan current with exactly one `in_progress` step.

### Testing Notes

- If tests are part of the task, run unit tests first; then integration as needed.
- Prefer robust assertions over brittle string matches for third‑party error messages.
- Keep mocks aligned with real import paths/aliases.

### Wrapping Up

- Ensure the session doc reflects the final state (what passed/failed, what changed).
- Propose clear next steps if work continues later.