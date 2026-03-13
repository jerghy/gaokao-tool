from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import base64
from datetime import datetime
import uuid

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'img')
DATA_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/img/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMG_DIR, filename)

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
        
        question_id = datetime.now().strftime('%Y%m%d%H%M%S')
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        question_data = {
            'id': question_id,
            'created_at': created_at,
            'question': data.get('question', {'items': []}),
            'answer': data.get('answer', {'items': []})
        }
        
        filename = f"{question_id}.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(question_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'id': question_id,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
