import os
from ai.images import encode_image_to_base64, get_image_media_type

__all__ = [
    "build_input_content",
    "parse_items_text",
]


def build_input_content(text: str = "", image_paths: list = None) -> list:
    content = []
    if image_paths:
        for image_path in image_paths:
            if os.path.exists(image_path):
                b64 = encode_image_to_base64(image_path)
                mt = get_image_media_type(image_path)
                content.append({"type": "input_image", "image_url": "data:" + mt + ";base64," + b64})
    if text:
        content.append({"type": "input_text", "text": text})
    return content


def parse_items_text(items: list) -> str:
    return "".join(item.get("content", "") for item in items if item.get("type") in ("text", "richtext"))
