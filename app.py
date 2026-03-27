from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import base64
from datetime import datetime
import uuid
import time
import threading
import hashlib
from tag_system import TagSystem
from search_engine import SearchEngine
from PIL import Image

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'img')
DATA_DIR = os.path.join(BASE_DIR, 'data')
SCREENSHOT_DIR = os.path.join(BASE_DIR, 'screenshot_temp')
SPLIT_CACHE_DIR = os.path.join(BASE_DIR, 'split_cache')
PENDING_SCREENSHOTS_FILE = os.path.join(BASE_DIR, 'pending_screenshots.json')

tag_system = TagSystem(os.path.join(BASE_DIR, 'tags_data.json'))
TAGS_DATA_PATH = os.path.join(BASE_DIR, 'tags_data.json')
search_engine = SearchEngine(DATA_DIR)

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(SPLIT_CACHE_DIR, exist_ok=True)

pending_screenshots = {}
pending_screenshots_lock = threading.Lock()

def load_pending_screenshots():
    global pending_screenshots
    if os.path.exists(PENDING_SCREENSHOTS_FILE):
        try:
            with open(PENDING_SCREENSHOTS_FILE, 'r', encoding='utf-8') as f:
                pending_screenshots = json.load(f)
        except:
            pending_screenshots = {}

def save_pending_screenshots():
    with pending_screenshots_lock:
        with open(PENDING_SCREENSHOTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(pending_screenshots, f, ensure_ascii=False, indent=2)

load_pending_screenshots()

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
            for field in ['question_analysis', 'thinking_processes', 'neural_reaction', 'immersion_thinking', 'math_thinking_chain']:
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
        
        search_engine.refresh()
        
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
        search = request.args.get('search', '')

        if search:
            result = search_engine.search(search, page, page_size)
            return jsonify(result)
        
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
            'total_pages': (total + page_size - 1) // page_size,
            'search_query': ''
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
        
        search_engine.refresh()
        
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
        
        search_engine.refresh()
        
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
        
        search_engine.refresh()
        
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
        save_pending_screenshots()
        
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
            
            if expired_ids:
                save_pending_screenshots()
            
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
        save_pending_screenshots()
        
        return jsonify({
            'success': True,
            'path': f'img/{new_filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/screenshot_temp/<path:filename>')
def serve_screenshot_temp(filename):
    return send_from_directory(SCREENSHOT_DIR, filename)

@app.route('/split_cache/<path:filename>')
def serve_split_cache(filename):
    return send_from_directory(SPLIT_CACHE_DIR, filename)

@app.route('/api/split-image', methods=['POST'])
def split_image():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        image_src = data.get('src')
        split_lines = data.get('splitLines', [])
        width = data.get('width', 300)
        
        if not image_src:
            return jsonify({'error': 'Image src is required'}), 400
        
        if not split_lines or len(split_lines) == 0:
            return jsonify({'success': True, 'parts': [{'src': image_src, 'width': width}]})
        
        if image_src.startswith('/'):
            image_src = image_src[1:]
        
        if image_src.startswith('img/'):
            image_path = os.path.join(BASE_DIR, image_src)
        else:
            image_path = os.path.join(IMG_DIR, os.path.basename(image_src))
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image not found'}), 404
        
        cache_key_str = f"{image_src}_{','.join(map(str, sorted(split_lines)))}_{width}"
        cache_key = hashlib.md5(cache_key_str.encode()).hexdigest()
        cache_dir = os.path.join(SPLIT_CACHE_DIR, cache_key)
        
        if os.path.exists(cache_dir):
            parts = []
            for filename in sorted(os.listdir(cache_dir)):
                if filename.endswith('.png'):
                    parts.append({
                        'src': f'/split_cache/{cache_key}/{filename}',
                        'width': width
                    })
            if parts:
                return jsonify({'success': True, 'parts': parts})
        
        os.makedirs(cache_dir, exist_ok=True)
        
        img = Image.open(image_path)
        img_width, img_height = img.size
        
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
        
        return jsonify({'success': True, 'parts': parts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clean-split-cache', methods=['POST'])
def clean_split_cache():
    try:
        max_age_hours = request.json.get('max_age_hours', 24) if request.json else 24
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        cleaned = 0
        
        for cache_key in os.listdir(SPLIT_CACHE_DIR):
            cache_dir = os.path.join(SPLIT_CACHE_DIR, cache_key)
            if os.path.isdir(cache_dir):
                dir_mtime = os.path.getmtime(cache_dir)
                if current_time - dir_mtime > max_age_seconds:
                    import shutil
                    shutil.rmtree(cache_dir)
                    cleaned += 1
        
        return jsonify({'success': True, 'cleaned': cleaned})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
