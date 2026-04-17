import os
import json
import time
import uuid
import base64
import shutil
import threading
from datetime import datetime
from PIL import Image


class ScreenshotService:
    def __init__(self, screenshot_dir, img_dir, pending_file_path, image_manager):
        self.screenshot_dir = screenshot_dir
        self.img_dir = img_dir
        self.pending_file_path = pending_file_path
        self.image_manager = image_manager
        self.pending_screenshots = {}
        self._lock = threading.RLock()
        self.load_pending()

    def load_pending(self):
        if os.path.exists(self.pending_file_path):
            try:
                with open(self.pending_file_path, 'r', encoding='utf-8') as f:
                    self.pending_screenshots = json.load(f)
            except Exception:
                self.pending_screenshots = {}

    def save_pending(self):
        with self._lock:
            with open(self.pending_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.pending_screenshots, f, ensure_ascii=False, indent=2)

    def upload_screenshot(self, image_data):
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]

        screenshot_id = datetime.now().strftime('%Y%m%d%H%M%S') + '_' + uuid.uuid4().hex[:8]
        filename = f"{screenshot_id}.png"
        filepath = os.path.join(self.screenshot_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))

        with self._lock:
            self.pending_screenshots[screenshot_id] = {
                'filename': filename,
                'path': f'screenshot_temp/{filename}',
                'timestamp': time.time(),
                'consumed': False
            }
        self.save_pending()

        return {
            'success': True,
            'screenshot_id': screenshot_id,
            'filename': filename
        }

    def check_screenshots(self):
        with self._lock:
            current_time = time.time()
            expired_ids = [
                sid for sid, info in self.pending_screenshots.items()
                if current_time - info['timestamp'] > 300
            ]
            for sid in expired_ids:
                filepath = os.path.join(self.screenshot_dir, self.pending_screenshots[sid]['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
                del self.pending_screenshots[sid]

            if expired_ids:
                self.save_pending()

            available = [
                {'id': sid, 'path': info['path']}
                for sid, info in self.pending_screenshots.items()
                if not info['consumed']
            ]

        return {
            'success': True,
            'has_screenshot': len(available) > 0,
            'screenshots': available
        }

    def consume_screenshot(self, screenshot_id):
        with self._lock:
            if screenshot_id not in self.pending_screenshots:
                raise ValueError(f"Screenshot not found: {screenshot_id}")

            info = self.pending_screenshots[screenshot_id]

            old_filepath = os.path.join(self.screenshot_dir, info['filename'])
            new_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
            new_filepath = os.path.join(self.img_dir, new_filename)

            if not os.path.exists(old_filepath):
                del self.pending_screenshots[screenshot_id]
                self.save_pending()
                raise ValueError(f"Screenshot file not found: {screenshot_id}")

            shutil.move(old_filepath, new_filepath)
            del self.pending_screenshots[screenshot_id]
            self.save_pending()

        img_width, img_height = None, None
        try:
            with Image.open(new_filepath) as img:
                img_width, img_height = img.size
        except Exception:
            pass

        file_size = os.path.getsize(new_filepath) if os.path.exists(new_filepath) else None

        image_id = self.image_manager.add_image(
            filename=new_filename,
            path=f'img/{new_filename}',
            width=img_width,
            height=img_height,
            file_size=file_size
        )

        return {
            'success': True,
            'image_id': image_id,
            'path': f'img/{new_filename}'
        }
