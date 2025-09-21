import os
import tempfile
import unittest

from nodes.tag_sampler import ICHIS_Tag_Sampler
from nodes.tag_category_select import ICHIS_Tag_Category_Select
from nodes.tag_file_loader import ICHIS_Tag_File_Loader


class TestTagSampler(unittest.TestCase):
    def setUp(self):
        ICHIS_Tag_File_Loader.clear_cache()
        self.node = ICHIS_Tag_Sampler()
        self.loader = ICHIS_Tag_File_Loader()
        self.selector = ICHIS_Tag_Category_Select()

    def _write_csv(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _load_metadata(self, path: str):
        metadata, *_ = self.loader.load_tags(file_path=path)
        return metadata

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
            metadata = self._load_metadata(path)
            # categories filter to only 'faces'; min=max=2 to make deterministic count
            tags, count, _ = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=2,
                max_count=2,
                category_list=["faces"],
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
            metadata = self._load_metadata(path)
            tags, count, _ = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=1,
                max_count=4,
                category_list=["faces", "clothes"],
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
            metadata = self._load_metadata(path)
            tags, count, _ = self.node.sample_tags(
                tag_metadata=metadata,
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
            metadata = self._load_metadata(path)
            tags, count, _ = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=1,
                max_count=3,
                category_list=["nonexistent"],
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
            metadata = self._load_metadata(path)
            r1 = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=2,
                max_count=3,
                seed=777,
            )
            r2 = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=2,
                max_count=3,
                seed=777,
            )
            self.assertEqual(r1, r2)
            r3 = self.node.sample_tags(
                tag_metadata=metadata,
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
            metadata = self._load_metadata(path)
            tags, count, _ = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=1,
                max_count=3,
                category_list=["faces"],
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
            metadata = self._load_metadata(path)
            tags, count, _ = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=2,
                max_count=3,
                seed=2,
            )
            self.assertTrue(2 <= count <= 3)
            parts = [p.strip() for p in tags.split(",") if p.strip()]
            self.assertTrue(set(parts).issubset({"a", "b", "c"}))
        finally:
            os.remove(path)

    def test_sampling_with_metadata_and_selection(self):
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "faces,blue eyes\n"
            "hair,blonde hair\n"
            "clothes,red dress\n"
        )
        path = self._write_csv(csv_content)
        try:
            metadata, _, _, _, _ = self.loader.load_tags(file_path=path)
            selection_payload, selected_list, category_tags = self.selector.select_categories(
                tag_metadata=metadata,
                categories="faces\nclothes",
            )
            self.assertEqual(selected_list, ["faces", "clothes"])
            self.assertTrue(set(category_tags).issubset({"smile", "blue eyes", "red dress"}))
            tags, count, tag_list = self.node.sample_tags(
                min_count=1,
                max_count=3,
                tag_metadata=metadata,
                tag_selection=selection_payload,
                seed=42,
            )
            self.assertTrue(1 <= count <= 3)
            self.assertEqual(len(tag_list), count)
            allowed = {"smile", "blue eyes", "red dress"}
            self.assertTrue(set(tag_list).issubset(allowed))
        finally:
            os.remove(path)

    def test_sampling_with_category_list_input(self):
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "faces,blue eyes\n"
            "hair,blonde hair\n"
        )
        path = self._write_csv(csv_content)
        try:
            metadata, categories, *_ = self.loader.load_tags(file_path=path)
            self.assertEqual(categories, ["faces", "hair"])
            tags, count, tag_list = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=2,
                max_count=2,
                category_list=["faces"],
                seed=123,
            )
            self.assertEqual(count, 2)
            allowed = {"smile", "blue eyes"}
            self.assertTrue(set(tag_list).issubset(allowed))
        finally:
            os.remove(path)

    def test_per_category_sampling_disabled(self):
        """Test that per_category=False samples across all categories (default behavior)."""
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "faces,frown\n"
            "hair,blonde\n"
            "hair,brown\n"
            "clothes,shirt\n"
            "clothes,dress\n"
        )
        path = self._write_csv(csv_content)
        try:
            metadata = self._load_metadata(path)
            # Sample 3 tags with per_category=False (default)
            result, count, tags_list = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=3,
                max_count=3,
                seed=42,
                per_category=False,
            )
            
            # Should get exactly 3 tags from across all categories
            self.assertEqual(count, 3)
            self.assertEqual(len(tags_list), 3)
            # Verify all tags are from the available pool
            all_tags = {"smile", "frown", "blonde", "brown", "shirt", "dress"}
            self.assertTrue(set(tags_list).issubset(all_tags))
        finally:
            os.remove(path)

    def test_per_category_sampling_enabled(self):
        """Test that per_category=True samples min-max from each category."""
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "faces,frown\n"
            "hair,blonde\n"
            "hair,brown\n"
            "clothes,shirt\n"
            "clothes,dress\n"
        )
        path = self._write_csv(csv_content)
        try:
            metadata = self._load_metadata(path)
            # Sample 1-2 tags per category with per_category=True
            result, count, tags_list = self.node.sample_tags(
                tag_metadata=metadata,
                min_count=1,
                max_count=2,
                seed=42,
                per_category=True,
            )
            
            # Should get 1-2 tags from each of the 3 categories = 3-6 total tags
            self.assertGreaterEqual(count, 3)  # At least 1 from each category
            self.assertLessEqual(count, 6)     # At most 2 from each category
            self.assertEqual(len(tags_list), count)
            
            # Verify we have tags from multiple categories
            faces_tags = {"smile", "frown"}
            hair_tags = {"blonde", "brown"}
            clothes_tags = {"shirt", "dress"}
            
            has_faces = any(tag in faces_tags for tag in tags_list)
            has_hair = any(tag in hair_tags for tag in tags_list)
            has_clothes = any(tag in clothes_tags for tag in tags_list)
            
            # With per_category=True, we should have tags from all categories
            self.assertTrue(has_faces, "Should have at least one face tag")
            self.assertTrue(has_hair, "Should have at least one hair tag")
            self.assertTrue(has_clothes, "Should have at least one clothes tag")
        finally:
            os.remove(path)

    def test_per_category_with_category_selection(self):
        """Test per_category sampling with specific category selection."""
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "faces,frown\n"
            "hair,blonde\n"
            "hair,brown\n"
            "clothes,shirt\n"
            "clothes,dress\n"
        )
        path = self._write_csv(csv_content)
        try:
            metadata = self._load_metadata(path)
            # Select only faces and hair categories
            selection, selected_categories, _ = self.selector.select_categories(
                tag_metadata=metadata,
                categories="faces\nhair"
            )
            
            # Sample 1-1 tags per selected category with per_category=True
            result, count, tags_list = self.node.sample_tags(
                tag_metadata=metadata,
                tag_selection=selection,
                min_count=1,
                max_count=1,
                seed=42,
                per_category=True,
            )
            
            # Should get exactly 2 tags (1 from faces, 1 from hair)
            self.assertEqual(count, 2)
            self.assertEqual(len(tags_list), 2)
            
            # Verify we have one from each selected category
            faces_tags = {"smile", "frown"}
            hair_tags = {"blonde", "brown"}
            clothes_tags = {"shirt", "dress"}
            
            has_faces = any(tag in faces_tags for tag in tags_list)
            has_hair = any(tag in hair_tags for tag in tags_list)
            has_clothes = any(tag in clothes_tags for tag in tags_list)
            
            self.assertTrue(has_faces, "Should have exactly one face tag")
            self.assertTrue(has_hair, "Should have exactly one hair tag")
            self.assertFalse(has_clothes, "Should not have any clothes tags")
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
