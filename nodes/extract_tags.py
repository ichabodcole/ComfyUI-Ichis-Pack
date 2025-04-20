import re
from typing import List

class ICHIS_Extract_Tags:
    """
    A node that extracts text segments based on matching tags and combines them with a specified delimiter.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "concepts": ("STRING", {"multiline": True, "placeholder": "Enter tags separated by commas or new lines"}),
                "delimiter": ("STRING", {"default": ", ", "placeholder": "Enter delimiter to join matches"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("extracted_text",)
    FUNCTION = "extract_text"
    CATEGORY = "ICHIS"
    
    def extract_text(self, text: str, concepts: str, delimiter: str) -> tuple:
        # Default delimiter to ", " if none provided
        if not delimiter:
            delimiter = ", "
        # Split input text by commas and clean up whitespace
        segments = [segment.strip() for segment in text.split(',')]
        
        # Split concepts by newlines and commas, and clean up whitespace
        # First split by newlines, then by commas if any
        concept_lines = concepts.split('\n')
        concept_list = []
        for line in concept_lines:
            # Split each line by commas if they exist
            concepts_in_line = [concept.strip().lower() for concept in line.split(',') if concept.strip()]
            concept_list.extend(concepts_in_line)
        
        # Find segments that match any of the concepts
        matching_segments = []
        for segment in segments:
            # Check if any concept is in the segment (case-insensitive)
            segment_lower = segment.lower()
            if any(concept in segment_lower for concept in concept_list):
                matching_segments.append(segment)
        
        # Join matching segments with the specified delimiter
        result = delimiter.join(matching_segments)
        
        return (result,) 