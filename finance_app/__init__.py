# Creates Flask app, connects DB
from flask import Flask, send_from_directory
from flask_login import LoginManager
from finance_app.database import init_db, close_db
from finance_app.models import User
import os


def create_app():
    """Initialize Flask application with database and authentication"""
    app = Flask(__name__, static_folder='../static', static_url_path='')
    
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
    login_manager.login_view = '/login.html'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(int(user_id))
    
    @login_manager.unauthorized_handler
    def unauthorized():
        # Return JSON error for API routes, redirect for HTML routes
        from flask import request
        if request.path.startswith('/api/'):
            from flask import jsonify
            return jsonify({'error': 'Authentication required'}), 401
        # For HTML routes, redirect to login (default behavior)
        from flask import redirect, url_for
        return redirect('/login.html')
    
    # Register API blueprint
    from finance_app.api import api
    app.register_blueprint(api)
    
    # Serve static HTML files
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        # Skip API routes - they're handled by the API blueprint
        if path.startswith('api/'):
            from flask import abort
            abort(404)
        
        # Serve static files from static directory
        try:
            return send_from_directory(app.static_folder, path)
        except:
            # If file not found, try to serve index.html for HTML routes
            if '.' not in path.split('/')[-1] or path.endswith('.html'):
                return send_from_directory(app.static_folder, 'index.html')
            raise
    
    # Initialize database tables
    with app.app_context():
        init_db()
        # Create uploads directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app
