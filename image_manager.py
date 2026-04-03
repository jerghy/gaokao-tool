import json
import threading
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any


class ImageManager:
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self._lock = threading.RLock()
        self._data = {"images": {}, "configs": {}}
        self._load_data()

    def _load_data(self):
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {"images": {}, "configs": {}}
        else:
            self._data = {"images": {}, "configs": {}}

    def _save_data(self):
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _generate_id(self, prefix: str) -> str:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{prefix}_{timestamp}_{random_str}"

    def add_image(
        self,
        filename: str,
        path: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        file_size: Optional[int] = None
    ) -> str:
        with self._lock:
            image_id = self._generate_id('img')
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            image_data = {
                "id": image_id,
                "filename": filename,
                "path": path,
                "created_at": created_at
            }
            
            if width is not None:
                image_data["width"] = width
            if height is not None:
                image_data["height"] = height
            if file_size is not None:
                image_data["file_size"] = file_size
            
            self._data["images"][image_id] = image_data
            self._save_data()
            
            return image_id

    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._data["images"].get(image_id)

    def get_image_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for image in self._data["images"].values():
                if image.get("filename") == filename:
                    return image
            return None

    def create_config(
        self,
        image_id: str,
        display: str = "center",
        width: int = 300,
        height: str = "auto",
        charBox: Optional[Dict] = None,
        splitLines: Optional[List] = None
    ) -> str:
        with self._lock:
            config_id = self._generate_id('cfg')
            
            config_data = {
                "id": config_id,
                "image_id": image_id,
                "display": display,
                "width": width,
                "height": height,
                "used_by": []
            }
            
            if charBox is not None:
                config_data["charBox"] = charBox
            if splitLines is not None:
                config_data["splitLines"] = splitLines
            
            self._data["configs"][config_id] = config_data
            self._save_data()
            
            return config_id

    def get_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._data["configs"].get(config_id)

    def update_config(self, config_id: str, **kwargs) -> bool:
        with self._lock:
            config = self._data["configs"].get(config_id)
            if not config:
                return False
            
            protected_fields = {'id', 'image_id', 'used_by'}
            for key, value in kwargs.items():
                if key not in protected_fields:
                    config[key] = value
            
            self._save_data()
            return True

    def delete_config(self, config_id: str) -> bool:
        with self._lock:
            if config_id not in self._data["configs"]:
                return False
            
            del self._data["configs"][config_id]
            self._save_data()
            return True

    def add_usage(self, config_id: str, question_id: str):
        with self._lock:
            config = self._data["configs"].get(config_id)
            if config:
                if "used_by" not in config:
                    config["used_by"] = []
                if question_id not in config["used_by"]:
                    config["used_by"].append(question_id)
                    self._save_data()

    def remove_usage(self, config_id: str, question_id: str):
        with self._lock:
            config = self._data["configs"].get(config_id)
            if config and "used_by" in config:
                if question_id in config["used_by"]:
                    config["used_by"].remove(question_id)
                    self._save_data()

    def get_full_image_info(self, config_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            config = self._data["configs"].get(config_id)
            if not config:
                return None
            
            image_id = config.get("image_id")
            image = self._data["images"].get(image_id)
            if not image:
                return None
            
            full_info = {
                "config": config,
                "image": image
            }
            
            return full_info

    def get_all_images(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._data["images"].values())

    def get_all_configs(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._data["configs"].values())
