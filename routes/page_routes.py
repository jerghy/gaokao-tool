import os
from flask import Blueprint, send_from_directory, current_app

page_bp = Blueprint('pages', __name__)


@page_bp.route('/')
def index():
    return send_from_directory('static', 'index.html')


@page_bp.route('/browse')
def browse():
    return send_from_directory('static', 'browse.html')


@page_bp.route('/training')
def training():
    return send_from_directory('static', 'training.html')


@page_bp.route('/training-print')
def training_print():
    return send_from_directory('static', 'training-print.html')


@page_bp.route('/print')
@page_bp.route('/print.html')
def print_page():
    return send_from_directory('static', 'print.html')


@page_bp.route('/difficulty')
def difficulty():
    return send_from_directory('static', 'difficulty.html')


@page_bp.route('/pdf')
def pdf_viewer():
    return send_from_directory('static/pdfjs/web', 'viewer.html')


@page_bp.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@page_bp.route('/img/<path:filename>')
def serve_image(filename):
    img_dir = current_app.config.get('IMG_DIR')
    return send_from_directory(img_dir, filename)


@page_bp.route('/screenshot_temp/<path:filename>')
def serve_screenshot_temp(filename):
    screenshot_dir = current_app.config.get('SCREENSHOT_DIR')
    return send_from_directory(screenshot_dir, filename)


@page_bp.route('/split_cache/<path:filename>')
def serve_split_cache(filename):
    split_cache_dir = current_app.config.get('SPLIT_CACHE_DIR')
    return send_from_directory(split_cache_dir, filename)
