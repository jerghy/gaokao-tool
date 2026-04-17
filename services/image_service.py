import os
import base64
import hashlib
import time
import shutil
import uuid
from datetime import datetime
from PIL import Image
from errors import ValidationError, NotFoundError


class ImageService:
    def __init__(self, image_manager, img_dir, base_dir, split_cache_dir):
        self.image_manager = image_manager
        self.img_dir = img_dir
        self.base_dir = base_dir
        self.split_cache_dir = split_cache_dir

    def upload_image(self, image_data):
        if not image_data:
            raise ValidationError("No image data provided")

        raw = image_data
        if raw.startswith('data:image'):
            raw = raw.split(',')[1]

        file_ext = 'png'
        if 'image/jpeg' in image_data:
            file_ext = 'jpg'
        elif 'image/gif' in image_data:
            file_ext = 'gif'

        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{file_ext}"
        filepath = os.path.join(self.img_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(raw))

        try:
            with Image.open(filepath) as img:
                img_width, img_height = img.size
        except Exception:
            img_width, img_height = None, None

        file_size = os.path.getsize(filepath)

        image_id = self.image_manager.add_image(
            filename=filename,
            path=f'img/{filename}',
            width=img_width,
            height=img_height,
            file_size=file_size
        )

        return {
            'success': True,
            'image_id': image_id,
            'filename': filename,
            'path': f'img/{filename}'
        }

    def split_image(self, image_src, split_lines, width=300):
        if not image_src:
            raise ValidationError("Image src is required")

        if not split_lines or len(split_lines) == 0:
            return {'success': True, 'parts': [{'src': image_src, 'width': width}]}

        if image_src.startswith('/'):
            image_src = image_src[1:]

        if image_src.startswith('img/'):
            image_path = os.path.join(self.base_dir, image_src)
        else:
            image_path = os.path.join(self.img_dir, os.path.basename(image_src))

        if not os.path.exists(image_path):
            raise NotFoundError("Image", image_src)

        cache_key_str = f"{image_src}_{','.join(map(str, sorted(split_lines)))}_{width}"
        cache_key = hashlib.md5(cache_key_str.encode()).hexdigest()
        cache_dir = os.path.join(self.split_cache_dir, cache_key)

        if os.path.exists(cache_dir):
            parts = []
            for filename in sorted(os.listdir(cache_dir)):
                if filename.endswith('.png'):
                    parts.append({
                        'src': f'/split_cache/{cache_key}/{filename}',
                        'width': width
                    })
            if parts:
                return {'success': True, 'parts': parts}

        os.makedirs(cache_dir, exist_ok=True)

        with Image.open(image_path) as img:
            img_width, img_height = img.size

            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            lines = [0] + sorted(split_lines) + [1]
            parts = []

            for i in range(len(lines) - 1):
                top_ratio = lines[i]
                bottom_ratio = lines[i + 1]

                top_y = int(img_height * top_ratio)
                bottom_y = int(img_height * bottom_ratio)

                cropped = img.crop((0, top_y, img_width, bottom_y))

                part_filename = f'part_{i:03d}.png'
                part_path = os.path.join(cache_dir, part_filename)
                cropped.save(part_path, 'PNG')

                parts.append({
                    'src': f'/split_cache/{cache_key}/{part_filename}',
                    'width': width
                })

        return {'success': True, 'parts': parts}

    def get_images(self):
        images = self.image_manager.get_all_images()
        configs = self.image_manager.get_all_configs()
        return {
            'success': True,
            'images': images,
            'configs': configs
        }

    def get_image_config(self, config_id):
        full_info = self.image_manager.get_full_image_info(config_id)
        if not full_info:
            raise NotFoundError("Image config", config_id)
        return {
            'success': True,
            'image': full_info['image'],
            'config': full_info['config']
        }

    def clean_split_cache(self, max_age_hours=24):
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        cleaned = 0

        for cache_key in os.listdir(self.split_cache_dir):
            cache_dir = os.path.join(self.split_cache_dir, cache_key)
            if os.path.isdir(cache_dir):
                dir_mtime = os.path.getmtime(cache_dir)
                if current_time - dir_mtime > max_age_seconds:
                    shutil.rmtree(cache_dir)
                    cleaned += 1

        return {'success': True, 'cleaned': cleaned}
