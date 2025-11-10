"""
Create Example Database 1 - Student/Freelancer Profile
This database simulates a student or freelancer with moderate spending
"""
import sqlite3
from datetime import datetime, timedelta
import random

# Database file name
DB_FILE = 'example_db1.db'

# Create connection
conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

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

# Create indexes
cursor.execute('CREATE INDEX IF NOT EXISTS idx_expense_user_id ON expense(user_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_expense_date ON expense(date)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_expense_category ON expense(category)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_budget_user_id ON budget(user_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_budget_month_year ON budget(month, year)')

# Create user
from werkzeug.security import generate_password_hash
user_password_hash = generate_password_hash('demo123')
cursor.execute('''
    INSERT INTO user (username, email, password_hash)
    VALUES (?, ?, ?)
''', ('demo_user', 'demo@example.com', user_password_hash))
user_id = cursor.lastrowid

# Set budgets for current month
current_date = datetime.now()
current_month = current_date.month
current_year = current_date.year

budgets = [
    ('Food', 400.00),
    ('Transport', 150.00),
    ('Entertainment', 100.00),
    ('Shopping', 200.00),
    ('Rent', 800.00),
    ('Utilities', 100.00),
]

for category, amount in budgets:
    cursor.execute('''
        INSERT INTO budget (user_id, category, amount, month, year)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, category, amount, current_month, current_year))

# Generate expenses for the last 3 months
categories = ['Food', 'Transport', 'Entertainment', 'Shopping', 'Rent', 'Utilities', 'Health', 'Education']
food_descriptions = ['Grocery Store', 'Restaurant', 'Coffee Shop', 'Fast Food', 'Supermarket', 'Lunch', 'Dinner']
transport_descriptions = ['Gas Station', 'Uber', 'Bus Ticket', 'Parking', 'Metro', 'Taxi']
entertainment_descriptions = ['Movie Theater', 'Netflix', 'Spotify', 'Concert', 'Game', 'Books']
shopping_descriptions = ['Amazon', 'Clothing Store', 'Electronics', 'Online Purchase', 'Mall']
rent_descriptions = ['Monthly Rent', 'Apartment Rent']
utilities_descriptions = ['Electric Bill', 'Internet Bill', 'Phone Bill', 'Water Bill']
health_descriptions = ['Pharmacy', 'Doctor Visit', 'Gym Membership']
education_descriptions = ['Textbooks', 'Course Fee', 'School Supplies']

description_map = {
    'Food': food_descriptions,
    'Transport': transport_descriptions,
    'Entertainment': entertainment_descriptions,
    'Shopping': shopping_descriptions,
    'Rent': rent_descriptions,
    'Utilities': utilities_descriptions,
    'Health': health_descriptions,
    'Education': education_descriptions
}

# Generate expenses
start_date = current_date - timedelta(days=90)  # Last 3 months
expenses = []

for day_offset in range(90):
    expense_date = start_date + timedelta(days=day_offset)
    
    # Randomly decide if there's an expense on this day (70% chance)
    if random.random() < 0.7:
        category = random.choice(categories)
        descriptions = description_map.get(category, ['Expense'])
        description = random.choice(descriptions)
        
        # Amount ranges by category
        amount_ranges = {
            'Food': (5.00, 50.00),
            'Transport': (10.00, 40.00),
            'Entertainment': (10.00, 80.00),
            'Shopping': (20.00, 150.00),
            'Rent': (800.00, 800.00),
            'Utilities': (30.00, 120.00),
            'Health': (15.00, 100.00),
            'Education': (20.00, 200.00)
        }
        
        min_amount, max_amount = amount_ranges.get(category, (10.00, 50.00))
        amount = round(random.uniform(min_amount, max_amount), 2)
        
        # Rent and utilities only once per month
        if category == 'Rent' and expense_date.day != 1:
            continue
        if category == 'Utilities' and expense_date.day > 5:
            continue
        
        expenses.append((user_id, description, amount, category, expense_date.date().isoformat()))

# Insert expenses in batches
cursor.executemany('''
    INSERT INTO expense (user_id, description, amount, category, date)
    VALUES (?, ?, ?, ?, ?)
''', expenses)

# Commit and close
conn.commit()
conn.close()

print(f"✅ Example database 1 created: {DB_FILE}")
print(f"   - User: demo_user / demo123")
print(f"   - Expenses: {len(expenses)} transactions over last 3 months")
print(f"   - Budgets: {len(budgets)} categories set for current month")

