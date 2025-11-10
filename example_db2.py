"""
Create Example Database 2 - Young Professional Profile
This database simulates a young professional with higher spending and more categories
"""
import sqlite3
from datetime import datetime, timedelta
import random

# Database file name
DB_FILE = 'example_db2.db'

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
user_password_hash = generate_password_hash('test123')
cursor.execute('''
    INSERT INTO user (username, email, password_hash)
    VALUES (?, ?, ?)
''', ('test_user', 'test@example.com', user_password_hash))
user_id = cursor.lastrowid

# Set budgets for current month (higher budgets for professional)
current_date = datetime.now()
current_month = current_date.month
current_year = current_date.year

budgets = [
    ('Food', 600.00),
    ('Transport', 250.00),
    ('Entertainment', 200.00),
    ('Shopping', 400.00),
    ('Rent', 1200.00),
    ('Utilities', 150.00),
    ('Travel', 500.00),
    ('Health', 150.00),
]

for category, amount in budgets:
    cursor.execute('''
        INSERT INTO budget (user_id, category, amount, month, year)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, category, amount, current_month, current_year))

# Generate expenses for the last 4 months
categories = ['Food', 'Transport', 'Entertainment', 'Shopping', 'Rent', 'Utilities', 'Health', 'Travel', 'Education']
food_descriptions = ['Fine Dining', 'Grocery Store', 'Coffee Shop', 'Lunch Meeting', 'Dinner Out', 'Food Delivery', 'Supermarket']
transport_descriptions = ['Gas Station', 'Uber', 'Parking', 'Metro', 'Taxi', 'Car Service', 'Flight']
entertainment_descriptions = ['Movie Theater', 'Netflix', 'Spotify', 'Concert', 'Theater', 'Sports Event', 'Gaming']
shopping_descriptions = ['Amazon', 'Clothing Store', 'Electronics', 'Online Purchase', 'Furniture', 'Tech Gadgets']
rent_descriptions = ['Monthly Rent', 'Apartment Rent']
utilities_descriptions = ['Electric Bill', 'Internet Bill', 'Phone Bill', 'Water Bill', 'Cable Bill']
health_descriptions = ['Pharmacy', 'Doctor Visit', 'Gym Membership', 'Yoga Class', 'Medical Checkup']
travel_descriptions = ['Hotel Booking', 'Flight Ticket', 'Car Rental', 'Vacation', 'Business Trip', 'Airbnb']
education_descriptions = ['Online Course', 'Workshop', 'Conference', 'Training', 'Certification']

description_map = {
    'Food': food_descriptions,
    'Transport': transport_descriptions,
    'Entertainment': entertainment_descriptions,
    'Shopping': shopping_descriptions,
    'Rent': rent_descriptions,
    'Utilities': utilities_descriptions,
    'Health': health_descriptions,
    'Travel': travel_descriptions,
    'Education': education_descriptions
}

# Generate expenses
start_date = current_date - timedelta(days=120)  # Last 4 months
expenses = []

for day_offset in range(120):
    expense_date = start_date + timedelta(days=day_offset)
    
    # Randomly decide if there's an expense on this day (80% chance - more active)
    if random.random() < 0.8:
        # Some days have multiple expenses
        num_expenses = 1
        if random.random() < 0.3:  # 30% chance of 2 expenses
            num_expenses = 2
        elif random.random() < 0.1:  # 10% chance of 3 expenses
            num_expenses = 3
        
        for _ in range(num_expenses):
            category = random.choice(categories)
            descriptions = description_map.get(category, ['Expense'])
            description = random.choice(descriptions)
            
            # Higher amount ranges for professional
            amount_ranges = {
                'Food': (10.00, 120.00),
                'Transport': (15.00, 80.00),
                'Entertainment': (20.00, 150.00),
                'Shopping': (30.00, 300.00),
                'Rent': (1200.00, 1200.00),
                'Utilities': (50.00, 200.00),
                'Health': (25.00, 200.00),
                'Travel': (100.00, 800.00),
                'Education': (50.00, 500.00)
            }
            
            min_amount, max_amount = amount_ranges.get(category, (20.00, 100.00))
            amount = round(random.uniform(min_amount, max_amount), 2)
            
            # Rent only on 1st of month
            if category == 'Rent' and expense_date.day != 1:
                continue
            # Utilities around 5th of month
            if category == 'Utilities' and (expense_date.day < 3 or expense_date.day > 7):
                continue
            # Travel expenses are less frequent
            if category == 'Travel' and random.random() > 0.15:
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

print(f"✅ Example database 2 created: {DB_FILE}")
print(f"   - User: test_user / test123")
print(f"   - Expenses: {len(expenses)} transactions over last 4 months")
print(f"   - Budgets: {len(budgets)} categories set for current month")
print(f"   - Note: This profile has higher spending and more frequent transactions")

