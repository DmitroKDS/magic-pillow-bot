import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageChops, ImageOps

def pil_effect(image: Image.Image) -> Image.Image:
    """
    Adds an outline to an image, independent of the image's dimensions.

    Args:
        image: The input Pillow image with a transparent background.
        border_color (tuple): RGB color for the border.
        border_thickness (int): Thickness of the border in pixels.
        border_radius (int): Radius for the border rounding effect.

    Returns:
        Image: The resulting image with the outline added.
    """
    border_color = (255, 255, 255)
    border_thickness = 100
    border_radius = 300

    padding = border_radius + border_thickness
    canvas_size = (image.width + 2 * padding, image.height + 2 * padding)

    expand_image = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    expand_image.paste(image, (padding, padding), mask=image)

    cv2_image = cv2.cvtColor(np.array(expand_image), cv2.COLOR_RGBA2BGRA)

    alpha = cv2_image[:, :, 3]

    kernel_radius = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (border_radius, border_radius))
    kernel_thickness = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (border_thickness, border_thickness))

    expanded_mask = cv2.dilate(alpha, kernel_radius, iterations=1)
    filled_border = cv2.dilate(expanded_mask, kernel_thickness, iterations=1)

    border_image = np.zeros_like(cv2_image, dtype=np.uint8)
    border_image[filled_border != 0, :3] = border_color
    border_image[filled_border != 0, 3] = 255

    border_pil = Image.fromarray(cv2.cvtColor(border_image, cv2.COLOR_BGRA2RGBA))

    result = Image.alpha_composite(border_pil, expand_image)

    result = result.crop(result.getbbox())

    return result


def add_inner_shadow(image: Image) -> Image:
    """
    Create an inner shadow effect with a much lighter shadow color.
    """
    alpha = image.getchannel('A')

    shadow_base = Image.new('L', image.size, 0)
    shadow_base.paste(alpha)

    shadow_offset = ImageChops.offset(shadow_base, 10, 10)

    blurred_shadow = shadow_offset.filter(ImageFilter.GaussianBlur(40))

    shadow = ImageOps.colorize(blurred_shadow, black="black", white="white")
    shadow = shadow.point(lambda p: p * 0.6)

    new_alpha = ImageChops.subtract(alpha, blurred_shadow)

    shadow_layer = Image.new('RGBA', image.size, (180, 180, 180, 0))
    shadow_layer.putalpha(new_alpha)

    final_image = Image.alpha_composite(image, shadow_layer)

    return final_image