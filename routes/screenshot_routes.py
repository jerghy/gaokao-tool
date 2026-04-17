from flask import Blueprint, request, jsonify, current_app
from errors import ValidationError, NotFoundError

screenshot_bp = Blueprint('screenshots', __name__)


@screenshot_bp.route('/api/screenshot/upload', methods=['POST'])
def upload_screenshot():
    data = request.get_json(silent=True)
    if not data or 'image' not in data:
        raise ValidationError("No image data provided")
    service = current_app.config['services']['screenshot_service']
    result = service.upload_screenshot(data['image'])
    return jsonify(result)


@screenshot_bp.route('/api/screenshot/check', methods=['GET'])
def check_screenshot():
    service = current_app.config['services']['screenshot_service']
    result = service.check_screenshots()
    return jsonify(result)


@screenshot_bp.route('/api/screenshot/consume/<screenshot_id>', methods=['POST'])
def consume_screenshot(screenshot_id):
    service = current_app.config['services']['screenshot_service']
    try:
        result = service.consume_screenshot(screenshot_id)
    except ValueError:
        raise NotFoundError("Screenshot", screenshot_id)
    return jsonify(result)
