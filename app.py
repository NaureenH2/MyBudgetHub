from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import csv
import io
from datetime import datetime, timedelta
from collections import defaultdict

# Create the Flask app
app = Flask(__name__)
app.config['DATABASE'] = 'budget.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Create expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create budgets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE,
            monthly_budget REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Define routes
@app.route('/')
def index():
    """Home page with dashboard"""
    return render_template('index.html')

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """Get all expenses with optional filters"""
    conn = get_db()
    cursor = conn.cursor()
    
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search')
    
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if search:
        query += " AND description LIKE ?"
        params.append(f"%{search}%")
    
    query += " ORDER BY date DESC"
    
    cursor.execute(query, params)
    expenses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(expenses)

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    """Add a new expense"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO expenses (description, amount, category, date)
        VALUES (?, ?, ?, ?)
    ''', (data['description'], data['amount'], data['category'], data['date']))
    
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'id': expense_id, 'message': 'Expense added successfully'}), 201

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """Update an existing expense"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE expenses 
        SET description = ?, amount = ?, category = ?, date = ?
        WHERE id = ?
    ''', (data['description'], data['amount'], data['category'], data['date'], expense_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Expense updated successfully'})

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Delete an expense"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Expense deleted successfully'})

@app.route('/api/budgets', methods=['GET'])
def get_budgets():
    """Get all budgets"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM budgets')
    budgets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(budgets)

@app.route('/api/budgets', methods=['POST'])
def add_budget():
    """Add a new budget"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO budgets (category, monthly_budget)
        VALUES (?, ?)
    ''', (data['category'], data['monthly_budget']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Budget added successfully'}), 201

@app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    """Delete a budget"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM budgets WHERE id = ?', (budget_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Budget deleted successfully'})

@app.route('/api/stats/category-spending', methods=['GET'])
def get_category_spending():
    """Get spending by category for the current month"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current month's expenses
    today = datetime.now()
    first_day = today.replace(day=1).strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE date >= ?
        GROUP BY category
    ''', (first_day,))
    
    data = cursor.fetchall()
    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]
    
    conn.close()
    
    return jsonify({'categories': categories, 'amounts': amounts})

@app.route('/api/stats/monthly-trends', methods=['GET'])
def get_monthly_trends():
    """Get monthly spending trends"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get last 6 months of data
    six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total
        FROM expenses
        WHERE date >= ?
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
    ''', (six_months_ago,))
    
    data = cursor.fetchall()
    months = [row[0] for row in data]
    totals = [row[1] for row in data]
    
    conn.close()
    
    return jsonify({'months': months, 'totals': totals})

@app.route('/api/stats/budget-alerts', methods=['GET'])
def get_budget_alerts():
    """Get budget alerts for categories where spending exceeds 80%"""
    conn = get_db()
    cursor = conn.cursor()
    
    today = datetime.now()
    first_day = today.replace(day=1).strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT category, SUM(amount) as spent
        FROM expenses
        WHERE date >= ?
        GROUP BY category
    ''', (first_day,))
    
    spent = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute('SELECT category, monthly_budget FROM budgets')
    budgets_data = cursor.fetchall()
    conn.close()
    
    alerts = []
    for category, budget in budgets_data:
        if category in spent:
            percentage = (spent[category] / budget) * 100
            if percentage >= 80:
                alerts.append({
                    'category': category,
                    'spent': spent[category],
                    'budget': budget,
                    'percentage': percentage
                })
    
    return jsonify(alerts)

@app.route('/api/stats/dashboard-summary', methods=['GET'])
def get_dashboard_summary():
    """Get dashboard summary statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    two_weeks_ago = today - timedelta(days=14)
    
    # This week's spending
    cursor.execute('''
        SELECT SUM(amount) as total
        FROM expenses
        WHERE date >= ?
    ''', (week_ago.strftime('%Y-%m-%d'),))
    
    this_week = cursor.fetchone()[0] or 0
    
    # Last week's spending
    cursor.execute('''
        SELECT SUM(amount) as total
        FROM expenses
        WHERE date >= ? AND date < ?
    ''', (two_weeks_ago.strftime('%Y-%m-%d'), week_ago.strftime('%Y-%m-%d')))
    
    last_week = cursor.fetchone()[0] or 0
    
    # Monthly total
    first_day = today.replace(day=1).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT SUM(amount) as total
        FROM expenses
        WHERE date >= ?
    ''', (first_day,))
    
    monthly_total = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        'this_week': this_week,
        'last_week': last_week,
        'monthly_total': monthly_total
    })

@app.route('/api/import-csv', methods=['POST'])
def import_csv():
    """Import expenses from CSV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_reader = csv.DictReader(stream)
    
    conn = get_db()
    cursor = conn.cursor()
    
    imported = 0
    for row in csv_reader:
        try:
            # Expected CSV columns: description, amount, category, date
            description = row.get('description', '')
            amount = float(row.get('amount', 0))
            category = row.get('category', 'Other')
            date = row.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            cursor.execute('''
                INSERT INTO expenses (description, amount, category, date)
                VALUES (?, ?, ?, ?)
            ''', (description, amount, category, date))
            
            imported += 1
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': f'Imported {imported} expenses successfully'})

@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    """Export expenses to CSV file"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM expenses ORDER BY date DESC')
    expenses = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['id', 'description', 'amount', 'category', 'date', 'created_at'])
    
    # Write data
    for expense in expenses:
        writer.writerow(expense)
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='expenses_export.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)
