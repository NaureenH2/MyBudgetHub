# database tables - User class for Flask-Login compatibility
from flask_login import UserMixin
from finance_app.database import get_db


class User(UserMixin):
    """User class for Flask-Login compatibility with standard SQL"""
    
    def __init__(self, id, username, email, password_hash, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
    
    @staticmethod
    def get(user_id):
        """Get user by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM user WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                created_at=row['created_at']
            )
        return None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM user WHERE username = ?', (username,))
        row = cursor.fetchone()
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                created_at=row['created_at']
            )
        return None
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM user WHERE email = ?', (email,))
        row = cursor.fetchone()
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                created_at=row['created_at']
            )
        return None
    
    @staticmethod
    def create(username, email, password_hash):
        """Create a new user"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO user (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        db.commit()
        user_id = cursor.lastrowid
        return User.get(user_id)
