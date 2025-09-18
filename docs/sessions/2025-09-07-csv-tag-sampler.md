Context
- Add a new ComfyUI node to sample random image tags from a CSV keyed by image path and category.

Scope & Objectives
- Implement node: read CSV, filter by image and optional categories, sample random tags between min/max.
- Register node and add unit tests with deterministic seeds.
- Keep implementation lightweight and follow repo conventions.

Plan
1. Review repo nodes/tests structure
2. Design CSV format and I/O
3. Implement node and register
4. Add unit tests
5. Document session

Environment
- Python 3.8+, pytest configured via pyproject.toml
- Local workspace-write, network restricted

Findings Log
- Existing nodes follow ICHIS_ prefix and simple INPUT_TYPES/RETURN_TYPES patterns.
- Tests instantiate node classes directly and call their methods.
- Added seed parameter for reproducibility; IS_CHANGED triggers when seed=0 to respect randomness.

Fixes Applied
- nodes/csv_tag_sampler.py: New node ICHIS_CSV_Tag_Sampler with CSV parsing and random sampling.
- nodes/__init__.py: Registered node in NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS.
- tests/test_csv_tag_sampler.py: Unit tests covering formats, filtering, clamping, empty result, and seed reproducibility.

Open Questions
- CSV format variants beyond the two supported (custom headers? multiple images per row?).
- Should image path matching be case-insensitive or support globbing?
- Additional outputs (e.g., list type) for downstream nodes?

Lessons Learned
- Adding a seed parameter greatly simplifies reliable testing for random behavior.
- Supporting both row-per-tag and row-per-category-list formats gives flexibility with minimal complexity.

Next Steps
- If desired, add UI options: allow duplicates, per-category min/max, and output list type.
- Extend tests to cover very large CSVs and performance.

