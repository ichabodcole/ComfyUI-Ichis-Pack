import csv
import os
import traceback
import random as rand_module
import time
import uuid
from typing import List, Set


class ICHIS_CSV_Tag_Sampler:
    """
    Read a CSV or JSON file of category/tag records and sample a random
    set of tags optionally filtered by category, with min/max selection
    bounds.

    Supported input formats:
    - CSV row-per-tag: category,tag
    - CSV row-per-category list: category,tags (comma/semicolon/pipe-separated)
    - CSV tag-only: tag
    - JSON: array of objects { "category": str, "tags": [str] }
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"placeholder": "Path to tags file (.csv or .json)"}),
                "min_count": ("INT", {"default": 1, "min": 0, "max": 4096}),
                "max_count": ("INT", {"default": 5, "min": 1, "max": 4096}),
            },
            "optional": {
                "categories": ("STRING", {"default": "", "multiline": False, "placeholder": "comma/newline separated; empty = all"}),
                "delimiter": ("STRING", {"default": ", "}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "unique_only": ("BOOLEAN", {"default": True}),
                "ignore_case_categories": ("BOOLEAN", {"default": True}),
                "base_dir": ("STRING", {"default": "", "placeholder": "optional base dir for csv_path"}),
                "debug": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "INT", "LIST")
    RETURN_NAMES = ("tags", "count", "tags_list")
    FUNCTION = "sample_tags"
    CATEGORY = "ICHIS"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # If seed is 0, treat as dynamic randomness and force execution each time
        if kwargs.get("seed", 0) == 0:
            return f"random_{time.time()}_{uuid.uuid4()}"
        return None

    def _parse_categories(self, categories: str, ignore_case: bool) -> Set[str]:
        if not categories:
            return set()
        # Split by comma and newline, strip whitespace
        raw = []
        for line in categories.split("\n"):
            raw.extend([p.strip() for p in line.split(",")])
        cats = [c for c in raw if c]
        if ignore_case:
            return {c.lower() for c in cats}
        return set(cats)

    def _split_tags_field(self, s: str) -> List[str]:
        if not s:
            return []
        parts: List[str] = []
        for sep in [",", ";", "|"]:
            # progressively split by separators; start by replacing with commas
            s = s.replace(sep, ",")
        for p in s.split(","):
            p = p.strip()
            if p:
                parts.append(p)
        return parts

    def _resolve_path(self, path: str, base_dir: str, debug: bool) -> str:
        original = path
        # expand user and env vars
        path = os.path.expandvars(os.path.expanduser(path))
        if base_dir:
            base_dir = os.path.expandvars(os.path.expanduser(base_dir))
            candidate = os.path.abspath(os.path.join(base_dir, path))
            if os.path.exists(candidate):
                if debug:
                    print(f"[CSV_Tag_Sampler] Resolved via base_dir: {candidate}")
                return candidate
        # try absolute/relative from cwd
        abs1 = os.path.abspath(path)
        if os.path.exists(abs1):
            if debug:
                print(f"[CSV_Tag_Sampler] Resolved path: {abs1}")
            return abs1
        if debug:
            print(f"[CSV_Tag_Sampler] Could not resolve path. original='{original}', expanded='{path}', base_dir='{base_dir}'")
        return abs1  # return best-effort absolute even if missing

    def _collect_tags_csv(self, csv_path: str, categories: Set[str], ignore_case: bool, debug: bool) -> List[str]:
        tags: List[str] = []
        # Accept a few header name variants
        category_keys = {"category", "cat"}
        tag_keys_single = {"tag"}
        tag_keys_list = {"tags"}

        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                # Validate required headers exist in some variant
                headers = {h.strip(): h for h in (reader.fieldnames or [])}
                if debug:
                    print(f"[CSV_Tag_Sampler] Headers detected: {list(headers.keys())}")
                if not headers:
                    if debug:
                        print("[CSV_Tag_Sampler] No headers found in CSV.")
                    return []

                # Map chosen keys present in file
                category_col = next((headers[k] for k in headers if k.lower() in category_keys), None)
                tag_col_single = next((headers[k] for k in headers if k.lower() in tag_keys_single), None)
                tag_col_list = next((headers[k] for k in headers if k.lower() in tag_keys_list), None)

                if debug:
                    print(f"[CSV_Tag_Sampler] Using columns -> category: {category_col}, tag(single): {tag_col_single}, tags(list): {tag_col_list}")

                # Require at least one tag column; image and category are optional
                if (not tag_col_single and not tag_col_list):
                    if debug:
                        print("[CSV_Tag_Sampler] Missing tag column(s) (tag/tags). Nothing to extract.")
                    return []

                matched_rows = 0
                for row in reader:
                    if not row:
                        continue

                    matched_rows += 1
                    if category_col:
                        cat_val = (row.get(category_col) or "").strip()
                        cat_cmp = cat_val.lower() if ignore_case else cat_val
                        # If categories set provided, filter
                        if categories and cat_cmp not in categories:
                            continue

                    row_tags: List[str] = []
                    if tag_col_single and row.get(tag_col_single):
                        t = (row.get(tag_col_single) or "").strip()
                        if t:
                            row_tags.append(t)
                    if tag_col_list and row.get(tag_col_list):
                        list_str = (row.get(tag_col_list) or "").strip()
                        row_tags.extend(self._split_tags_field(list_str))

                    # extend to global list
                    tags.extend(rt for rt in row_tags if rt)

                if debug:
                    print(f"[CSV_Tag_Sampler] Rows considered: {matched_rows}")
        except Exception as e:
            if debug:
                print(f"[CSV_Tag_Sampler] Error opening/reading CSV: {e}")
                traceback.print_exc()
            return []

        # Deduplicate while preserving order
        seen: Set[str] = set()
        uniq: List[str] = []
        for t in tags:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        return uniq

    def _collect_tags_json(self, json_path: str, categories: Set[str], ignore_case: bool, debug: bool) -> List[str]:
        import json
        tags: List[str] = []
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                if debug:
                    print("[CSV_Tag_Sampler] JSON root is not a list; expecting an array of objects.")
                return []
            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    continue
                cat_val = (item.get("category") or "").strip()
                cat_cmp = cat_val.lower() if ignore_case else cat_val
                if categories and cat_cmp not in categories:
                    continue
                row_tags = item.get("tags", [])
                if isinstance(row_tags, str):
                    # allow string with separators too
                    row_tags = self._split_tags_field(row_tags)
                elif isinstance(row_tags, list):
                    row_tags = [str(t).strip() for t in row_tags if str(t).strip()]
                else:
                    row_tags = []
                tags.extend(rt for rt in row_tags if rt)
        except Exception as e:
            if debug:
                print(f"[CSV_Tag_Sampler] Error reading JSON: {e}")
                traceback.print_exc()
            return []
        # dedupe preserve order
        seen: Set[str] = set()
        uniq: List[str] = []
        for t in tags:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        return uniq

    def sample_tags(
        self,
        file_path: str,
        min_count: int = 1,
        max_count: int = 5,
        categories: str = "",
        delimiter: str = ", ",
        seed: int = 0,
        unique_only: bool = True,
        ignore_case_categories: bool = True,
        base_dir: str = "",
        debug: bool = False,
    ) -> tuple:
        if debug:
            print("[CSV_Tag_Sampler] ===== Debug Enabled =====")
            print(f"[CSV_Tag_Sampler] CWD: {os.getcwd()}")
            print(f"[CSV_Tag_Sampler] Input file_path: {file_path}")
            print(f"[CSV_Tag_Sampler] base_dir: {base_dir}")
            print(f"[CSV_Tag_Sampler] min_count: {min_count}, max_count: {max_count}")
            print(f"[CSV_Tag_Sampler] categories(raw): '{categories}'")

        # Normalize bounds
        if min_count < 0:
            min_count = 0
        if max_count < 0:
            max_count = 0
        if min_count > max_count:
            min_count, max_count = max_count, min_count

        # Parse categories filter
        cats = self._parse_categories(categories, ignore_case_categories)
        if debug:
            print(f"[CSV_Tag_Sampler] categories(parsed): {sorted(list(cats))}")

        # Collect all candidate tags
        resolved_file = self._resolve_path(file_path, base_dir, debug)
        if debug:
            print(f"[CSV_Tag_Sampler] Resolved file exists: {os.path.exists(resolved_file)} -> {resolved_file}")
        # Dispatch by extension
        ext = os.path.splitext(resolved_file)[1].lower()
        if ext == ".json":
            if debug:
                print("[CSV_Tag_Sampler] Detected JSON input.")
            tags = self._collect_tags_json(resolved_file, cats, ignore_case_categories, debug)
        else:
            tags = self._collect_tags_csv(resolved_file, cats, ignore_case_categories, debug)
        if not tags:
            if debug:
                print("[CSV_Tag_Sampler] No tags found after filtering.")
            return ("", 0)

        # When not unique, allow duplicates by sampling with replacement
        # Implemented by expanding the pool; but we will default to unique_only
        if unique_only:
            available = tags
        else:
            # allow duplicates by repeating list to ensure enough population
            available = tags * max(1, max_count // max(1, len(tags)) + 1)

        # Seed if provided
        if seed != 0:
            rand_module.seed(seed)

        # Determine how many to pick
        upper = max_count
        lower = min_count
        # If available is smaller than desired and unique_only, clamp
        if unique_only:
            upper = min(max_count, len(available))
            lower = min(min_count, len(available))

        k = rand_module.randint(lower, upper) if upper >= lower else 0

        if debug:
            print(f"[CSV_Tag_Sampler] Candidate tags (unique={unique_only}): {len(available)} available -> {available}")
            print(f"[CSV_Tag_Sampler] Sampling k between [{lower}, {upper}] => {k}")

        if k <= 0:
            if debug:
                print("[CSV_Tag_Sampler] k <= 0, returning empty result.")
            return ("", 0)

        if unique_only:
            chosen = rand_module.sample(available, k)
        else:
            # with replacement
            chosen = [rand_module.choice(available) for _ in range(k)]

        result = delimiter.join(chosen)
        if debug:
            print(f"[CSV_Tag_Sampler] Chosen tags: {chosen}")
            print(f"[CSV_Tag_Sampler] Result: '{result}' (count={len(chosen)})")
        return (result, len(chosen), chosen)
