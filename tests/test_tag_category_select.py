import os
import tempfile
import unittest

from nodes.tag_category_select import ICHIS_Tag_Category_Select
from nodes.tag_file_loader import ICHIS_Tag_File_Loader


class TestTagCategorySelect(unittest.TestCase):
    def setUp(self):
        ICHIS_Tag_File_Loader.clear_cache()
        self.loader = ICHIS_Tag_File_Loader()
        self.selector = ICHIS_Tag_Category_Select()

    def _write_csv(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def test_manual_selection_filters_categories(self):
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "hair,blonde hair\n"
            "clothes,red dress\n"
        )
        path = self._write_csv(csv_content)
        try:
            metadata, categories, *_ = self.loader.load_tags(file_path=path)
            (
                selection,
                selected_list,
                category_tags,
            ) = self.selector.select_categories(
                tag_metadata=metadata,
                categories="faces\nclothes",
            )
            self.assertEqual(selected_list, ["faces", "clothes"])
            self.assertEqual(selection["selected_categories"], ["faces", "clothes"])
            self.assertListEqual(selection["category_tags"], category_tags)
            self.assertTrue(set(category_tags).issubset({"smile", "red dress"}))
        finally:
            os.remove(path)

    def test_empty_selection_returns_empty_list(self):
        """Test that empty category selection returns empty list (no auto-defaulting)."""
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "hair,blonde hair\n"
        )
        path = self._write_csv(csv_content)
        try:
            metadata, categories, *_ = self.loader.load_tags(file_path=path)
            _, selected_list, category_tags = self.selector.select_categories(
                tag_metadata=metadata,
            )
            # After removing auto-defaulting behavior, empty selection should return empty list
            self.assertEqual(selected_list, [])
            self.assertEqual(category_tags, [])
        finally:
            os.remove(path)

    def test_allow_empty_true_with_empty_selection(self):
        """Test that allow_empty=True works correctly with empty selection."""
        csv_content = (
            "category,tag\n"
            "faces,smile\n"
            "hair,blonde hair\n"
        )
        path = self._write_csv(csv_content)
        try:
            metadata, categories, *_ = self.loader.load_tags(file_path=path)
            _, selected_list, category_tags = self.selector.select_categories(
                tag_metadata=metadata,
                allow_empty=True,
            )
            # With allow_empty=True, empty selection should still return empty list
            self.assertEqual(selected_list, [])
            self.assertEqual(category_tags, [])
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
