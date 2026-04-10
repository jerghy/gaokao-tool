import os
import base64
import json
from typing import Optional

__all__ = [
    "encode_image_to_base64",
    "get_image_media_type",
    "load_images_data",
    "get_image_path_by_config_id",
    "extract_image_paths_from_items",
]


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_media_type(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower()
    media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
    return media_types.get(ext, "image/png")


_images_data_cache = None
_images_data_path = None

def _get_base_dir(data_dir: str) -> str:
    return os.path.dirname(os.path.abspath(data_dir))

def load_images_data(data_dir: str) -> dict:
    global _images_data_cache, _images_data_path
    images_path = os.path.join(_get_base_dir(data_dir), "images.json")
    if _images_data_cache is not None and _images_data_path == images_path:
        return _images_data_cache
    if os.path.exists(images_path):
        with open(images_path, "r", encoding="utf-8") as f:
            _images_data_cache = json.load(f)
            _images_data_path = images_path
            return _images_data_cache
    return {"images": {}, "configs": {}}

def get_image_path_by_config_id(config_id: str, data_dir: str, images_data=None) -> Optional[str]:
    if images_data is None:
        images_data = load_images_data(data_dir)
    config = images_data.get("configs", {}).get(config_id)
    if not config:
        return None
    image = images_data.get("images", {}).get(config.get("image_id"))
    if not image:
        return None
    path = image.get("path")
    if not path:
        return None
    full_path = os.path.normpath(os.path.join(_get_base_dir(data_dir), path))
    return full_path if os.path.exists(full_path) else None

def extract_image_paths_from_items(items: list, data_dir: str, images_data=None) -> list:
    paths = []
    for item in items:
        if item.get("type") != "image":
            continue
        config_id = item.get("config_id")
        if config_id:
            path = get_image_path_by_config_id(config_id, data_dir, images_data)
            if path:
                paths.append(path)
            continue
        src = item.get("src")
        if src:
            full_path = os.path.normpath(os.path.join(_get_base_dir(data_dir), src))
            if os.path.exists(full_path):
                paths.append(full_path)
    return paths
