# REST API endpoints - returns JSON instead of templates
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from finance_app.database import get_db
from finance_app.models import User
from finance_app.utils import (
    format_currency, calculate_category_totals, calculate_monthly_totals,
    get_budget_status, get_weekly_comparison, get_monthly_total,
    get_top_categories, get_category_comparison, predict_budget_overrun,
    categorize_transaction
)
from datetime import datetime, timedelta
import csv
import io
import os
import json

api = Blueprint('api', __name__, url_prefix='/api')


# Use standard login_required - unauthorized handler will return JSON for API routes


def error_response(message, status_code=400):
    """Return error response"""
    return jsonify({'error': message}), status_code


def success_response(data, status_code=200):
    """Return success response"""
    return jsonify(data), status_code


@api.route('/auth/register', methods=['POST'])
def register():
    """User registration API"""
    data = request.get_json()
    
    if not data:
        return error_response('Invalid request data')
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    confirm_password = data.get('confirm_password', '').strip()
    
    # Validation
    if not username or len(username) < 3:
        return error_response('Username must be at least 3 characters')
    if not email or '@' not in email:
        return error_response('Invalid email address')
    if not password or len(password) < 6:
        return error_response('Password must be at least 6 characters')
    if password != confirm_password:
        return error_response('Passwords do not match')
    
    # Check if user exists
    if User.get_by_username(username):
        return error_response('Username already exists')
    if User.get_by_email(email):
        return error_response('Email already registered')
    
    # Create user
    try:
        user = User.create(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        login_user(user, remember=True)
        return success_response({
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, 201)
    except Exception as e:
        return error_response(f'Registration failed: {str(e)}', 500)


@api.route('/auth/login', methods=['POST'])
def login():
    """User login API"""
    data = request.get_json()
    
    if not data:
        return error_response('Invalid request data')
    
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return error_response('Username and password are required')
    
    user = User.get_by_username(username)
    if user and check_password_hash(user.password_hash, password):
        login_user(user, remember=True)
        return success_response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    else:
        return error_response('Invalid username or password', 401)


@api.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """User logout API"""
    logout_user()
    return success_response({'message': 'Logged out successfully'})


@api.route('/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if current_user.is_authenticated:
        return success_response({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email
            }
        })
    else:
        return success_response({'authenticated': False})


@api.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Get dashboard data"""
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year
    
    db = get_db()
    cursor = db.cursor()
    
    # Get all expenses
    cursor.execute('SELECT * FROM expense WHERE user_id = ? ORDER BY date DESC', (current_user.id,))
    expenses_rows = cursor.fetchall()
    expenses = [dict(row) for row in expenses_rows]
    
    # Calculate metrics
    this_week, last_week, week_change = get_weekly_comparison(current_user.id)
    monthly_total = get_monthly_total(current_user.id, current_month, current_year)
    top_categories = get_top_categories(current_user.id, current_month, current_year, limit=3)
    category_totals = calculate_category_totals(expenses)
    
    # Monthly trends
    monthly_trends = {}
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_key = f"{month_date.year}-{month_date.month:02d}"
        monthly_trends[month_key] = get_monthly_total(current_user.id, month_date.month, month_date.year)
    
    # Budget alerts
    cursor.execute('''
        SELECT * FROM budget 
        WHERE user_id = ? AND month = ? AND year = ?
    ''', (current_user.id, current_month, current_year))
    budgets_rows = cursor.fetchall()
    budgets = [dict(row) for row in budgets_rows]
    
    budget_alerts = []
    for budget in budgets:
        budget_amount, spent, remaining, percentage, is_over, is_warning = get_budget_status(
            current_user.id, budget['category'], current_month, current_year
        )
        if budget_amount is not None and (is_over or is_warning):
            budget_alerts.append({
                'category': budget['category'],
                'budget': budget_amount,
                'spent': spent,
                'remaining': remaining,
                'percentage': percentage,
                'is_over': is_over,
                'is_warning': is_warning
            })
    
    # Insights
    insights = []
    if top_categories:
        top_cats_str = ", ".join([cat for cat, _ in top_categories])
        insights.append(f"Your top 3 expense categories this month are {top_cats_str}.")
    
    if top_categories:
        for category, _ in top_categories[:2]:
            current, previous, change = get_category_comparison(current_user.id, category, current_month, current_year)
            if change != 0:
                direction = "more" if change > 0 else "less"
                insights.append(f"You spent {abs(change):.1f}% {direction} on {category} compared to last month.")
    
    for budget in budgets:
        will_exceed, projected, overrun = predict_budget_overrun(current_user.id, budget['category'], current_month, current_year)
        if will_exceed:
            insights.append(f"You are likely to exceed your budget for {budget['category']} if current pace continues. Projected overrun: {format_currency(overrun)}")
    
    # Recent expenses
    cursor.execute('''
        SELECT * FROM expense 
        WHERE user_id = ? 
        ORDER BY date DESC, created_at DESC 
        LIMIT 10
    ''', (current_user.id,))
    recent_expenses_rows = cursor.fetchall()
    recent_expenses = [dict(row) for row in recent_expenses_rows]
    
    return success_response({
        'this_week': this_week,
        'last_week': last_week,
        'week_change': week_change,
        'monthly_total': monthly_total,
        'top_categories': top_categories,
        'category_totals': category_totals,
        'monthly_trends': monthly_trends,
        'budget_alerts': budget_alerts,
        'insights': insights,
        'recent_expenses': recent_expenses
    })


@api.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    """Get or create expenses"""
    if request.method == 'GET':
        # Get expenses with filters
        search_query = request.args.get('search', '')
        category_filter = request.args.get('category', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        sort_by = request.args.get('sort', 'date_desc')
        
        db = get_db()
        cursor = db.cursor()
        query = 'SELECT * FROM expense WHERE user_id = ?'
        params = [current_user.id]
        
        if search_query:
            query += ' AND description LIKE ?'
            params.append(f'%{search_query}%')
        
        if category_filter:
            query += ' AND category = ?'
            params.append(category_filter)
        
        if date_from:
            query += ' AND date >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND date <= ?'
            params.append(date_to)
        
        # Sorting
        sort_map = {
            'date_asc': 'ORDER BY date ASC',
            'date_desc': 'ORDER BY date DESC',
            'amount_asc': 'ORDER BY amount ASC',
            'amount_desc': 'ORDER BY amount DESC',
            'category': 'ORDER BY category ASC'
        }
        query += ' ' + sort_map.get(sort_by, 'ORDER BY date DESC')
        
        cursor.execute(query, params)
        expenses_rows = cursor.fetchall()
        expenses = [dict(row) for row in expenses_rows]
        
        # Get categories
        cursor.execute('SELECT DISTINCT category FROM expense WHERE user_id = ?', (current_user.id,))
        categories_rows = cursor.fetchall()
        categories = [row['category'] for row in categories_rows]
        
        return success_response({
            'expenses': expenses,
            'categories': categories
        })
    
    else:  # POST
        data = request.get_json()
        if not data:
            return error_response('Invalid request data')
        
        description = data.get('description', '').strip()
        amount = data.get('amount')
        category = data.get('category', '').strip()
        date = data.get('date', '').strip()
        
        # Validation
        if not description:
            return error_response('Description is required')
        if not amount or amount <= 0:
            return error_response('Valid amount is required')
        if not category:
            return error_response('Category is required')
        if not date:
            return error_response('Date is required')
        
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO expense (user_id, description, amount, category, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (current_user.id, description, amount, category, date))
            db.commit()
            
            expense_id = cursor.lastrowid
            cursor.execute('SELECT * FROM expense WHERE id = ?', (expense_id,))
            expense = dict(cursor.fetchone())
            
            return success_response({'expense': expense}, 201)
        except Exception as e:
            return error_response(f'Failed to create expense: {str(e)}', 500)


@api.route('/expenses/<int:expense_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def expense(expense_id):
    """Get, update, or delete an expense"""
    db = get_db()
    cursor = db.cursor()
    
    # Get expense
    cursor.execute('SELECT * FROM expense WHERE id = ?', (expense_id,))
    expense_row = cursor.fetchone()
    
    if not expense_row:
        return error_response('Expense not found', 404)
    
    expense = dict(expense_row)
    
    # Check ownership
    if expense['user_id'] != current_user.id:
        return error_response('Permission denied', 403)
    
    if request.method == 'GET':
        return success_response({'expense': expense})
    
    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return error_response('Invalid request data')
        
        description = data.get('description', '').strip()
        amount = data.get('amount')
        category = data.get('category', '').strip()
        date = data.get('date', '').strip()
        
        if not description or not amount or not category or not date:
            return error_response('All fields are required')
        
        try:
            cursor.execute('''
                UPDATE expense 
                SET description = ?, amount = ?, category = ?, date = ?
                WHERE id = ? AND user_id = ?
            ''', (description, amount, category, date, expense_id, current_user.id))
            db.commit()
            
            cursor.execute('SELECT * FROM expense WHERE id = ?', (expense_id,))
            updated_expense = dict(cursor.fetchone())
            
            return success_response({'expense': updated_expense})
        except Exception as e:
            return error_response(f'Failed to update expense: {str(e)}', 500)
    
    else:  # DELETE
        try:
            cursor.execute('DELETE FROM expense WHERE id = ? AND user_id = ?', (expense_id, current_user.id))
            db.commit()
            return success_response({'message': 'Expense deleted successfully'})
        except Exception as e:
            return error_response(f'Failed to delete expense: {str(e)}', 500)


@api.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    """Get or create budgets"""
    if request.method == 'GET':
        today = datetime.now().date()
        current_month = today.month
        current_year = today.year
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT * FROM budget 
            WHERE user_id = ? AND month = ? AND year = ?
        ''', (current_user.id, current_month, current_year))
        budgets_rows = cursor.fetchall()
        budgets_list = [dict(row) for row in budgets_rows]
        
        # Get budget statuses
        budget_statuses = []
        for budget in budgets_list:
            budget_amount, spent, remaining, percentage, is_over, is_warning = get_budget_status(
                current_user.id, budget['category'], current_month, current_year
            )
            if budget_amount is not None:
                budget_statuses.append({
                    'budget': budget,
                    'amount': budget_amount,
                    'spent': spent,
                    'remaining': remaining,
                    'percentage': percentage,
                    'is_over': is_over,
                    'is_warning': is_warning
                })
        
        return success_response({'budgets': budget_statuses})
    
    else:  # POST
        data = request.get_json()
        if not data:
            return error_response('Invalid request data')
        
        category = data.get('category', '').strip()
        amount = data.get('amount')
        
        if not category:
            return error_response('Category is required')
        if not amount or amount <= 0:
            return error_response('Valid amount is required')
        
        today = datetime.now().date()
        month = today.month
        year = today.year
        
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Check if budget exists
            cursor.execute('''
                SELECT * FROM budget 
                WHERE user_id = ? AND category = ? AND month = ? AND year = ?
            ''', (current_user.id, category, month, year))
            existing_budget = cursor.fetchone()
            
            if existing_budget:
                # Update
                cursor.execute('''
                    UPDATE budget 
                    SET amount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND category = ? AND month = ? AND year = ?
                ''', (amount, current_user.id, category, month, year))
                message = 'Budget updated successfully'
            else:
                # Create
                cursor.execute('''
                    INSERT INTO budget (user_id, category, amount, month, year)
                    VALUES (?, ?, ?, ?, ?)
                ''', (current_user.id, category, amount, month, year))
                message = 'Budget set successfully'
            
            db.commit()
            
            cursor.execute('''
                SELECT * FROM budget 
                WHERE user_id = ? AND category = ? AND month = ? AND year = ?
            ''', (current_user.id, category, month, year))
            budget = dict(cursor.fetchone())
            
            return success_response({'budget': budget, 'message': message}, 201)
        except Exception as e:
            return error_response(f'Failed to set budget: {str(e)}', 500)


@api.route('/charts/category', methods=['GET'])
@login_required
def chart_category():
    """Get category chart data"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM expense WHERE user_id = ?', (current_user.id,))
    expenses_rows = cursor.fetchall()
    expenses = [dict(row) for row in expenses_rows]
    category_totals = calculate_category_totals(expenses)
    
    return success_response({
        'labels': list(category_totals.keys()),
        'data': list(category_totals.values())
    })


@api.route('/charts/monthly', methods=['GET'])
@login_required
def chart_monthly():
    """Get monthly trend chart data"""
    today = datetime.now().date()
    monthly_trends = {}
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_key = f"{month_date.strftime('%b %Y')}"
        monthly_trends[month_key] = get_monthly_total(current_user.id, month_date.month, month_date.year)
    
    return success_response({
        'labels': list(monthly_trends.keys()),
        'data': list(monthly_trends.values())
    })


@api.route('/export', methods=['GET'])
@login_required
def export():
    """Export expenses as CSV"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT * FROM expense 
        WHERE user_id = ? 
        ORDER BY date DESC
    ''', (current_user.id,))
    expenses_rows = cursor.fetchall()
    expenses = [dict(row) for row in expenses_rows]
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Description', 'Amount', 'Category', 'Date'])
    
    for expense in expenses:
        writer.writerow([
            expense['description'],
            expense['amount'],
            expense['category'],
            expense['date']
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'expenses_{datetime.now().strftime("%Y%m%d")}.csv'
    )


@api.route('/upload', methods=['POST'])
@login_required
def upload():
    """Upload and import CSV file"""
    if 'file' not in request.files:
        return error_response('No file provided')
    
    file = request.files['file']
    if file.filename == '':
        return error_response('No file selected')
    
    if not file.filename.endswith('.csv'):
        return error_response('Invalid file type. Please upload a CSV file')
    
    imported_count = 0
    errors = []
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Read CSV - handle both text and binary uploads
        file_content = file.read()
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8')
        stream = io.StringIO(file_content, newline=None)
        reader = csv.DictReader(stream)
        
        for row in reader:
            try:
                description = row.get('description', '').strip()
                amount_str = row.get('amount', '').strip()
                category = row.get('category', '').strip()
                date_str = row.get('date', '').strip()
                
                if not description or not amount_str:
                    errors.append(f"Row missing description or amount: {row}")
                    continue
                
                try:
                    amount = float(amount_str)
                except ValueError:
                    errors.append(f"Invalid amount in row: {row}")
                    continue
                
                if not category:
                    category = categorize_transaction(description, amount)
                
                try:
                    if date_str:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        date_obj = datetime.now().date()
                except ValueError:
                    date_obj = datetime.now().date()
                
                cursor.execute('''
                    INSERT INTO expense (user_id, description, amount, category, date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (current_user.id, description, amount, category, date_obj.isoformat()))
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error processing row {row}: {str(e)}")
        
        db.commit()
        
        return success_response({
            'imported_count': imported_count,
            'errors': errors[:10] if len(errors) > 10 else errors,  # Limit errors in response
            'error_count': len(errors),
            'message': f'Successfully imported {imported_count} expenses'
        })
        
    except Exception as e:
        return error_response(f'Error reading CSV file: {str(e)}', 500)

