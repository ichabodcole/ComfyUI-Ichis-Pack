import hashlib
import time
import uuid
from typing import Dict, Iterable, List, Sequence

from .tag_data_utils import (
    TagMetadata,
    metadata_from_payload,
    normalize_categories_selection,
    parse_categories_string,
)


class ICHIS_Tag_Category_Select:
    """Select categories from loaded tag metadata."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tag_metadata": ("ICHIS_TAG_METADATA", {}),
            },
            "optional": {
                "categories": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "placeholder": "Newline separated categories",
                    },
                ),
                "allow_empty": ("BOOLEAN", {"default": False}),
                "debug": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("ICHIS_TAG_SELECTION", "LIST", "LIST")
    RETURN_NAMES = (
        "tag_selection",
        "selected_categories",
        "category_tags",
    )
    FUNCTION = "select_categories"
    CATEGORY = "ICHIS"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        metadata = kwargs.get("tag_metadata")
        categories = kwargs.get("categories", "")
        allow_empty = kwargs.get("allow_empty", False)
        meta_signature = ""
        if isinstance(metadata, dict):
            meta_signature = str(metadata.get("cache_signature", ""))
        elif isinstance(metadata, TagMetadata):
            meta_signature = str(metadata.cache_signature or "")
        parts = [meta_signature, categories, str(int(allow_empty))]
        return "|".join(parts)

    def _ensure_metadata(self, metadata_obj) -> TagMetadata:
        if isinstance(metadata_obj, TagMetadata):
            return metadata_obj
        if isinstance(metadata_obj, dict):
            return metadata_from_payload(metadata_obj)
        raise TypeError("tag_metadata must be TagMetadata or payload dict")

    def _compute_signature(self, metadata: TagMetadata, selected: Sequence[str]) -> str:
        hasher = hashlib.sha1()
        hasher.update(str(metadata.cache_signature or metadata.resolved_path).encode("utf-8"))
        hasher.update("||".join(selected).encode("utf-8"))
        return hasher.hexdigest()

    def select_categories(
        self,
        tag_metadata,
        categories: str = "",
        allow_empty: bool = False,
        debug: bool = False,
    ) -> tuple:
        metadata = self._ensure_metadata(tag_metadata)
        available = metadata.categories or []
        selected: List[str] = []
        manual = normalize_categories_selection(
            parse_categories_string(categories), metadata
        )
        if manual:
            selected = manual
        else:
            # Respect empty selections - don't auto-default to first category
            # This allows users to intentionally clear category selections
            selected = []
        category_tags: List[str] = []
        for category in selected:
            category_tags.extend(metadata.tags_by_category.get(category, []))
        # dedupe while preserving order
        seen = set()
        deduped_tags: List[str] = []
        for tag in category_tags:
            if tag not in seen:
                seen.add(tag)
                deduped_tags.append(tag)
        selection_payload: Dict[str, object] = {
            "selected_categories": list(selected),
            "category_tags": list(deduped_tags),
            "metadata_signature": metadata.cache_signature,
            "selection_signature": self._compute_signature(metadata, selected),
            "timestamp": time.time(),
            "id": str(uuid.uuid4()),
        }
        if debug:
            selection_payload["debug"] = {
                "metadata_categories": available,
                "input_categories": categories,
            }
        return (
            selection_payload,
            list(selected),
            deduped_tags,
        )
