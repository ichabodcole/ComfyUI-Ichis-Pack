import random as rand_module
import time
import uuid
from typing import Dict, List, Sequence

from .tag_data_utils import (
    TagMetadata,
    metadata_from_payload,
    normalize_categories_selection,
)


class ICHIS_Tag_Sampler:
    """
    Sample tags from metadata produced by ``ICHIS_Tag_File_Loader`` and
    ``ICHIS_Tag_Category_Select``.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tag_metadata": ("ICHIS_TAG_METADATA", {}),
                "min_count": ("INT", {"default": 1, "min": 0, "max": 4096}),
                "max_count": ("INT", {"default": 5, "min": 1, "max": 4096}),
            },
            "optional": {
                "tag_selection": ("ICHIS_TAG_SELECTION", {}),
                "category_list": ("LIST", {}),
                "seed": (
                    "INT",
                    {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF},
                ),
                "unique_only": ("BOOLEAN", {"default": True}),
                "per_category": ("BOOLEAN", {"default": False}),
                "ignore_case_categories": ("BOOLEAN", {"default": True}),
                "debug": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "INT", "LIST")
    RETURN_NAMES = ("tags", "count", "tags_list")
    FUNCTION = "sample_tags"
    CATEGORY = "ICHIS"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed = kwargs.get("seed", 0)
        metadata = kwargs.get("tag_metadata")
        selection = kwargs.get("tag_selection")
        ignore_case = kwargs.get("ignore_case_categories", True)
        category_list = kwargs.get("category_list")
        per_category = kwargs.get("per_category", False)

        meta_sig = ""
        if isinstance(metadata, dict):
            meta_sig = str(metadata.get("cache_signature", ""))
        elif isinstance(metadata, TagMetadata):
            meta_sig = str(metadata.cache_signature or "")
        selection_sig = ""
        if isinstance(selection, dict):
            selection_sig = str(selection.get("selection_signature", ""))
        category_sig = ""
        if category_list:
            category_sig = "||".join(map(str, category_list))
        parts = [meta_sig, selection_sig, category_sig, str(per_category)]
        if seed == 0:
            parts.append(f"rand_{time.time()}_{uuid.uuid4()}")
        return "|".join(parts)

    def _select_categories(
        self,
        metadata,
        tag_selection,
        category_list,
    ) -> List[str]:
        if category_list:
            normalized = normalize_categories_selection(category_list, metadata)
            if normalized:
                return normalized
            return []
        if isinstance(tag_selection, dict):
            selected = tag_selection.get("selected_categories") or []
            normalized = normalize_categories_selection(selected, metadata)
            if normalized:
                return normalized
        # When no specific selection is provided, return empty list
        # The caller will handle defaulting to all categories if needed
        return []

    def _gather_candidate_tags(
        self,
        metadata,
        categories: Sequence[str],
    ) -> List[str]:
        if not categories:
            return []
        seen = set()
        result: List[str] = []
        for category in categories:
            if isinstance(metadata, dict):
                tags = metadata.get("tags_by_category", {}).get(category, [])
            else:
                tags = metadata.tags_by_category.get(category, [])
            for tag in tags:
                if tag not in seen:
                    seen.add(tag)
                    result.append(tag)
        return result

    def sample_tags(
        self,
        tag_metadata,
        min_count: int = 1,
        max_count: int = 5,
        tag_selection=None,
        category_list=None,
        seed: int = 0,
        unique_only: bool = True,
        per_category: bool = False,
        ignore_case_categories: bool = True,
        debug: bool = False,
    ) -> tuple:
        if tag_metadata is None:
            raise TypeError("tag_metadata is required")
        if isinstance(tag_metadata, TagMetadata):
            metadata = tag_metadata
        elif isinstance(tag_metadata, dict):
            metadata = metadata_from_payload(tag_metadata)
        else:
            raise TypeError("tag_metadata must be TagMetadata or payload dict")

        if debug:
            print("[Tag_Sampler] ===== Debug Enabled =====")
            print(f"[Tag_Sampler] Source path: {metadata.resolved_path}")
            print(f"[Tag_Sampler] min_count={min_count}, max_count={max_count}")
            print(f"[Tag_Sampler] per_category={per_category}")
            print(f"[Tag_Sampler] category_list={category_list}")

        if min_count < 0:
            min_count = 0
        if max_count < 0:
            max_count = 0
        if min_count > max_count:
            min_count, max_count = max_count, min_count

        selected_categories = self._select_categories(
            metadata,
            tag_selection,
            category_list,
        )
        if not selected_categories and tag_selection is None and not category_list:
            if isinstance(metadata, dict):
                selected_categories = list(metadata.get("categories", []))
            else:
                selected_categories = list(metadata.categories)
        if debug:
            print(f"[Tag_Sampler] Using categories: {selected_categories}")

        if seed != 0:
            rand_module.seed(seed)

        if per_category:
            # Sample min_count to max_count tags from each category
            all_chosen = []
            for category in selected_categories:
                if isinstance(metadata, dict):
                    category_tags = metadata.get("tags_by_category", {}).get(category, [])
                else:
                    category_tags = metadata.tags_by_category.get(category, [])
                if not category_tags:
                    if debug:
                        print(f"[Tag_Sampler] No tags in category '{category}', skipping.")
                    continue
                
                if unique_only:
                    available = list(category_tags)
                else:
                    repetitions = max(1, max_count // max(1, len(category_tags)) + 1)
                    available = category_tags * repetitions

                upper = min(max_count, len(available)) if unique_only else max_count
                lower = min(min_count, len(available)) if unique_only else min_count
                k = rand_module.randint(lower, upper) if upper >= lower else 0

                if debug:
                    print(f"[Tag_Sampler] Category '{category}': {len(category_tags)} tags, sampling {k}")

                if k > 0:
                    if unique_only:
                        category_chosen = rand_module.sample(available, k)
                    else:
                        category_chosen = [rand_module.choice(available) for _ in range(k)]
                    all_chosen.extend(category_chosen)

            chosen = all_chosen
        else:
            # Original behavior: sample from all categories combined
            tags = self._gather_candidate_tags(metadata, selected_categories)
            if not tags:
                if debug:
                    print("[Tag_Sampler] No tags available after selection.")
                return ("", 0, [])

            if unique_only:
                available = list(tags)
            else:
                repetitions = max(1, max_count // max(1, len(tags)) + 1)
                available = tags * repetitions

            upper = min(max_count, len(available)) if unique_only else max_count
            lower = min(min_count, len(available)) if unique_only else min_count
            k = rand_module.randint(lower, upper) if upper >= lower else 0

            if debug:
                print(
                    f"[Tag_Sampler] Candidate tags (unique={unique_only}): "
                    f"{len(available)} available -> {available}"
                )
                print(f"[Tag_Sampler] Sampling k between [{lower}, {upper}] => {k}")

            if k <= 0:
                if debug:
                    print("[Tag_Sampler] k <= 0, returning empty result.")
                return ("", 0, [])

            if unique_only:
                chosen = rand_module.sample(available, k)
            else:
                chosen = [rand_module.choice(available) for _ in range(k)]

        if not chosen:
            if debug:
                print("[Tag_Sampler] No tags chosen, returning empty result.")
            return ("", 0, [])

        result = ", ".join(chosen)
        if debug:
            print(f"[Tag_Sampler] Chosen tags: {chosen}")
            print(f"[Tag_Sampler] Result: '{result}' (count={len(chosen)})")
        return (result, len(chosen), chosen)
