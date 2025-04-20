import unittest
from nodes.extract_tags import ICHIS_Extract_Tags

class TestExtractTags(unittest.TestCase):
    def setUp(self):
        self.node = ICHIS_Extract_Tags()
    
    def test_basic_extraction(self):
        # Test basic extraction with single concept
        text = "woman, beautiful eyes, big blue eyes, crossing eyes and looking up, red lips, tall, running down beach"
        concepts = "eyes"
        delimiter = ", "
        
        result = self.node.extract_text(text, concepts, delimiter)[0]
        expected = "beautiful eyes, big blue eyes, crossing eyes and looking up"
        self.assertEqual(result, expected)
    
    def test_multiple_concepts(self):
        # Test extraction with multiple concepts
        text = "woman, beautiful eyes, big blue eyes, crossing eyes and looking up, red lips, tall, running down beach"
        concepts = "eyes\nlips"
        delimiter = ", "
        
        result = self.node.extract_text(text, concepts, delimiter)[0]
        expected = "beautiful eyes, big blue eyes, crossing eyes and looking up, red lips"
        self.assertEqual(result, expected)
    
    def test_case_insensitivity(self):
        # Test case-insensitive matching
        text = "woman, Beautiful Eyes, BIG BLUE EYES, crossing eyes and looking up, RED LIPS, tall, running down beach"
        concepts = "EYES\nLIPS"
        delimiter = ", "
        
        result = self.node.extract_text(text, concepts, delimiter)[0]
        expected = "Beautiful Eyes, BIG BLUE EYES, crossing eyes and looking up, RED LIPS"
        self.assertEqual(result, expected)
    
    def test_custom_delimiter(self):
        # Test custom delimiter
        text = "woman, beautiful eyes, big blue eyes, crossing eyes and looking up, red lips, tall, running down beach"
        concepts = "eyes\nlips"
        delimiter = " | "
        
        result = self.node.extract_text(text, concepts, delimiter)[0]
        expected = "beautiful eyes | big blue eyes | crossing eyes and looking up | red lips"
        self.assertEqual(result, expected)
    
    def test_empty_inputs(self):
        # Test empty inputs
        text = ""
        concepts = ""
        delimiter = ", "
        
        result = self.node.extract_text(text, concepts, delimiter)[0]
        self.assertEqual(result, "")
    
    def test_no_matches(self):
        # Test when no matches are found
        text = "woman, beautiful eyes, big blue eyes, crossing eyes and looking up, red lips, tall, running down beach"
        concepts = "nose"
        delimiter = ", "
        
        result = self.node.extract_text(text, concepts, delimiter)[0]
        self.assertEqual(result, "")
    
    def test_whitespace_handling(self):
        # Test handling of extra whitespace
        text = "woman,  beautiful eyes  , big blue eyes, crossing eyes and looking up,  red lips  , tall, running down beach"
        concepts = "  eyes  \n  lips  "
        delimiter = ", "
        
        result = self.node.extract_text(text, concepts, delimiter)[0]
        expected = "beautiful eyes, big blue eyes, crossing eyes and looking up, red lips"
        self.assertEqual(result, expected)
    
    def test_partial_matches(self):
        # Test when some concepts match and others don't
        text = "woman, beautiful eyes, big blue eyes, crossing eyes and looking up, red lips, tall, running down beach"
        concepts = "eyes\nlook\nlooking"
        delimiter = ", "
        
        result = self.node.extract_text(text, concepts, delimiter)[0]
        expected = "beautiful eyes, big blue eyes, crossing eyes and looking up"
        self.assertEqual(result, expected)

    def test_complex_character_description(self):
        # Test extraction from a complex character description
        text = "Tink, blonde hair, single hair bun, big blue eyes, rosy cheeks, fairy wings, emo, purple hair, bored look, silk choker, dark purple sweater, purple skirt"
        concepts = "eyes\nlooking\nlook\nskin\nface"
        result = self.node.extract_text(text, concepts, ", ")
        self.assertEqual(result[0], "big blue eyes, bored look")

    def test_comma_separated_concepts(self):
        # Test extraction with comma-separated concepts
        text = "Tink, blonde hair, single hair bun, big blue eyes, rosy cheeks, fairy wings, emo, purple hair, bored look, silk choker, dark purple sweater, purple skirt"
        concepts = "eyes, looking, look, skin, face"  # Comma-separated instead of newline
        result = self.node.extract_text(text, concepts, ", ")
        self.assertEqual(result[0], "big blue eyes, bored look")

    def test_mixed_separator_concepts(self):
        # Test extraction with both comma and newline separated concepts
        text = "woman, beautiful eyes, big blue eyes, crossing eyes and looking up, red lips, tall, running down beach"
        concepts = "eyes, looking\nlips, tall"  # Mix of comma and newline separators
        result = self.node.extract_text(text, concepts, ", ")
        self.assertEqual(result[0], "beautiful eyes, big blue eyes, crossing eyes and looking up, red lips, tall")

if __name__ == '__main__':
    unittest.main() 