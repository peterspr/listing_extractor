"""
Flask application entry point
"""
import logging
from flask import Flask
from flask_cors import CORS

from backend.config.settings import settings
from backend.api.routes import api

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_app():
    """Application factory"""
    app = Flask(__name__)

    # Configure CORS
    CORS(app, origins=settings.CORS_ORIGINS, supports_credentials=True)

    # Register blueprints
    app.register_blueprint(api)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {str(error)}")
        return {'error': 'Internal server error'}, 500

    logger.info("Flask application initialized")

    return app


if __name__ == '__main__':
    app = create_app()
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG,
        threaded=True
    )
