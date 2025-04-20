import re
import random as rand_module
import uuid
import time

class ICHIS_Text_Selector:
    """
    A node that allows selecting text segments from a multi-line input using various selection modes.
    """
    
    current_step_index = 0  # Class variable to track step position
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "mode": (["normal", "step", "random"], {"default": "normal"}),
            },
            "optional": {
                "index": ("INT", {"default": 1, "min": 1, "max": 1000}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "filter_indices": ("STRING", {"default": "", "placeholder": "Format: +[1,3-5] to include or -[2,4-6] to exclude"}),
                "reset_step": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("selected_text", "index_used")
    FUNCTION = "select_text"
    CATEGORY = "ICHIS"
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Check reset first - use time/uuid to ensure trigger even if toggled quickly
        if kwargs.get("reset_step", False):
            return f"reset_{time.time()}_{uuid.uuid4()}"
            
        # Check mode next
        if kwargs.get("mode", "normal") != "normal":
            current_time = time.time()
            # No need for complex time check here, dynamic mode on means run
            return f"{current_time}_{uuid.uuid4()}"
             
        return None
    
    def select_text(self, text, mode="normal", index=1, seed=0, filter_indices="", reset_step=False):
        # Split text into segments using @ or @N pattern
        segments = []
        current_segment = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('@'):
                # If we have a previous segment, add it
                if current_segment:
                    segments.append('\n'.join(current_segment))
                    current_segment = []
                current_segment.append(line)
            else:
                current_segment.append(line)
                
        # Add the last segment if there is one
        if current_segment:
            segments.append('\n'.join(current_segment))
            
        # Handle empty input
        if not segments:
            return ("", 0)
            
        # Validate filter_indices format; ignore invalid inputs
        raw_filter = filter_indices.strip()
        if raw_filter:
            cleaned = raw_filter.replace(' ', '')
            # Accept +[...], -[...], [...], or raw list like 1,2-4 (no brackets)
            pattern = r"([+\-]\[\d+(-\d+)?(,\d+(-\d+)?)*\])|" \
                      r"(\[\d+(-\d+)?(,\d+(-\d+)?)*\])|" \
                      r"(\d+(-\d+)?(,\d+(-\d+)?)*$)"
            if not re.fullmatch(pattern, cleaned):
                raw_filter = ''  # invalid format, disable filtering
        filter_indices = raw_filter
        
        # Determine if we're using inclusion or exclusion mode
        is_inclusion_mode = True
        parsed_indices = set()
        
        if filter_indices.strip():
            # Check if it starts with + or -
            if filter_indices.strip().startswith('-'):
                is_inclusion_mode = False
                clean_filter = filter_indices.strip()[1:].strip()  # Remove the - and trim
            elif filter_indices.strip().startswith('+'):
                is_inclusion_mode = True
                clean_filter = filter_indices.strip()[1:].strip()  # Remove the + and trim
            else:
                # No prefix, assume inclusion
                clean_filter = filter_indices.strip()
            
            try:
                # Remove brackets and whitespace, then split by commas
                clean_str = clean_filter.strip('[]{}()').replace(' ', '')
                if clean_str:
                    # Split by commas and process each part
                    for part in clean_str.split(','):
                        try:
                            # Check if it's a range notation (e.g., "1-5")
                            if '-' in part:
                                range_parts = part.split('-')
                                if len(range_parts) == 2:
                                    start = int(range_parts[0])
                                    end = int(range_parts[1])
                                    if start > 0 and end > 0:
                                        # Add all indices in the range
                                        for i in range(start, end + 1):
                                            parsed_indices.add(i)
                            else:
                                # Regular single index
                                idx = int(part)
                                if idx > 0:  # Only include positive indices
                                    parsed_indices.add(idx)
                        except ValueError:
                            continue  # Skip invalid numbers or ranges
            except:
                pass  # Ignore any parsing errors
        
        # Create available indices based on inclusion/exclusion mode
        if is_inclusion_mode:
            # Include only specified indices
            if parsed_indices:
                available_indices = [i for i in parsed_indices if 1 <= i <= len(segments)]
            else:
                # If no indices specified in inclusion mode, use all
                available_indices = list(range(1, len(segments) + 1))
        else:
            # Exclude the specified indices
            available_indices = [i for i in range(1, len(segments) + 1) if i not in parsed_indices]
        
        # If no indices are available after filtering, use all indices
        if not available_indices:
            available_indices = list(range(1, len(segments) + 1))
        
        # Sort available indices for consistent ordering
        available_indices.sort()
        
        # Store the selected index for output
        selected_index = index
        
        # --- Handle Reset ---        
        if reset_step:
            self.__class__.current_step_index = 0 # Reset to 0
            
        # --- Determine selected index based on mode ---        
        if mode == "random":
            # Set seed if provided
            if seed != 0:
                rand_module.seed(seed)
                
            # Select from available indices
            selected_index = rand_module.choice(available_indices)
        elif mode == "step":
            # Use the current step index
            step_to_use = self.__class__.current_step_index % len(available_indices)
            selected_index = available_indices[step_to_use]
            
            # Update step index for next time
            self.__class__.current_step_index = (step_to_use + 1) % len(available_indices)
            
        # else mode == "normal", use the provided index
        
        # If normal mode and the selected index is not in available_indices,
        # choose the closest available index
        if mode == "normal" and selected_index not in available_indices:
            if available_indices:
                # Find the closest available index
                selected_index = min(available_indices, key=lambda x: abs(x - selected_index))
        
        # Ensure index is within bounds
        if selected_index < 1:
            selected_index = 1
        elif selected_index > len(segments):
            selected_index = len(segments)
            
        # Get the selected text and remove the @N marker
        selected_text = segments[selected_index - 1]
        if selected_text.startswith('@'):
            # Remove the @N marker and any following whitespace
            selected_text = selected_text.split(' ', 1)[1] if ' ' in selected_text else selected_text[1:]
            
        return (selected_text, selected_index) 