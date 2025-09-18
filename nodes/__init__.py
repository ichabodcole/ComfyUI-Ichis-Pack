"""
Node definitions for ICHIS Nodes package
"""

from .aspect_ratio_plus import ICHIS_Aspect_Ratio_Plus
from .extract_tags import ICHIS_Extract_Tags
from .text_selector import ICHIS_Text_Selector
from .csv_tag_sampler import ICHIS_CSV_Tag_Sampler
from .save_tags import ICHIS_Save_Tags

# Register all nodes
NODE_CLASS_MAPPINGS = {
    "ICHIS_Aspect_Ratio_Plus": ICHIS_Aspect_Ratio_Plus,
    "ICHIS_Extract_Tags": ICHIS_Extract_Tags,
    "ICHIS_Text_Selector": ICHIS_Text_Selector,
    "ICHIS_CSV_Tag_Sampler": ICHIS_CSV_Tag_Sampler,
    "ICHIS_Save_Tags": ICHIS_Save_Tags,
}

# Define display names for each node
NODE_DISPLAY_NAME_MAPPINGS = {
    "ICHIS_Aspect_Ratio_Plus": "ICHIS Aspect Ratio Plus",
    "ICHIS_Extract_Tags": "ICHIS Extract Tags",
    "ICHIS_Text_Selector": "ICHIS Text Selector",
    "ICHIS_CSV_Tag_Sampler": "ICHIS CSV Tag Sampler",
    "ICHIS_Save_Tags": "ICHIS Save Tags",
}
