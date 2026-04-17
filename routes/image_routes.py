from flask import Blueprint, request, jsonify, current_app
from errors import ValidationError

image_bp = Blueprint('images', __name__)


@image_bp.route('/api/upload-image', methods=['POST'])
def upload_image():
    data = request.get_json(silent=True)
    if not data or 'image' not in data:
        raise ValidationError("No image data provided")
    service = current_app.config['services']['image_service']
    result = service.upload_image(data['image'])
    return jsonify(result)


@image_bp.route('/api/images', methods=['GET'])
def get_images():
    service = current_app.config['services']['image_service']
    result = service.get_images()
    return jsonify(result)


@image_bp.route('/api/images/<config_id>', methods=['GET'])
def get_image_config(config_id):
    service = current_app.config['services']['image_service']
    result = service.get_image_config(config_id)
    return jsonify(result)


@image_bp.route('/api/split-image', methods=['POST'])
def split_image():
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError("No data provided")
    service = current_app.config['services']['image_service']
    result = service.split_image(
        data.get('src'),
        data.get('splitLines', []),
        data.get('width', 300)
    )
    return jsonify(result)


@image_bp.route('/api/clean-split-cache', methods=['POST'])
def clean_split_cache():
    data = request.get_json(silent=True)
    max_age_hours = data.get('max_age_hours', 24) if data else 24
    service = current_app.config['services']['image_service']
    result = service.clean_split_cache(max_age_hours)
    return jsonify(result)
