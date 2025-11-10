# Creates Flask app, connects DB
from flask import Flask
from flask_login import LoginManager
from finance_app.database import init_db, close_db
from finance_app.models import User
import os


def create_app():
    """Initialize Flask application with database and authentication"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Set database URL for sqlite3
    os.environ.setdefault('DATABASE_URL', 'finance_app.db')
    
    # Register database cleanup
    app.teardown_appcontext(close_db)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(int(user_id))
    
    # Register blueprints
    from finance_app.routes import bp
    app.register_blueprint(bp)
    
    # Initialize database tables
    with app.app_context():
        init_db()
        # Create uploads directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app
