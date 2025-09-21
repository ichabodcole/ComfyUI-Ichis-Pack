"""
Node definitions for ICHIS Nodes package
"""

from .aspect_ratio_plus import ICHIS_Aspect_Ratio_Plus
from .extract_tags import ICHIS_Extract_Tags
from .text_selector import ICHIS_Text_Selector
from .tag_sampler import ICHIS_Tag_Sampler
from .tag_file_loader import ICHIS_Tag_File_Loader
from .tag_category_select import ICHIS_Tag_Category_Select
from .save_tags import ICHIS_Save_Tags

WEB_DIRECTORY = "./web"
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]

# Register all nodes
NODE_CLASS_MAPPINGS = {
    "ICHIS_Aspect_Ratio_Plus": ICHIS_Aspect_Ratio_Plus,
    "ICHIS_Extract_Tags": ICHIS_Extract_Tags,
    "ICHIS_Text_Selector": ICHIS_Text_Selector,
    "ICHIS_Tag_Sampler": ICHIS_Tag_Sampler,
    "ICHIS_Save_Tags": ICHIS_Save_Tags,
    "ICHIS_Tag_File_Loader": ICHIS_Tag_File_Loader,
    "ICHIS_Tag_Category_Select": ICHIS_Tag_Category_Select,
}

# Define display names for each node
NODE_DISPLAY_NAME_MAPPINGS = {
    "ICHIS_Aspect_Ratio_Plus": "ICHIS Aspect Ratio Plus",
    "ICHIS_Extract_Tags": "ICHIS Extract Tags",
    "ICHIS_Text_Selector": "ICHIS Text Selector",
    "ICHIS_Tag_Sampler": "ICHIS Tag Sampler",
    "ICHIS_Save_Tags": "ICHIS Save Tags",
    "ICHIS_Tag_File_Loader": "ICHIS Tag File Loader",
    "ICHIS_Tag_Category_Select": "ICHIS Tag Category Select",
}
