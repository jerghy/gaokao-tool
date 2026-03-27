from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import base64
from datetime import datetime
import uuid
import time
import threading
from tag_system import TagSystem

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'img')
DATA_DIR = os.path.join(BASE_DIR, 'data')
SCREENSHOT_DIR = os.path.join(BASE_DIR, 'screenshot_temp')

tag_system = TagSystem(os.path.join(BASE_DIR, 'tags_data.json'))
TAGS_DATA_PATH = os.path.join(BASE_DIR, 'tags_data.json')

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

pending_screenshots = {}
pending_screenshots_lock = threading.Lock()

tag_system = TagSystem(data_path=TAGS_DATA_PATH)

def initialize_tags_from_data():
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                record_id = data.get('id')
                tags = data.get('tags', [])
                if record_id:
                    for tag in tags:
                        tag_system.add_tag(record_id, tag)

initialize_tags_from_data()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/browse')
def browse():
    return send_from_directory('static', 'browse.html')

@app.route('/print.html')
def print_page():
    return send_from_directory('static', 'print.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/img/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMG_DIR, filename)

@app.route('/pdf')
def pdf_viewer():
    return send_from_directory('static/pdfjs/web', 'viewer.html')

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        image_data = data['image']
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        file_ext = 'png'
        if 'image/jpeg' in data.get('image', ''):
            file_ext = 'jpg'
        elif 'image/gif' in data.get('image', ''):
            file_ext = 'gif'
        
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{file_ext}"
        filepath = os.path.join(IMG_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': f'img/{filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/save', methods=['POST'])
def save_question():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        question_id = data.get('id', datetime.now().strftime('%Y%m%d%H%M%S'))
        filepath = os.path.join(DATA_DIR, f"{question_id}.json")
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                question_data = json.load(f)
            
            old_tags = question_data.get('tags', [])
            new_tags = data.get('tags', old_tags)
            
            if old_tags != new_tags:
                for tag in old_tags:
                    tag_system.remove_tag(question_id, tag)
                for tag in new_tags:
                    tag_system.add_tag(question_id, tag)
            
            question_data['question'] = data.get('question', question_data.get('question', {'items': []}))
            question_data['answer'] = data.get('answer', question_data.get('answer', {'items': []}))
            question_data['tags'] = new_tags
            question_data['sub_questions'] = data.get('sub_questions', [])
            for field in ['question_analysis', 'thinking_processes', 'neural_reaction', 'immersion_thinking']:
                if field in question_data:
                    del question_data[field]
        else:
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            question_data = {
                'id': question_id,
                'created_at': created_at,
                'question': data.get('question', {'items': []}),
                'answer': data.get('answer', {'items': []}),
                'tags': data.get('tags', []),
                'sub_questions': data.get('sub_questions', [])
            }
            
            for tag in data.get('tags', []):
                tag_system.add_tag(question_id, tag)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(question_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'id': question_id,
            'filename': f"{question_id}.json"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tags', methods=['GET'])
def get_tags():
    try:
        tag_tree = tag_system.get_tag_tree()
        all_tags = tag_system.get_all_tags()
        return jsonify({
            'success': True,
            'tag_tree': tag_tree,
            'all_tags': all_tags
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions', methods=['GET'])
def get_questions():
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 50, type=int)

        questions = []
        for filename in sorted(os.listdir(DATA_DIR), reverse=True):
            if filename.endswith('.json'):
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    questions.append(data)

        total = len(questions)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = questions[start:end]

        return jsonify({
            'questions': paginated,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions/<id>', methods=['PUT'])
def update_question(id):
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        filepath = os.path.join(DATA_DIR, f"{id}.json")
        if not os.path.exists(filepath):
            return jsonify({'error': 'Question not found'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            question_data = json.load(f)
        
        old_tags = question_data.get('tags', [])
        new_tags = data.get('tags', old_tags)
        
        if old_tags != new_tags:
            for tag in old_tags:
                tag_system.remove_tag(id, tag)
            for tag in new_tags:
                tag_system.add_tag(id, tag)
        
        question_data['question'] = data.get('question', question_data.get('question', {'items': []}))
        question_data['answer'] = data.get('answer', question_data.get('answer', {'items': []}))
        question_data['tags'] = new_tags
        question_data['sub_questions'] = data.get('sub_questions', question_data.get('sub_questions', []))
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(question_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'id': id,
            'question': question_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions/<id>', methods=['DELETE'])
def delete_question(id):
    try:
        filepath = os.path.join(DATA_DIR, f"{id}.json")
        if not os.path.exists(filepath):
            return jsonify({'error': 'Question not found'}), 404
        
        tags = tag_system.get_tags(id)
        for tag in tags:
            tag_system.remove_tag(id, tag)
        
        os.remove(filepath)
        
        return jsonify({'success': True, 'id': id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions/batch-add-tag', methods=['POST'])
def batch_add_tag():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        record_ids = data.get('record_ids', [])
        tag = data.get('tag', '')
        
        if not record_ids or not tag:
            return jsonify({'error': 'record_ids and tag are required'}), 400
        
        results = tag_system.batch_add_tag(record_ids, tag)
        
        for record_id in record_ids:
            if results[record_id]:
                filepath = os.path.join(DATA_DIR, f"{record_id}.json")
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        question_data = json.load(f)
                    if tag not in question_data.get('tags', []):
                        question_data['tags'] = question_data.get('tags', []) + [tag]
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(question_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/screenshot/upload', methods=['POST'])
def upload_screenshot():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        image_data = data['image']
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        screenshot_id = datetime.now().strftime('%Y%m%d%H%M%S') + '_' + uuid.uuid4().hex[:8]
        filename = f"{screenshot_id}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        with pending_screenshots_lock:
            pending_screenshots[screenshot_id] = {
                'filename': filename,
                'path': f'screenshot_temp/{filename}',
                'timestamp': time.time(),
                'consumed': False
            }
        
        return jsonify({
            'success': True,
            'screenshot_id': screenshot_id,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/screenshot/check', methods=['GET'])
def check_screenshot():
    try:
        with pending_screenshots_lock:
            current_time = time.time()
            expired_ids = [
                sid for sid, info in pending_screenshots.items()
                if current_time - info['timestamp'] > 300
            ]
            for sid in expired_ids:
                filepath = os.path.join(SCREENSHOT_DIR, pending_screenshots[sid]['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
                del pending_screenshots[sid]
            
            available = [
                {'id': sid, 'path': info['path']}
                for sid, info in pending_screenshots.items()
                if not info['consumed']
            ]
        
        return jsonify({
            'success': True,
            'has_screenshot': len(available) > 0,
            'screenshots': available
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/screenshot/consume/<screenshot_id>', methods=['POST'])
def consume_screenshot(screenshot_id):
    try:
        with pending_screenshots_lock:
            if screenshot_id not in pending_screenshots:
                return jsonify({'error': 'Screenshot not found'}), 404
            
            info = pending_screenshots[screenshot_id]
            info['consumed'] = True
            
            old_filepath = os.path.join(SCREENSHOT_DIR, info['filename'])
            new_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
            new_filepath = os.path.join(IMG_DIR, new_filename)
            
            if os.path.exists(old_filepath):
                import shutil
                shutil.move(old_filepath, new_filepath)
            
            del pending_screenshots[screenshot_id]
        
        return jsonify({
            'success': True,
            'path': f'img/{new_filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/screenshot_temp/<path:filename>')
def serve_screenshot_temp(filename):
    return send_from_directory(SCREENSHOT_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
