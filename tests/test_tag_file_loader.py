import os
import tempfile
import unittest

from nodes.tag_file_loader import ICHIS_Tag_File_Loader


class TestTagFileLoader(unittest.TestCase):
    def setUp(self):
        ICHIS_Tag_File_Loader.clear_cache()
        self.node = ICHIS_Tag_File_Loader()

    def _write_temp(self, suffix: str, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix, text=True)
        os.close(fd)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def test_loads_csv_metadata(self):
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "faces,blue eyes\n"
            "hair,blonde hair\n"
        )
        path = self._write_temp(".csv", csv_content)
        try:
            metadata, categories, all_tags, resolved, cache_hit = self.node.load_tags(
                file_path=path,
                ignore_case=True,
            )
            self.assertFalse(cache_hit)
            self.assertEqual(resolved, path)
            self.assertListEqual(categories, ["faces", "hair"])
            self.assertListEqual(sorted(all_tags), ["blonde hair", "blue eyes", "smile"])
            self.assertEqual(metadata["source_type"], "csv")
            # Cache should hit on second call
            metadata2, _, _, _, cache_hit2 = self.node.load_tags(file_path=path)
            self.assertTrue(cache_hit2)
            self.assertEqual(metadata2["cache_signature"], metadata["cache_signature"])
        finally:
            os.remove(path)

    def test_loads_json_metadata(self):
        json_content = (
            "[\n"
            "  {\"category\": \"faces\", \"tags\": [\"smile\", \"wink\"]},\n"
            "  {\"category\": \"hair\", \"tags\": \"blonde hair; short hair\"}\n"
            "]"
        )
        path = self._write_temp(".json", json_content)
        try:
            metadata, categories, all_tags, resolved, cache_hit = self.node.load_tags(
                file_path=path,
                ignore_case=True,
            )
            self.assertFalse(cache_hit)
            self.assertEqual(resolved, path)
            self.assertListEqual(categories, ["faces", "hair"])
            self.assertIn("short hair", all_tags)
            self.assertEqual(metadata["source_type"], "json")
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
