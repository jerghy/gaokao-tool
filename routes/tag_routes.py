from flask import Blueprint, jsonify, current_app

tag_bp = Blueprint('tags', __name__)


@tag_bp.route('/api/tags', methods=['GET'])
def get_tags():
    tag_repo = current_app.config['services']['tag_repo']
    tag_tree = tag_repo.get_tag_tree()
    all_tags = tag_repo.get_all_tags()
    return jsonify({
        'success': True,
        'tag_tree': tag_tree,
        'all_tags': all_tags
    })
