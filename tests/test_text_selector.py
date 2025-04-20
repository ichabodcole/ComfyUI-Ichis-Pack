import unittest
from nodes.text_selector import ICHIS_Text_Selector

class TestTextSelector(unittest.TestCase):
    def setUp(self):
        self.node = ICHIS_Text_Selector()
        # Reset the step index before each test
        ICHIS_Text_Selector.current_step_index = 0
    
    def test_normal_mode(self):
        # Test normal mode selection
        text = "@1 First text\n@2 Second text\n@3 Third text"
        result = self.node.select_text(text, mode="normal", index=2)
        self.assertEqual(result, ("Second text", 2))
    
    def test_step_mode(self):
        # Test step mode progression
        text = "@1 First text\n@2 Second text\n@3 Third text"
        
        # First step
        result1 = self.node.select_text(text, mode="step")
        self.assertEqual(result1, ("First text", 1))
        
        # Second step
        result2 = self.node.select_text(text, mode="step")
        self.assertEqual(result2, ("Second text", 2))
        
        # Third step
        result3 = self.node.select_text(text, mode="step")
        self.assertEqual(result3, ("Third text", 3))
        
        # Fourth step (should wrap around)
        result4 = self.node.select_text(text, mode="step")
        self.assertEqual(result4, ("First text", 1))
    
    def test_step_mode_reset(self):
        # Test step mode reset
        text = "@1 First text\n@2 Second text\n@3 Third text"
        
        # Take a step
        self.node.select_text(text, mode="step")
        
        # Reset and verify it goes back to first item
        result = self.node.select_text(text, mode="step", reset_step=True)
        self.assertEqual(result, ("First text", 1))
    
    def test_random_mode(self):
        # Test random mode with seed
        text = "@1 First text\n@2 Second text\n@3 Third text"
        
        # With same seed, should get same result
        result1 = self.node.select_text(text, mode="random", seed=42)
        result2 = self.node.select_text(text, mode="random", seed=42)
        self.assertEqual(result1, result2)
        
        # With different seed, should get different result
        result3 = self.node.select_text(text, mode="random", seed=43)
        self.assertNotEqual(result1, result3)
    
    def test_index_bounds(self):
        # Test index bounds handling
        text = "@1 First text\n@2 Second text\n@3 Third text"
        
        # Test index too low
        result_low = self.node.select_text(text, mode="normal", index=0)
        self.assertEqual(result_low, ("First text", 1))
        
        # Test index too high
        result_high = self.node.select_text(text, mode="normal", index=4)
        self.assertEqual(result_high, ("Third text", 3))
    
    def test_empty_input(self):
        # Test empty input handling
        result = self.node.select_text("", mode="normal")
        self.assertEqual(result, ("", 0))
    
    def test_no_markers(self):
        # Test text without @ markers
        text = "First text\nSecond text\nThird text"
        result = self.node.select_text(text, mode="normal", index=1)
        self.assertEqual(result, (text.strip(), 1))
    
    def test_exclude_indices(self):
        # Test exclusion functionality with minus prefix
        text = "@1 First text\n@2 Second text\n@3 Third text\n@4 Fourth text"
        
        # Exclude indices 1 and 3
        result = self.node.select_text(
            text, 
            mode="normal", 
            index=2,
            filter_indices="-[1,3]"
        )
        self.assertEqual(result, ("Second text", 2))
        
        # Test step mode with excluded indices
        result_step = self.node.select_text(
            text,
            mode="step",
            filter_indices="-[1,3]"
        )
        self.assertEqual(result_step, ("Second text", 2))
        
    def test_include_indices(self):
        # Test inclusion functionality with plus prefix
        text = "@1 First text\n@2 Second text\n@3 Third text\n@4 Fourth text"
        
        # Include only indices 2 and 4
        result = self.node.select_text(
            text, 
            mode="normal", 
            index=2,
            filter_indices="+[2,4]"
        )
        self.assertEqual(result, ("Second text", 2))
        
        # Test step mode with included indices
        self.node.current_step_index = 0
        result_step1 = self.node.select_text(
            text,
            mode="step",
            filter_indices="+[2,4]"
        )
        self.assertEqual(result_step1, ("Second text", 2))
        
        # Second step
        result_step2 = self.node.select_text(
            text,
            mode="step",
            filter_indices="+[2,4]"
        )
        self.assertEqual(result_step2, ("Fourth text", 4))
        
        # Third step (should wrap around)
        result_step3 = self.node.select_text(
            text,
            mode="step",
            filter_indices="+[2,4]"
        )
        self.assertEqual(result_step3, ("Second text", 2))
        
    def test_implicit_inclusion(self):
        # Test implicit inclusion (no + prefix)
        text = "@1 First text\n@2 Second text\n@3 Third text\n@4 Fourth text"
        
        # Include only indices 1 and 3
        result = self.node.select_text(
            text, 
            mode="normal", 
            index=3,
            filter_indices="[1,3]"
        )
        self.assertEqual(result, ("Third text", 3))
        
    def test_closest_index_selection(self):
        # Test that in normal mode, if selected index isn't available, it chooses closest one
        text = "@1 First text\n@2 Second text\n@3 Third text\n@4 Fourth text\n@5 Fifth text"
        
        # Include only indices 1, 3, 5
        # Asking for index 2 should return index 1 or 3 (closest)
        result = self.node.select_text(
            text, 
            mode="normal", 
            index=2,
            filter_indices="+[1,3,5]"
        )
        # Should choose either 1 or 3 as they're equally close to 2
        self.assertTrue(result[1] in [1, 3])
        
        # Include only indices 1, 5
        # Asking for index 4 should return index 5 (closest)
        result = self.node.select_text(
            text, 
            mode="normal", 
            index=4,
            filter_indices="+[1,5]"
        )
        self.assertEqual(result[1], 5)
        
    def test_exclude_indices_range_notation(self):
        # Test exclude_indices with range notation
        text = "@1 First text\n@2 Second text\n@3 Third text\n@4 Fourth text\n@5 Fifth text\n@6 Sixth text"
        
        # Test simple range notation
        result_range = self.node.select_text(
            text, 
            mode="normal", 
            index=1,
            filter_indices="-[2-4]"
        )
        # Should exclude indices 2, 3, 4, so available indices are 1, 5, 6
        # With index=1, should select First text
        self.assertEqual(result_range, ("First text", 1))
        
        # Test mixed notation
        result_mixed = self.node.select_text(
            text, 
            mode="normal", 
            index=6,
            filter_indices="-[1,3-5]"
        )
        # Should exclude indices 1, 3, 4, 5, so available indices are 2, 6
        # With index=6, should select Sixth text
        self.assertEqual(result_mixed, ("Sixth text", 6))
        
        # Test step mode with range exclusion
        # Set up test with exclusions 2-5
        self.node.current_step_index = 0
        result_step1 = self.node.select_text(
            text,
            mode="step",
            filter_indices="-[2-5]"
        )
        # First step should give first item
        self.assertEqual(result_step1, ("First text", 1))
        
        # Second step should give sixth item
        result_step2 = self.node.select_text(
            text,
            mode="step",
            filter_indices="-[2-5]"
        )
        self.assertEqual(result_step2, ("Sixth text", 6))
        
        # Third step should wrap around to first item
        result_step3 = self.node.select_text(
            text,
            mode="step",
            filter_indices="-[2-5]"
        )
        self.assertEqual(result_step3, ("First text", 1))
        
    def test_include_indices_range_notation(self):
        # Test include_indices with range notation
        text = "@1 First text\n@2 Second text\n@3 Third text\n@4 Fourth text\n@5 Fifth text\n@6 Sixth text"
        
        # Test simple range notation
        result_range = self.node.select_text(
            text, 
            mode="normal", 
            index=2,
            filter_indices="+[1-3]"
        )
        # Should include only indices 1, 2, 3
        # With index=2, should select Second text
        self.assertEqual(result_range, ("Second text", 2))
        
        # Test mixed notation
        result_mixed = self.node.select_text(
            text, 
            mode="normal", 
            index=4,
            filter_indices="+[1,3-5]"
        )
        # Should include indices 1, 3, 4, 5
        # With index=4, it should select the Fourth text
        self.assertEqual(result_mixed, ("Fourth text", 4))
        
        # Test step mode with range inclusion
        # Set up test with inclusions 1,6
        self.node.current_step_index = 0
        result_step1 = self.node.select_text(
            text,
            mode="step",
            filter_indices="+[1,6]"
        )
        # First step should give first item
        self.assertEqual(result_step1, ("First text", 1))
        
        # Second step should give sixth item
        result_step2 = self.node.select_text(
            text,
            mode="step",
            filter_indices="+[1,6]"
        )
        self.assertEqual(result_step2, ("Sixth text", 6))
        
        # Third step should wrap around to first item
        result_step3 = self.node.select_text(
            text,
            mode="step",
            filter_indices="+[1,6]"
        )
        self.assertEqual(result_step3, ("First text", 1))
        
    def test_empty_filter(self):
        # Test that empty filter uses all indices
        text = "@1 First text\n@2 Second text\n@3 Third text"
        
        # Empty filter should use all indices
        result = self.node.select_text(
            text, 
            mode="normal", 
            index=2,
            filter_indices=""
        )
        self.assertEqual(result, ("Second text", 2))
        
        # Empty inclusion list should use all indices
        result = self.node.select_text(
            text, 
            mode="normal", 
            index=2,
            filter_indices="+[]"
        )
        self.assertEqual(result, ("Second text", 2))
        
        # Empty exclusion list should use all indices
        result = self.node.select_text(
            text, 
            mode="normal", 
            index=2,
            filter_indices="-[]"
        )
        self.assertEqual(result, ("Second text", 2))

if __name__ == '__main__':
    unittest.main() 