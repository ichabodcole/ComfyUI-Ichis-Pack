"""Utilities for loading tag metadata from CSV or JSON sources."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import traceback
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

UNCATEGORIZED_LABEL = "uncategorized"


def split_tags_field(value: str) -> List[str]:
    """Split a delimited string into individual tag values."""
    if not value:
        return []
    # Normalize to comma separators, then split and trim
    normalized = value
    for sep in [";", "|", "\t"]:
        normalized = normalized.replace(sep, ",")
    parts = []
    for fragment in normalized.split(","):
        fragment = fragment.strip()
        if fragment:
            parts.append(fragment)
    return parts


def resolve_path(path: str, base_dir: str = "", debug: bool = False) -> str:
    """Resolve a path relative to optional base_dir while expanding user/env vars."""
    original = path
    path = os.path.expandvars(os.path.expanduser(path))
    if base_dir:
        base_dir = os.path.expandvars(os.path.expanduser(base_dir))
        candidate = os.path.abspath(os.path.join(base_dir, path))
        if os.path.exists(candidate):
            if debug:
                print(f"[TagData] Resolved via base_dir: {candidate}")
            return candidate
    abs_path = os.path.abspath(path)
    if debug:
        if os.path.exists(abs_path):
            print(f"[TagData] Resolved path: {abs_path}")
        else:
            print(
                "[TagData] Could not resolve path",
                f"original='{original}', expanded='{path}', base_dir='{base_dir}'",
            )
    return abs_path


@dataclass
class TagMetadata:
    resolved_path: str
    source_path: str
    source_type: str
    mtime: Optional[float]
    ignore_case: bool
    categories: List[str] = field(default_factory=list)
    tags_by_category: Dict[str, List[str]] = field(default_factory=dict)
    all_tags: List[str] = field(default_factory=list)
    category_alias_map: Dict[str, str] = field(default_factory=dict)
    uncategorized_label: str = UNCATEGORIZED_LABEL
    errors: List[str] = field(default_factory=list)
    debug_messages: List[str] = field(default_factory=list)
    cache_signature: Optional[str] = None

    def as_payload(self) -> Dict[str, object]:
        """Return a dict suitable for passing through ComfyUI sockets."""
        return {
            "resolved_path": self.resolved_path,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "mtime": self.mtime,
            "ignore_case": self.ignore_case,
            "categories": list(self.categories),
            "tags_by_category": {k: list(v) for k, v in self.tags_by_category.items()},
            "all_tags": list(self.all_tags),
            "category_alias_map": dict(self.category_alias_map),
            "uncategorized_label": self.uncategorized_label,
            "errors": list(self.errors),
            "debug_messages": list(self.debug_messages),
            "cache_signature": self.cache_signature,
        }


def compute_metadata_signature(metadata: TagMetadata) -> str:
    hasher = hashlib.sha1()
    hasher.update(metadata.resolved_path.encode("utf-8", errors="ignore"))
    hasher.update(str(metadata.mtime or 0).encode("utf-8"))
    hasher.update(str(metadata.ignore_case).encode("utf-8"))
    hasher.update("||".join(metadata.categories).encode("utf-8"))
    hasher.update("||".join(metadata.all_tags).encode("utf-8"))
    return hasher.hexdigest()


class _TagAggregator:
    def __init__(self, ignore_case: bool) -> None:
        self.ignore_case = ignore_case
        self.category_alias_map: Dict[str, str] = {}
        self.categories_order: List[str] = []
        self.tags_by_category: Dict[str, List[str]] = {}
        self.tags_seen_by_category: Dict[str, set] = {}
        self.all_tags: List[str] = []
        self.all_tags_seen: set = set()

    def _normalize_category(self, category: Optional[str]) -> Tuple[str, str]:
        display = (category or "").strip()
        if not display:
            display = UNCATEGORIZED_LABEL
        canonical = display.lower() if self.ignore_case else display
        if canonical not in self.category_alias_map:
            self.category_alias_map[canonical] = display
            self.categories_order.append(display)
            self.tags_by_category[display] = []
            self.tags_seen_by_category[display] = set()
        return canonical, self.category_alias_map[canonical]

    def add_tags(self, category: Optional[str], tags: Iterable[str]) -> None:
        canonical, display = self._normalize_category(category)
        target_list = self.tags_by_category[display]
        seen = self.tags_seen_by_category[display]
        for tag in tags:
            tag = (tag or "").strip()
            if not tag:
                continue
            if tag not in seen:
                seen.add(tag)
                target_list.append(tag)
            if tag not in self.all_tags_seen:
                self.all_tags_seen.add(tag)
                self.all_tags.append(tag)

    def finalize(self) -> Dict[str, object]:
        return {
            "categories": list(self.categories_order),
            "tags_by_category": {k: list(v) for k, v in self.tags_by_category.items()},
            "all_tags": list(self.all_tags),
            "category_alias_map": dict(self.category_alias_map),
            "uncategorized_label": UNCATEGORIZED_LABEL,
        }


def _collect_from_csv(path: str, ignore_case: bool, debug: bool, debug_log: List[str]) -> Dict[str, object]:
    aggregator = _TagAggregator(ignore_case)
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            headers = [h.strip() for h in (reader.fieldnames or [])]
            if debug:
                debug_log.append(f"CSV headers: {headers}")
            if not headers:
                debug_log.append("CSV missing headers; expected at least a tag column")
                return aggregator.finalize()
            lower_map = {h.lower(): h for h in headers}
            category_col = next((lower_map[key] for key in ("category", "cat") if key in lower_map), None)
            tag_col_single = lower_map.get("tag")
            tag_col_list = lower_map.get("tags")
            if debug:
                debug_log.append(
                    "Using columns -> "
                    f"category: {category_col}, tag(single): {tag_col_single}, tags(list): {tag_col_list}"
                )
            if not tag_col_single and not tag_col_list:
                debug_log.append("No tag column detected (tag/tags)")
                return aggregator.finalize()
            for row in reader:
                if not row:
                    continue
                category = row.get(category_col) if category_col else None
                row_tags: List[str] = []
                if tag_col_single and row.get(tag_col_single):
                    row_tags.append((row.get(tag_col_single) or "").strip())
                if tag_col_list and row.get(tag_col_list):
                    row_tags.extend(split_tags_field(row.get(tag_col_list) or ""))
                aggregator.add_tags(category, row_tags)
    except Exception as exc:
        debug_log.append(f"Error reading CSV: {exc}")
        if debug:
            traceback.print_exc()
    return aggregator.finalize()


def _collect_from_json(path: str, ignore_case: bool, debug: bool, debug_log: List[str]) -> Dict[str, object]:
    aggregator = _TagAggregator(ignore_case)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, Sequence):
            debug_log.append("JSON root must be a list of objects")
            return aggregator.finalize()
        for entry in data:
            if not isinstance(entry, dict):
                continue
            category = entry.get("category")
            tags_field = entry.get("tags", [])
            if isinstance(tags_field, str):
                tags = split_tags_field(tags_field)
            elif isinstance(tags_field, Sequence):
                tags = [str(t).strip() for t in tags_field if str(t).strip()]
            else:
                tags = []
            aggregator.add_tags(category, tags)
    except Exception as exc:
        debug_log.append(f"Error reading JSON: {exc}")
        if debug:
            traceback.print_exc()
    return aggregator.finalize()


def load_tag_metadata(
    resolved_path: str,
    ignore_case: bool = True,
    debug: bool = False,
) -> TagMetadata:
    """Load tag metadata from a CSV or JSON file."""
    debug_log: List[str] = []
    source_type = "csv"
    ext = os.path.splitext(resolved_path)[1].lower()
    if ext == ".json":
        source_type = "json"
        payload = _collect_from_json(resolved_path, ignore_case, debug, debug_log)
    else:
        payload = _collect_from_csv(resolved_path, ignore_case, debug, debug_log)
    mtime: Optional[float] = None
    if os.path.exists(resolved_path):
        try:
            mtime = os.path.getmtime(resolved_path)
        except OSError:
            mtime = None
    metadata = TagMetadata(
        resolved_path=resolved_path,
        source_path=resolved_path,
        source_type=source_type,
        mtime=mtime,
        ignore_case=ignore_case,
        categories=payload.get("categories", []),
        tags_by_category=payload.get("tags_by_category", {}),
        all_tags=payload.get("all_tags", []),
        category_alias_map=payload.get("category_alias_map", {}),
        uncategorized_label=payload.get("uncategorized_label", UNCATEGORIZED_LABEL),
        debug_messages=debug_log,
    )
    return metadata


def metadata_from_payload(payload: Dict[str, object]) -> TagMetadata:
    """Reconstruct TagMetadata from a payload dict."""
    metadata = TagMetadata(
        resolved_path=str(payload.get("resolved_path", "")),
        source_path=str(payload.get("source_path", "")),
        source_type=str(payload.get("source_type", "")),
        mtime=payload.get("mtime"),
        ignore_case=bool(payload.get("ignore_case", True)),
        categories=list(payload.get("categories", [])),
        tags_by_category={
            str(k): list(v) for k, v in (payload.get("tags_by_category", {}) or {}).items()
        },
        all_tags=list(payload.get("all_tags", [])),
        category_alias_map={
            str(k): str(v)
            for k, v in (payload.get("category_alias_map", {}) or {}).items()
        },
        uncategorized_label=str(payload.get("uncategorized_label", UNCATEGORIZED_LABEL)),
        errors=list(payload.get("errors", [])),
        debug_messages=list(payload.get("debug_messages", [])),
        cache_signature=payload.get("cache_signature"),
    )
    return metadata


def normalize_categories_selection(
    categories: Iterable[str],
    metadata: TagMetadata,
) -> List[str]:
    """Normalize a list of category strings against available metadata."""
    normalized: List[str] = []
    alias_map = metadata.category_alias_map or {}
    ignore_case = metadata.ignore_case
    seen = set()
    for raw in categories:
        candidate = (raw or "").strip()
        if not candidate:
            continue
        canonical = candidate.lower() if ignore_case else candidate
        if canonical in alias_map:
            resolved = alias_map[canonical]
        else:
            resolved = candidate
        if resolved not in seen and resolved in metadata.tags_by_category:
            seen.add(resolved)
            normalized.append(resolved)
    return normalized


def parse_categories_string(value: str) -> List[str]:
    """Parse category string using newline separation only.
    
    This function expects newline-separated category names and does NOT
    fall back to comma-splitting, as category names may contain commas.
    """
    if not value:
        return []
    parts: List[str] = []
    # Always split on newlines only - no comma fallback to preserve
    # category names that contain commas
    candidates = value.split("\n")
    for fragment in candidates:
        fragment = fragment.strip()
        if fragment:
            parts.append(fragment)
    return parts
