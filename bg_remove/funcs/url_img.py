import aiohttp
from PIL import Image
from io import BytesIO
from pillow_heif import register_heif_opener


register_heif_opener()


async def url_img(url: str) -> Image.Image:
    """Get image from url
    
    Keyword arguments:
    url - string
    Return: Pillow Image
    """
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            img_data = await resp.read()

    img = Image.open(BytesIO(img_data))
    return img