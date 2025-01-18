from bg_remove.funcs.url_img import url_img
from bg_remove.funcs.pil_effect import pil_effect
from bg_remove.funcs.thumbnail import thumbnail

import asyncio

import logging

import torch
from torchvision import transforms
from transformers import AutoModelForImageSegmentation

from PIL import Image


device = "cpu"

model = AutoModelForImageSegmentation.from_pretrained('briaai/RMBG-2.0', trust_remote_code=True, revision="main")
torch.set_float32_matmul_precision(['high', 'highest'][0])
model.to(device)
model.eval()

image_preparator = transforms.Compose([
    transforms.Resize((1024, 1024)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


async def bg_remove(img: Image.Image, img_path: str) -> list[tuple[Image.Image, str]]:
    logging.info(f'Removing background {img_path}')
    
    try:
        # Convert image preparation to async
        input_images = await asyncio.to_thread(
            lambda: image_preparator(img.convert('RGB')).unsqueeze(0).to(device)
        )
        
        # Run model inference
        async def run_inference():
            with torch.no_grad():
                preds = model(input_images)[-1].sigmoid().cpu()
            return preds
            
        preds = await asyncio.to_thread(run_inference)
        
        # Process results
        pred = preds[0].squeeze()
        pred_pil = await asyncio.to_thread(transforms.ToPILImage(), pred)
        no_bg_mask = await asyncio.to_thread(lambda: pred_pil.resize(img.size))
        
        # Create final images
        no_bg_img = img.copy()
        no_bg_img.putalpha(no_bg_mask)
        no_bg_img = await asyncio.to_thread(lambda: no_bg_img.crop(no_bg_img.getbbox()))
        no_bg_img = await asyncio.to_thread(lambda: thumbnail(no_bg_img, (4000, 4000)))
        
        img_name = img_path.split('/')[-1]
        no_bg_img_path = f"data/no_bg/{img_name}"
        
        # Create pil effect image
        pil_effect_img = await asyncio.to_thread(pil_effect, no_bg_img)
        pil_effect_img_path = f"data/pil_effect/{img_name}"
        
        logging.info(f'Processing completed for {img_path}')
        
        return [
            (no_bg_img, no_bg_img_path),
            (pil_effect_img, pil_effect_img_path)
        ]
        
    except Exception as e:
        logging.error(f"Error in bg_remove: {e}")
        raise