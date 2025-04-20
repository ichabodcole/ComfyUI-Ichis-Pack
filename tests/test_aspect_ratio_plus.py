import unittest
from nodes.aspect_ratio_plus import ICHIS_Aspect_Ratio_Plus

class TestAspectRatioPlus(unittest.TestCase):
    def setUp(self):
        self.node = ICHIS_Aspect_Ratio_Plus()
    
    def test_get_aspect_ratio_normal_mode(self):
        # Test normal mode with all ratios enabled
        result = self.node.get_aspect_ratio(
            aspect_ratio="1:1 square 1024x1024",
            size_mode="portrait",
            include_1_1=True,
            include_3_4=True,
            include_5_8=True,
            include_9_16=True,
            include_9_21=True,
            include_3_2=True,
            include_16_9=True,
            include_21_9=True
        )
        self.assertIsNotNone(result)
    
    def test_get_aspect_ratio_portrait_filter(self):
        # Test portrait mode filtering
        result = self.node.get_aspect_ratio(
            aspect_ratio="1:1 square 1024x1024",
            size_mode="portrait",
            include_1_1=True,
            include_3_4=True,
            include_5_8=True,
            include_9_16=True,
            include_9_21=True,
            include_3_2=False,
            include_16_9=False,
            include_21_9=False
        )
        self.assertIsNotNone(result)
    
    def test_get_aspect_ratio_landscape_filter(self):
        # Test landscape mode filtering
        result = self.node.get_aspect_ratio(
            aspect_ratio="1:1 square 1024x1024",
            size_mode="landscape",
            include_1_1=True,
            include_3_4=False,
            include_5_8=False,
            include_9_16=False,
            include_9_21=False,
            include_3_2=True,
            include_16_9=True,
            include_21_9=True
        )
        self.assertIsNotNone(result)
    
    def test_get_aspect_ratio_square_filter(self):
        # Test square mode filtering
        result = self.node.get_aspect_ratio(
            aspect_ratio="1:1 square 1024x1024",
            size_mode="square",
            include_1_1=True,
            include_3_4=False,
            include_5_8=False,
            include_9_16=False,
            include_9_21=False,
            include_3_2=False,
            include_16_9=False,
            include_21_9=False
        )
        self.assertIsNotNone(result)
    
    def test_get_aspect_ratio_all_disabled(self):
        # Test when all ratios are disabled
        result = self.node.get_aspect_ratio(
            aspect_ratio="1:1 square 1024x1024",
            size_mode="portrait",
            include_1_1=False,
            include_3_4=False,
            include_5_8=False,
            include_9_16=False,
            include_9_21=False,
            include_3_2=False,
            include_16_9=False,
            include_21_9=False
        )
        self.assertIsNotNone(result)
    
    def test_get_aspect_ratio_step_mode(self):
        # Test step mode
        result1 = self.node.get_aspect_ratio(
            aspect_ratio="1:1 square 1024x1024",
            size_mode="portrait",
            mode="step",
            include_1_1=True,
            include_3_4=True,
            include_5_8=True,
            include_9_16=True,
            include_9_21=True,
            include_3_2=True,
            include_16_9=True,
            include_21_9=True
        )
        self.assertIsNotNone(result1)
    
    def test_get_aspect_ratio_random_mode(self):
        # Test random mode with seed
        result1 = self.node.get_aspect_ratio(
            aspect_ratio="1:1 square 1024x1024",
            size_mode="portrait",
            mode="random",
            include_1_1=True,
            include_3_4=True,
            include_5_8=True,
            include_9_16=True,
            include_9_21=True,
            include_3_2=True,
            include_16_9=True,
            include_21_9=True,
            seed=42
        )
        self.assertIsNotNone(result1)

if __name__ == '__main__':
    unittest.main() 