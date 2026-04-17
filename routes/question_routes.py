from flask import Blueprint, request, jsonify, current_app
from errors import ValidationError

question_bp = Blueprint('questions', __name__)


@question_bp.route('/api/save', methods=['POST'])
def save_question():
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError("No data provided")
    service = current_app.config['services']['question_service']
    result = service.save_question(data)
    return jsonify(result)


@question_bp.route('/api/questions', methods=['GET'])
def get_questions():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    search = request.args.get('search', '')
    service = current_app.config['services']['question_service']
    result = service.get_questions(page, page_size, search)
    return jsonify(result)


@question_bp.route('/api/questions/<id>', methods=['PUT'])
def update_question(id):
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError("No data provided")
    service = current_app.config['services']['question_service']
    result = service.update_question(id, data)
    return jsonify(result)


@question_bp.route('/api/questions/<id>', methods=['DELETE'])
def delete_question(id):
    service = current_app.config['services']['question_service']
    result = service.delete_question(id)
    return jsonify(result)


@question_bp.route('/api/questions/batch-add-tag', methods=['POST'])
def batch_add_tag():
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError("No data provided")
    record_ids = data.get('record_ids', [])
    tag = data.get('tag', '')
    service = current_app.config['services']['question_service']
    result = service.batch_add_tag(record_ids, tag)
    return jsonify(result)


@question_bp.route('/api/training-items', methods=['GET'])
def get_training_items():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    search = request.args.get('search', '')
    ability_tag = request.args.get('ability_tag', '')
    service = current_app.config['services']['question_service']
    result = service.get_training_items(page, page_size, search, ability_tag)
    return jsonify(result)


@question_bp.route('/api/training-ability-tags', methods=['GET'])
def get_training_ability_tags():
    service = current_app.config['services']['question_service']
    result = service.get_training_ability_tags()
    return jsonify(result)


@question_bp.route('/api/questions-with-difficulties', methods=['GET'])
def get_questions_with_difficulties():
    service = current_app.config['services']['question_service']
    result = service.get_questions_with_difficulties()
    return jsonify(result)


@question_bp.route('/api/questions/<id>/selected-difficulties', methods=['PUT'])
def update_selected_difficulties(id):
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError("No data provided")
    selected_difficulty_ids = data.get('selected_difficulty_ids')
    if selected_difficulty_ids is None:
        raise ValidationError("selected_difficulty_ids is required")
    service = current_app.config['services']['question_service']
    result = service.update_selected_difficulties(id, selected_difficulty_ids)
    return jsonify(result)
