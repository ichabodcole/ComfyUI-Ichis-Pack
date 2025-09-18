import os
import json
import tempfile
import unittest

from nodes.save_tags import ICHIS_Save_Tags


class TestSaveTags(unittest.TestCase):
    def setUp(self):
        self.node = ICHIS_Save_Tags()

    def test_skip_when_not_triggered(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            saved, out_path = self.node.save(
                file_path=path,
                tags="a, b",
                tags_list=["a", "b"],
                format="jsonl",
                save_now=False,
            )
            self.assertFalse(saved)
            self.assertEqual(out_path, path)
        finally:
            os.remove(path)

    def test_save_jsonl(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            saved, out_path = self.node.save(
                file_path=path,
                tags="a, b",
                tags_list=["a", "b"],
                format="jsonl",
                save_now=True,
                append=False,
            )
            self.assertTrue(saved)
            with open(path, "r", encoding="utf-8") as f:
                line = f.readline().strip()
                obj = json.loads(line)
                self.assertEqual(obj.get("tags"), ["a", "b"]) 
        finally:
            os.remove(path)

    def test_save_txt(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            saved, out_path = self.node.save(
                file_path=path,
                tags="x | y | z",
                tags_list=["x", "y", "z"],
                format="txt",
                save_now=True,
                append=False,
            )
            self.assertTrue(saved)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                self.assertEqual(content, "x | y | z")
        finally:
            os.remove(path)


if __name__ == '__main__':
    unittest.main()

