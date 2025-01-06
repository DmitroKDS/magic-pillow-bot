from PIL import Image


def thumbnail(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    """
    Generate a thumbnail of an image while maintaining its aspect ratio.

    Args:
        image (Image): The input PIL image to generate a thumbnail from.
        max_size (tuple[int, int]): The maximum (width, height) of the thumbnail.

    Returns:
        Image: A resized PIL image that fits within max_size while maintaining its aspect ratio.
    """
    aspect_ratio = image.width / image.height

    if aspect_ratio > 1:
        new_width = max_size[0]
        new_height = int(max_size[0] / aspect_ratio)
    else:
        new_height = max_size[1]
        new_width = int(max_size[1] * aspect_ratio)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)