"""
Image captioning with really lightweight model
"""
import os
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
from config import CAPTION_MODEL_ID


_caption_processor = None
_caption_model = None
_caption_device = None


def initialize_captioning_model():
    global _caption_processor, _caption_model, _caption_device
    
    _caption_device = "cuda" if torch.cuda.is_available() else "cpu"
    
    _caption_processor = AutoProcessor.from_pretrained(
        CAPTION_MODEL_ID, 
        trust_remote_code=True
    )
    _caption_model = AutoModelForCausalLM.from_pretrained(
        CAPTION_MODEL_ID,
        torch_dtype=torch.float16 if _caption_device == "cuda" else torch.float32,
        trust_remote_code=True,
    ).to(_caption_device)
    _caption_model.eval()


def caption_image(image_path: str, max_size: int = 1024) -> str:
    """
    Generate detailed caption for animal photo.
    
    Args:
        image_path: Path to image file
        max_size: Max dimension for pre-resize
        
    Returns:
        Caption text for agent context
    """
    
    try:
        # Load and pre-resize
        image = Image.open(image_path).convert("RGB")
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Generate detailed caption
        prompt = "<MORE_DETAILED_CAPTION>"
        
        inputs = _caption_processor(
            text=prompt, 
            images=image, 
            return_tensors="pt"
        )
        
        # Make sure dtype is the same with model weights
        inputs = {k: v.to(_caption_device) for k, v in inputs.items()}
        if "pixel_values" in inputs:
            inputs["pixel_values"] = inputs["pixel_values"].to(torch.float16)
        
        with torch.inference_mode():
            generated_ids = _caption_model.generate(
                **inputs,
                max_new_tokens=100,
                num_beams=3,
                do_sample=False,
            )
        
        caption = _caption_processor.batch_decode(
            generated_ids, 
            skip_special_tokens=True
        )[0]
        
        caption = caption.replace(prompt, "").strip()
        print(f"CAPTION: {caption}")
        
        return (
            f"Photo shows: {caption}. "
            f"Based on visible breed/species and appearance, estimate the animal's "
            f"approximate weight and size category (small/medium/large)."
        )
        
    except Exception as e:
        base = os.path.basename(image_path)
        print(f"Captioning failed: {e}")
        return (
            f"User provided photo '{base}'. Unable to analyze automatically. "
            f"Assume single animal of unknown type, medium size (~20-30 kg)."
        )
