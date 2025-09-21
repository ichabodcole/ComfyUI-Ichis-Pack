import os
import time
import uuid
from typing import Dict, Tuple

from .tag_data_utils import (
    TagMetadata,
    compute_metadata_signature,
    load_tag_metadata,
    resolve_path,
)

try:  # ComfyUI runtime
    from server import PromptServer  # type: ignore
except Exception:  # pragma: no cover - during tests PromptServer unavailable
    PromptServer = None  # type: ignore


class ICHIS_Tag_File_Loader:
    """Load tag metadata from CSV or JSON files with simple caching."""

    _CACHE: Dict[Tuple[str, bool], TagMetadata] = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"placeholder": "Path to tags file (.csv or .json)"}),
            },
            "optional": {
                "base_dir": ("STRING", {"default": "", "placeholder": "Optional base dir"}),
                "ignore_case": ("BOOLEAN", {"default": True}),
                "refresh": ("BOOLEAN", {"default": False, "label": "Force reload"}),
                "debug": ("BOOLEAN", {"default": False}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("ICHIS_TAG_METADATA", "LIST", "LIST", "STRING", "BOOLEAN")
    RETURN_NAMES = ("metadata", "categories", "all_tags", "resolved_path", "cache_hit")
    FUNCTION = "load_tags"
    CATEGORY = "ICHIS"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed = kwargs.get("_loader_seed", 0)
        file_path = kwargs.get("file_path", "")
        ignore_case = kwargs.get("ignore_case", True)
        base_dir = kwargs.get("base_dir", "")
        refresh = kwargs.get("refresh", False)
        resolved = resolve_path(file_path, base_dir, False) if file_path else ""
        stamp = "missing"
        if resolved and os.path.exists(resolved):
            try:
                mtime = os.path.getmtime(resolved)
                stamp = f"{resolved}:{mtime}:{ignore_case}"
            except OSError:
                stamp = f"{resolved}:unknown:{ignore_case}"
        parts = [stamp, str(int(ignore_case)), str(int(refresh))]
        if seed == 0:
            parts.append(f"rand_{time.time()}_{uuid.uuid4()}")
        return "|".join(parts)

    @classmethod
    def clear_cache(cls):
        cls._CACHE.clear()

    def _broadcast_metadata(self, unique_id: str, payload: Dict[str, object]) -> None:
        if not unique_id or PromptServer is None:
            return
        try:
            data = {
                "unique_id": unique_id,
                "categories": payload.get("categories", []),
                "all_tags": payload.get("all_tags", []),
                "resolved_path": payload.get("resolved_path"),
                "source_path": payload.get("source_path"),
                "timestamp": time.time(),
            }
            PromptServer.instance.send_sync("ichis-tag-loader", data)
        except Exception:
            # Silently ignore broadcast failures to keep offline usage working.
            pass

    def load_tags(
        self,
        file_path: str = "",
        base_dir: str = "",
        ignore_case: bool = True,
        refresh: bool = False,
        debug: bool = False,
        _loader_seed: int = 0,
        unique_id: str = "",
    ) -> tuple:
        if not file_path:
            raise TypeError("file_path is required")

        resolved = resolve_path(file_path, base_dir, debug)
        if not os.path.exists(resolved):
            metadata = TagMetadata(
                resolved_path=resolved,
                source_path=file_path,
                source_type="missing",
                mtime=None,
                ignore_case=ignore_case,
                errors=[f"File not found: {resolved}"],
                debug_messages=["File missing; returning empty metadata"],
            )
            metadata.cache_signature = f"missing:{resolved}:{ignore_case}"
            payload = metadata.as_payload()
            self._broadcast_metadata(unique_id, payload)
            return (payload, [], [], resolved, False)

        cache_key = (resolved, bool(ignore_case))
        cached = None if refresh else self._CACHE.get(cache_key)
        mtime = None
        try:
            mtime = os.path.getmtime(resolved)
        except OSError:
            mtime = None
        cache_hit = False
        if cached and cached.mtime == mtime:
            metadata = cached
            cache_hit = True
        else:
            metadata = load_tag_metadata(resolved, ignore_case=ignore_case, debug=debug)
            metadata.mtime = mtime
            metadata.cache_signature = compute_metadata_signature(metadata)
            if not refresh:
                self._CACHE[cache_key] = metadata
        payload = metadata.as_payload()
        self._broadcast_metadata(unique_id, payload)
        return (
            payload,
            list(payload.get("categories", [])),
            list(payload.get("all_tags", [])),
            resolved,
            cache_hit,
        )
