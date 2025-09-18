import os
import json
import time
import uuid
from typing import List


class ICHIS_Save_Tags:
    """
    Save tags to a file when triggered via a toggle.

    Supports two formats:
    - txt: writes the joined string (with delimiter), plus newline.
    - jsonl: appends a JSON object per line: {"tags": [...], "tags_str": str, "timestamp": float}
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"placeholder": "Where to save (e.g., /path/to/tags.jsonl or .txt)"}),
                "tags": ("STRING", {"multiline": True, "default": ""}),
                "tags_list": ("LIST", {}),
                "format": (["txt", "jsonl"], {"default": "jsonl"}),
            },
            "optional": {
                "delimiter": ("STRING", {"default": ", ", "placeholder": "Used for txt format"}),
                "append": ("BOOLEAN", {"default": True}),
                "ensure_dir": ("BOOLEAN", {"default": True}),
                "save_now": ("BOOLEAN", {"default": False}),
                "debug": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "STRING")
    RETURN_NAMES = ("saved", "path")
    FUNCTION = "save"
    CATEGORY = "ICHIS"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Trigger re-run on save_now True to enable one-click save semantics
        if kwargs.get("save_now", False):
            return f"save_{time.time()}_{uuid.uuid4()}"
        return None

    def _ensure_dir(self, path: str, ensure: bool, debug: bool):
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            if ensure:
                if debug:
                    print(f"[Save_Tags] Creating directory: {d}")
                os.makedirs(d, exist_ok=True)

    def save(self, file_path: str, tags: str, tags_list: List[str], format: str = "jsonl",
             delimiter: str = ", ", append: bool = True, ensure_dir: bool = True,
             save_now: bool = False, debug: bool = False):
        if debug:
            print("[Save_Tags] ===== Debug Enabled =====")
            print(f"[Save_Tags] file_path: {file_path}")
            print(f"[Save_Tags] format: {format}, append: {append}")
            print(f"[Save_Tags] tags_list({len(tags_list)}): {tags_list}")
            print(f"[Save_Tags] tags_str: '{tags}'")
            print(f"[Save_Tags] save_now: {save_now}")

        if not save_now:
            if debug:
                print("[Save_Tags] save_now is False; skipping write.")
            return (False, file_path)

        if not file_path:
            if debug:
                print("[Save_Tags] No file_path provided; skipping write.")
            return (False, file_path)

        self._ensure_dir(file_path, ensure_dir, debug)

        mode = "a" if append else "w"
        try:
            if format == "txt":
                line = tags if tags is not None else (delimiter.join(tags_list) if tags_list else "")
                with open(file_path, mode, encoding="utf-8") as f:
                    f.write(line + "\n")
            else:  # jsonl
                record = {
                    "tags": list(tags_list or []),
                    "tags_str": tags if tags is not None else "",
                    "timestamp": time.time(),
                }
                with open(file_path, mode, encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            if debug:
                print(f"[Save_Tags] Saved to {file_path}")
            return (True, file_path)
        except Exception as e:
            if debug:
                print(f"[Save_Tags] Error saving to {file_path}: {e}")
            return (False, file_path)

