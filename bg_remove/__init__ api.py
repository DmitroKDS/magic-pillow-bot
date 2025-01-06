from bg_remove.funcs.url_img import url_img
from bg_remove.funcs.pil_effect import pil_effect
from bg_remove.funcs.thumbnail import thumbnail

import asyncio

import logging

from gradio_client import Client, handle_file

from PIL import Image


hf_client = Client("briaai/BRIA-RMBG-2.0", hf_token="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")

async def bg_remove(img_path: str) -> list[tuple[Image.Image, str]]:
    logging.info(f'Removing background {img_path}')

    no_bg_img_result = await asyncio.to_thread(
        hf_client.predict,
        handle_file(img_path),
        api_name="/image"
    )

    logging.info(no_bg_img_result)

    no_bg_img = Image.open(no_bg_img_result[1])

    no_bg_img = await asyncio.to_thread(no_bg_img.crop, no_bg_img.getbbox())

    no_bg_img = await asyncio.to_thread( thumbnail, no_bg_img, (4000, 4000) )

    logging.info(f'Background removed {img_path}')


    img_name = img_path.split('/')[-1]
    no_bg_img_path = f"data/no_bg/{img_name}"

    logging.info(f'No bg image saved {no_bg_img_path}')


    pil_effect_img = await asyncio.to_thread( pil_effect, no_bg_img )
    pil_effect_img_path = f"data/pil_effect/{img_name}"

    logging.info(f'Pil effect image saved {no_bg_img_path}')


    return [
        (no_bg_img, no_bg_img_path),
        (pil_effect_img, pil_effect_img_path)
    ]