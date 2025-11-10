# DB setup - Standard SQL with sqlite3
import sqlite3
import os
from contextlib import contextmanager
from flask import g, current_app


def get_db():
    """Get database connection from Flask g object"""
    if 'db' not in g:
        db_path = os.environ.get('DATABASE_URL', 'finance_app.db')
        # Remove sqlite:/// prefix if present
        if db_path.startswith('sqlite:///'):
            db_path = db_path.replace('sqlite:///', '')
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row  # Return rows as dictionaries
    return g.db


def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    db_path = os.environ.get('DATABASE_URL', 'finance_app.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path.replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expense (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
            )
        ''')
        
        # Create budgets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, category, month, year),
                FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expense_user_id ON expense(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expense_date ON expense(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expense_category ON expense(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_budget_user_id ON budget(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_budget_month_year ON budget(month, year)')
        
        conn.commit()
