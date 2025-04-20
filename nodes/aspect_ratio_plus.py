import torch
import random as rand_module
import time
import uuid

class ICHIS_Aspect_Ratio_Plus:
    """
    A node that provides a selection of common SDXL-optimized aspect ratios with advanced control options.
    It outputs width, height, and an empty latent tensor.
    """
    
    # Class variable to keep track of the current step index for all instances
    step_index = 0
    # Class variable to track the last time the step was updated
    last_step_time = 0
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "aspect_ratio": (["1:1 square 1024x1024", 
                                 "3:4 portrait 896x1152", 
                                 "5:8 portrait 832x1216", 
                                 "9:16 portrait 768x1344", 
                                 "9:21 portrait 640x1536", 
                                 "3:2 landscape 1216x832", 
                                 "16:9 landscape 1344x768", 
                                 "21:9 landscape 1536x640"], {"default": "1:1 square 1024x1024"}),
                "upscale": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64}),
                "mode": (["normal", "step", "random"], {"default": "normal"}),
            },
            "optional": {
                "size_mode": (["all", "portrait only", "landscape only"], {"default": "all"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                # Individual toggles for each aspect ratio
                "include_1_1": ("BOOLEAN", {"default": True}),
                "include_3_4": ("BOOLEAN", {"default": True}),
                "include_5_8": ("BOOLEAN", {"default": True}),
                "include_9_16": ("BOOLEAN", {"default": True}),
                "include_9_21": ("BOOLEAN", {"default": True}),
                "include_3_2": ("BOOLEAN", {"default": True}),
                "include_16_9": ("BOOLEAN", {"default": True}),
                "include_21_9": ("BOOLEAN", {"default": True}),
                "reset_step": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("INT", "INT", "LATENT", "STRING", "INT")
    RETURN_NAMES = ("WIDTH", "HEIGHT", "LATENT", "SELECTED_RATIO", "NEXT_STEP")
    FUNCTION = "get_aspect_ratio"
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
    
    def get_aspect_ratio(self, aspect_ratio, upscale=1.0, batch_size=1, mode="normal", 
                        size_mode="all", seed=0, 
                        include_1_1=True, include_3_4=True, include_5_8=True, 
                        include_9_16=True, include_9_21=True, include_3_2=True, 
                        include_16_9=True, include_21_9=True,
                        reset_step=False):
        
        step_to_use = ICHIS_Aspect_Ratio_Plus.step_index
        next_step_index_internal = step_to_use # Default next step

        # --- Handle Reset ---        
        if reset_step:
            step_to_use = 0
            next_step_index_internal = 1 # Set next step after reset
            ICHIS_Aspect_Ratio_Plus.step_index = 0 # Reset to 0
            
        # Mapping of options to dimensions
        aspect_ratios = {
            "1:1 square 1024x1024": (1024, 1024),
            "3:4 portrait 896x1152": (896, 1152),
            "5:8 portrait 832x1216": (832, 1216),
            "9:16 portrait 768x1344": (768, 1344),
            "9:21 portrait 640x1536": (640, 1536),
            "3:2 landscape 1216x832": (1216, 832),
            "16:9 landscape 1344x768": (1344, 768),
            "21:9 landscape 1536x640": (1536, 640),
        }
        
        # Map between aspect ratio names and include toggles
        include_map = {
            "1:1 square 1024x1024": include_1_1,
            "3:4 portrait 896x1152": include_3_4,
            "5:8 portrait 832x1216": include_5_8,
            "9:16 portrait 768x1344": include_9_16,
            "9:21 portrait 640x1536": include_9_21,
            "3:2 landscape 1216x832": include_3_2,
            "16:9 landscape 1344x768": include_16_9,
            "21:9 landscape 1536x640": include_21_9,
        }
        
        # Store the selected aspect ratio name for output
        selected_ratio = aspect_ratio
        
        # Filter aspect ratios based on size_mode and individual toggles
        filtered_ratios = {}
        
        for key, value in aspect_ratios.items():
            # Skip if toggle is set to False
            if not include_map[key]:
                continue
                
            # Apply size_mode filtering
            if size_mode == "portrait only" and "portrait" not in key and "square" not in key:
                continue
            elif size_mode == "landscape only" and "landscape" not in key and "square" not in key:
                continue
                
            # Include this ratio
            filtered_ratios[key] = value
        
        # In case all toggles are off, use the manually selected aspect ratio
        if not filtered_ratios:
            filtered_ratios = {aspect_ratio: aspect_ratios[aspect_ratio]}
        
        ratio_keys = sorted(filtered_ratios.keys())
        max_index = len(ratio_keys) - 1
        
        # --- Determine selected ratio based on mode ---        
        if mode == "random":
            # Set seed if provided
            if seed != 0:
                rand_module.seed(seed)
                
            selected_ratio = rand_module.choice(ratio_keys)
            # Keep internal step_index unchanged in random mode
        elif mode == "step":
            # Use the index determined above (either from reset or internal state)
            step_to_use = step_to_use % len(ratio_keys)
            selected_ratio = ratio_keys[step_to_use]
            
            # Calculate and store the next step for the subsequent run
            next_step_index_internal = (step_to_use + 1) % len(ratio_keys)
            if not reset_step: # Only update if we weren't resetting
                 ICHIS_Aspect_Ratio_Plus.step_index = next_step_index_internal
            # If we reset, the index is already set to 0 
            
        # else mode == "normal", use the manually selected aspect_ratio
            
        # Get dimensions for the selected ratio
        width, height = aspect_ratios[selected_ratio]
        
        # Apply upscaling
        if upscale != 1.0:
            width = int(width * upscale)
            height = int(height * upscale)
        
        # Create empty latent tensor
        channels = 4
        latent_height = height // 8
        latent_width = width // 8
        latent = torch.zeros([batch_size, channels, latent_height, latent_width])
        
        # Return the NEXT step index that will be used
        return (width, height, latent, selected_ratio, next_step_index_internal) 