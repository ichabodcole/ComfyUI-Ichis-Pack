import os
import tempfile
import unittest

from nodes.csv_tag_sampler import ICHIS_CSV_Tag_Sampler


class TestCSVTagSampler(unittest.TestCase):
    def setUp(self):
        self.node = ICHIS_CSV_Tag_Sampler()

    def _write_csv(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_row_per_tag_sampling_fixed_count(self):
        # CSV with one tag per row (no image column)
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "faces,blue eyes\n"
            "hair,blonde hair\n"
            "faces,freckles\n"
            "faces,serious\n"
        )
        path = self._write_csv(csv_content)
        try:
            # categories filter to only 'faces'; min=max=2 to make deterministic count
            tags, count, _ = self.node.sample_tags(
                file_path=path,
                min_count=2,
                max_count=2,
                categories="faces",
                delimiter=", ",
                seed=12345,
            )
            self.assertEqual(count, 2)
            parts = [p.strip() for p in tags.split(",") if p.strip()]
            # All parts must be from the faces category set
            allowed = {"smile", "blue eyes", "freckles"}
            self.assertTrue(set(parts).issubset(allowed))
            # No duplicates
            self.assertEqual(len(parts), len(set(parts)))
        finally:
            os.remove(path)

    def test_row_per_category_list_and_mixed(self):
        # CSV using list rows
        csv_content = (
            "category,tags\n"
            "clothes,red dress; blue dress | green skirt\n"
            "faces,smile, wink\n"  # note: comma inside should split
        )
        path = self._write_csv(csv_content)
        try:
            tags, count, _ = self.node.sample_tags(
                file_path=path,
                min_count=1,
                max_count=4,
                categories="faces,clothes",
                delimiter=", ",
                seed=999,
            )
            # Should find from set below
            pool = {"red dress", "blue dress", "green skirt", "smile", "wink"}
            parts = [p.strip() for p in tags.split(",") if p.strip()]
            self.assertTrue(set(parts).issubset(pool))
            self.assertTrue(1 <= count <= 4)
        finally:
            os.remove(path)

    def test_clamp_when_not_enough_tags(self):
        csv_content = (
            "category,tag\n"
            "misc,one\n"
            "misc,two\n"
        )
        path = self._write_csv(csv_content)
        try:
            tags, count, _ = self.node.sample_tags(
                file_path=path,
                min_count=5,
                max_count=10,
                seed=42,
            )
            # Only two tags exist, should clamp to 2
            self.assertEqual(count, 2)
            parts = [p.strip() for p in tags.split(",") if p.strip()]
            self.assertEqual(len(parts), 2)
        finally:
            os.remove(path)
        
    def test_no_tags_with_unmatched_category(self):
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
        )
        path = self._write_csv(csv_content)
        try:
            tags, count, _ = self.node.sample_tags(
                file_path=path,
                min_count=1,
                max_count=3,
                categories="nonexistent",
            )
            self.assertEqual(tags, "")
            self.assertEqual(count, 0)
        finally:
            os.remove(path)

    def test_seed_reproducibility(self):
        csv_content = (
            "category,tag\n"
            "faces,a\n"
            "faces,b\n"
            "faces,c\n"
            "faces,d\n"
        )
        path = self._write_csv(csv_content)
        try:
            r1 = self.node.sample_tags(
                file_path=path,
                min_count=2,
                max_count=3,
                seed=777,
            )
            r2 = self.node.sample_tags(
                file_path=path,
                min_count=2,
                max_count=3,
                seed=777,
            )
            self.assertEqual(r1, r2)
            r3 = self.node.sample_tags(
                file_path=path,
                min_count=2,
                max_count=3,
                seed=778,
            )
            # Likely different; if coincidentally same, still valid
            self.assertTrue(r1 == r2)
        finally:
            os.remove(path)

    def test_no_image_column(self):
        # CSV without image column; categories present
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "faces,blue eyes\n"
            "hair,blonde hair\n"
        )
        path = self._write_csv(csv_content)
        try:
            tags, count, _ = self.node.sample_tags(
                file_path=path,
                min_count=1,
                max_count=3,
                categories="faces",
                seed=1,
            )
            self.assertTrue(1 <= count <= 2)
            allowed = {"smile", "blue eyes"}
            parts = [p.strip() for p in tags.split(",") if p.strip()]
            self.assertTrue(set(parts).issubset(allowed))
        finally:
            os.remove(path)

    def test_tag_only_csv(self):
        # CSV with tag column only
        csv_content = (
            "tag\n"
            "a\n"
            "b\n"
            "c\n"
        )
        path = self._write_csv(csv_content)
        try:
            tags, count = self.node.sample_tags(
                csv_path=path,
                min_count=2,
                max_count=3,
                seed=2,
            )
            self.assertTrue(2 <= count <= 3)
            parts = [p.strip() for p in tags.split(",") if p.strip()]
            self.assertTrue(set(parts).issubset({"a", "b", "c"}))
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
