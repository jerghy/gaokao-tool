import logging

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from image_manager import ImageManager
from search_engine import SearchEngine
from errors import AppError
from repositories.question_repository import QuestionRepository
from repositories.tag_repository import TagRepository
from services.question_service import QuestionService
from services.image_service import ImageService
from services.screenshot_service import ScreenshotService
from routes import question_bp, image_bp, screenshot_bp, tag_bp, page_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, static_folder=Config.STATIC_FOLDER)
    CORS(app)

    Config.ensure_dirs()

    question_repo = QuestionRepository(Config.DATA_DIR)
    tag_repo = TagRepository(Config.TAGS_DATA_PATH)
    tag_repo.initialize_from_data(Config.DATA_DIR)
    image_manager = ImageManager(Config.IMAGES_DATA_PATH)
    search_engine = SearchEngine(Config.DATA_DIR)

    question_service = QuestionService(
        question_repo=question_repo,
        tag_repo=tag_repo,
        image_manager=image_manager,
        search_engine=search_engine,
        img_dir=Config.IMG_DIR,
        static_dir=Config.BASE_DIR
    )
    image_service = ImageService(
        image_manager=image_manager,
        img_dir=Config.IMG_DIR,
        base_dir=Config.BASE_DIR,
        split_cache_dir=Config.SPLIT_CACHE_DIR
    )
    screenshot_service = ScreenshotService(
        screenshot_dir=Config.SCREENSHOT_DIR,
        img_dir=Config.IMG_DIR,
        pending_file_path=Config.PENDING_SCREENSHOTS_FILE,
        image_manager=image_manager
    )

    app.config['services'] = {
        'question_service': question_service,
        'image_service': image_service,
        'screenshot_service': screenshot_service,
        'tag_repo': tag_repo
    }
    app.config['IMG_DIR'] = Config.IMG_DIR
    app.config['SCREENSHOT_DIR'] = Config.SCREENSHOT_DIR
    app.config['SPLIT_CACHE_DIR'] = Config.SPLIT_CACHE_DIR

    app.register_blueprint(page_bp)
    app.register_blueprint(question_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(screenshot_bp)
    app.register_blueprint(tag_bp)

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        logger.warning(f"AppError: {error.code} - {error.message}")
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "请求的资源不存在"
            }
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "不支持的请求方法"
            }
        }), 405

    @app.errorhandler(Exception)
    def handle_generic_error(error: Exception):
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误"
            }
        }), 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
