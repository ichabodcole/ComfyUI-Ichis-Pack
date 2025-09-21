import os
import json
import tempfile
import unittest

from nodes.tag_sampler import ICHIS_Tag_Sampler
from nodes.tag_file_loader import ICHIS_Tag_File_Loader


class TestCSVTagSamplerJSON(unittest.TestCase):
    def setUp(self):
        self.node = ICHIS_Tag_Sampler()
        self.loader = ICHIS_Tag_File_Loader()

    def _write_json(self, data) -> str:
        fd, path = tempfile.mkstemp(suffix=".json", text=True)
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_basic_json_sampling(self):
        data = [
            {"category": "faces", "tags": ["smile", "blue eyes"]},
            {"category": "hair", "tags": ["blonde hair", "bangs"]},
        ]
        path = self._write_json(data)
        try:
            metadata, _, _, _, _ = self.loader.load_tags(file_path=path)
            tags, count, tags_list = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=1,
                max_count=3,
                category_list=["faces", "hair"],
                seed=123,
            )
            parts = [p.strip() for p in tags.split(",") if p.strip()]
            self.assertTrue(1 <= count <= 3)
            self.assertTrue(set(parts).issubset({"smile", "blue eyes", "blonde hair", "bangs"}))
            # Typed list should match count and allowed pool
            self.assertIsInstance(tags_list, list)
            self.assertEqual(len(tags_list), count)
            self.assertTrue(set(tags_list).issubset({"smile", "blue eyes", "blonde hair", "bangs"}))
        finally:
            os.remove(path)

    def test_json_string_tags_field(self):
        data = [
            {"category": "clothes", "tags": "red dress; blue shirt | green skirt"},
        ]
        path = self._write_json(data)
        try:
            metadata, _, _, _, _ = self.loader.load_tags(file_path=path)
            tags, count, tags_list = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=2,
                max_count=3,
                category_list=["clothes"],
                seed=9,
            )
            parts = [p.strip() for p in tags.split(",") if p.strip()]
            self.assertTrue(2 <= count <= 3)
            self.assertTrue(set(parts).issubset({"red dress", "blue shirt", "green skirt"}))
            self.assertIsInstance(tags_list, list)
            self.assertEqual(len(tags_list), count)
            self.assertTrue(set(tags_list).issubset({"red dress", "blue shirt", "green skirt"}))
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
