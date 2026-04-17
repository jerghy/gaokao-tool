import os


class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IMG_DIR = os.path.join(BASE_DIR, 'img')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    SCREENSHOT_DIR = os.path.join(BASE_DIR, 'screenshot_temp')
    SPLIT_CACHE_DIR = os.path.join(BASE_DIR, 'split_cache')
    PENDING_SCREENSHOTS_FILE = os.path.join(BASE_DIR, 'pending_screenshots.json')
    TAGS_DATA_PATH = os.path.join(BASE_DIR, 'tags_data.json')
    IMAGES_DATA_PATH = os.path.join(BASE_DIR, 'images.json')
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')

    @classmethod
    def ensure_dirs(cls):
        os.makedirs(cls.IMG_DIR, exist_ok=True)
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.SCREENSHOT_DIR, exist_ok=True)
        os.makedirs(cls.SPLIT_CACHE_DIR, exist_ok=True)
