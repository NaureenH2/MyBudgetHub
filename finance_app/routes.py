# Defines pages (e.g., /dashboard)
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from finance_app.database import get_db
from finance_app.models import User
from finance_app.forms import LoginForm, RegisterForm, ExpenseForm, BudgetForm, UploadForm
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

bp = Blueprint('routes', __name__)


@bp.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login"""
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    return redirect(url_for('routes.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('routes.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.get_by_username(form.username.data):
            flash('Username already exists. Please choose a different one.', 'error')
            return render_template('register.html', form=form)
        if User.get_by_email(form.email.data):
            flash('Email already registered. Please use a different one.', 'error')
            return render_template('register.html', form=form)
        
        user = User.create(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('routes.login'))
    
    return render_template('register.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('routes.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with charts and insights"""
    # Get current month and year
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year
    
    db = get_db()
    cursor = db.cursor()
    
    # Get all expenses for current user
    cursor.execute('SELECT * FROM expense WHERE user_id = ? ORDER BY date DESC', (current_user.id,))
    expenses_rows = cursor.fetchall()
    expenses = [dict(row) for row in expenses_rows]
    
    # Calculate weekly comparison
    this_week, last_week, week_change = get_weekly_comparison(current_user.id)
    
    # Get monthly total
    monthly_total = get_monthly_total(current_user.id, current_month, current_year)
    
    # Get top 3 categories this month
    top_categories = get_top_categories(current_user.id, current_month, current_year, limit=3)
    
    # Get category totals for pie chart
    category_totals = calculate_category_totals(expenses)
    
    # Get monthly trends for last 6 months
    monthly_trends = {}
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_key = f"{month_date.year}-{month_date.month:02d}"
        monthly_trends[month_key] = get_monthly_total(current_user.id, month_date.month, month_date.year)
    
    # Get budget alerts
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
    
    # Get intelligent insights
    insights = []
    
    # Top categories insight
    if top_categories:
        top_cats_str = ", ".join([cat for cat, _ in top_categories])
        insights.append(f"Your top 3 expense categories this month are {top_cats_str}.")
    
    # Category comparison insights
    if top_categories:
        for category, _ in top_categories[:2]:  # Check top 2 categories
            current, previous, change = get_category_comparison(current_user.id, category, current_month, current_year)
            if change != 0:
                direction = "more" if change > 0 else "less"
                insights.append(f"You spent {abs(change):.1f}% {direction} on {category} compared to last month.")
    
    # Budget prediction insights
    for budget in budgets:
        will_exceed, projected, overrun = predict_budget_overrun(current_user.id, budget['category'], current_month, current_year)
        if will_exceed:
            insights.append(f"You are likely to exceed your budget for {budget['category']} if current pace continues. Projected overrun: {format_currency(overrun)}")
    
    # Get recent expenses (last 10)
    cursor.execute('''
        SELECT * FROM expense 
        WHERE user_id = ? 
        ORDER BY date DESC, created_at DESC 
        LIMIT 10
    ''', (current_user.id,))
    recent_expenses_rows = cursor.fetchall()
    recent_expenses = [dict(row) for row in recent_expenses_rows]
    
    return render_template('dashboard.html',
                         expenses=recent_expenses,
                         this_week=this_week,
                         last_week=last_week,
                         week_change=week_change,
                         monthly_total=monthly_total,
                         top_categories=top_categories,
                         category_totals=category_totals,
                         monthly_trends=monthly_trends,
                         budget_alerts=budget_alerts,
                         insights=insights,
                         format_currency=format_currency)


@bp.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    """Expense management page with filtering and search"""
    form = ExpenseForm()
    
    # Handle form submission
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO expense (user_id, description, amount, category, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            current_user.id,
            form.description.data,
            form.amount.data,
            form.category.data,
            form.date.data.isoformat()
        ))
        db.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('routes.expenses'))
    
    # Get filter parameters
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    sort_by = request.args.get('sort', 'date_desc')
    
    # Build SQL query
    db = get_db()
    cursor = db.cursor()
    query = 'SELECT * FROM expense WHERE user_id = ?'
    params = [current_user.id]
    
    # Apply filters
    if search_query:
        query += ' AND description LIKE ?'
        params.append(f'%{search_query}%')
    
    if category_filter:
        query += ' AND category = ?'
        params.append(category_filter)
    
    if date_from:
        try:
            datetime.strptime(date_from, '%Y-%m-%d')
            query += ' AND date >= ?'
            params.append(date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            datetime.strptime(date_to, '%Y-%m-%d')
            query += ' AND date <= ?'
            params.append(date_to)
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == 'date_asc':
        query += ' ORDER BY date ASC'
    elif sort_by == 'date_desc':
        query += ' ORDER BY date DESC'
    elif sort_by == 'amount_asc':
        query += ' ORDER BY amount ASC'
    elif sort_by == 'amount_desc':
        query += ' ORDER BY amount DESC'
    elif sort_by == 'category':
        query += ' ORDER BY category ASC'
    else:
        query += ' ORDER BY date DESC'
    
    cursor.execute(query, params)
    expenses_rows = cursor.fetchall()
    expenses = [dict(row) for row in expenses_rows]
    
    # Get unique categories for filter dropdown
    cursor.execute('SELECT DISTINCT category FROM expense WHERE user_id = ?', (current_user.id,))
    categories_rows = cursor.fetchall()
    categories = [row['category'] for row in categories_rows]
    
    return render_template('budget.html',
                         form=form,
                         expenses=expenses,
                         categories=categories,
                         search_query=search_query,
                         category_filter=category_filter,
                         date_from=date_from,
                         date_to=date_to,
                         sort_by=sort_by,
                         format_currency=format_currency)


@bp.route('/expenses/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    """Edit an existing expense"""
    db = get_db()
    cursor = db.cursor()
    
    # Get expense
    cursor.execute('SELECT * FROM expense WHERE id = ?', (expense_id,))
    expense_row = cursor.fetchone()
    
    if not expense_row:
        flash('Expense not found.', 'error')
        return redirect(url_for('routes.expenses'))
    
    expense = dict(expense_row)
    
    # Check if expense belongs to current user
    if expense['user_id'] != current_user.id:
        flash('You do not have permission to edit this expense.', 'error')
        return redirect(url_for('routes.expenses'))
    
    # Create form with expense data
    form = ExpenseForm()
    if request.method == 'GET':
        form.description.data = expense['description']
        form.amount.data = expense['amount']
        form.category.data = expense['category']
        # Parse date string to date object
        if isinstance(expense['date'], str):
            form.date.data = datetime.strptime(expense['date'], '%Y-%m-%d').date()
        else:
            form.date.data = expense['date']
    
    if form.validate_on_submit():
        cursor.execute('''
            UPDATE expense 
            SET description = ?, amount = ?, category = ?, date = ?
            WHERE id = ? AND user_id = ?
        ''', (
            form.description.data,
            form.amount.data,
            form.category.data,
            form.date.data.isoformat(),
            expense_id,
            current_user.id
        ))
        db.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('routes.expenses'))
    
    # Get filter parameters for expenses list
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    sort_by = request.args.get('sort', 'date_desc')
    
    # Build query for expenses list
    query = 'SELECT * FROM expense WHERE user_id = ?'
    params = [current_user.id]
    
    if search_query:
        query += ' AND description LIKE ?'
        params.append(f'%{search_query}%')
    if category_filter:
        query += ' AND category = ?'
        params.append(category_filter)
    if date_from:
        try:
            datetime.strptime(date_from, '%Y-%m-%d')
            query += ' AND date >= ?'
            params.append(date_from)
        except ValueError:
            pass
    if date_to:
        try:
            datetime.strptime(date_to, '%Y-%m-%d')
            query += ' AND date <= ?'
            params.append(date_to)
        except ValueError:
            pass
    
    if sort_by == 'date_asc':
        query += ' ORDER BY date ASC'
    elif sort_by == 'date_desc':
        query += ' ORDER BY date DESC'
    elif sort_by == 'amount_asc':
        query += ' ORDER BY amount ASC'
    elif sort_by == 'amount_desc':
        query += ' ORDER BY amount DESC'
    elif sort_by == 'category':
        query += ' ORDER BY category ASC'
    else:
        query += ' ORDER BY date DESC'
    
    cursor.execute(query, params)
    expenses_rows = cursor.fetchall()
    expenses = [dict(row) for row in expenses_rows]
    
    cursor.execute('SELECT DISTINCT category FROM expense WHERE user_id = ?', (current_user.id,))
    categories_rows = cursor.fetchall()
    categories = [row['category'] for row in categories_rows]
    
    return render_template('budget.html', 
                         form=form, 
                         expense=expense, 
                         expenses=expenses,
                         categories=categories,
                         search_query=search_query,
                         category_filter=category_filter,
                         date_from=date_from,
                         date_to=date_to,
                         sort_by=sort_by,
                         edit_mode=True,
                         show_expenses=True,
                         format_currency=format_currency)


@bp.route('/expenses/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    """Delete an expense"""
    db = get_db()
    cursor = db.cursor()
    
    # Get expense and check ownership
    cursor.execute('SELECT * FROM expense WHERE id = ?', (expense_id,))
    expense_row = cursor.fetchone()
    
    if not expense_row:
        flash('Expense not found.', 'error')
        return redirect(url_for('routes.expenses'))
    
    expense = dict(expense_row)
    
    # Check if expense belongs to current user
    if expense['user_id'] != current_user.id:
        flash('You do not have permission to delete this expense.', 'error')
        return redirect(url_for('routes.expenses'))
    
    cursor.execute('DELETE FROM expense WHERE id = ? AND user_id = ?', (expense_id, current_user.id))
    db.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('routes.expenses'))


@bp.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    """Budget management page"""
    form = BudgetForm()
    
    # Handle form submission
    if request.method == 'POST':
        if form.validate_on_submit():
            today = datetime.now().date()
            month = today.month
            year = today.year
            
            db = get_db()
            cursor = db.cursor()
            
            # Check if budget already exists
            cursor.execute('''
                SELECT * FROM budget 
                WHERE user_id = ? AND category = ? AND month = ? AND year = ?
            ''', (current_user.id, form.category.data, month, year))
            existing_budget = cursor.fetchone()
            
            if existing_budget:
                # Update existing budget
                cursor.execute('''
                    UPDATE budget 
                    SET amount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND category = ? AND month = ? AND year = ?
                ''', (form.amount.data, current_user.id, form.category.data, month, year))
                flash('Budget updated successfully!', 'success')
            else:
                # Create new budget
                cursor.execute('''
                    INSERT INTO budget (user_id, category, amount, month, year)
                    VALUES (?, ?, ?, ?, ?)
                ''', (current_user.id, form.category.data, form.amount.data, month, year))
                flash('Budget set successfully!', 'success')
            
            db.commit()
            return redirect(url_for('routes.budgets'))
        else:
            # Form validation failed, continue to render template with errors
            pass
    
    # Get current month budgets
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
    
    # Get budget status for each
    budget_statuses = []
    for budget in budgets_list:
        budget_amount, spent, remaining, percentage, is_over, is_warning = get_budget_status(
            current_user.id, budget['category'], current_month, current_year
        )
        if budget_amount is not None:  # Only add if budget exists
            budget_statuses.append({
                'budget': budget,
                'amount': budget_amount,
                'spent': spent,
                'remaining': remaining,
                'percentage': percentage,
                'is_over': is_over,
                'is_warning': is_warning
            })
    
    return render_template('budget.html',
                         form=form,
                         budgets=budget_statuses,
                         format_currency=format_currency,
                         show_expenses=False)


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """CSV upload and import page"""
    form = UploadForm()
    
    if form.validate_on_submit():
        file = form.file.data
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Parse CSV
            imported_count = 0
            errors = []
            db = get_db()
            cursor = db.cursor()
            
            try:
                with open(filepath, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    for row in reader:
                        try:
                            # Get required fields
                            description = row.get('description', '').strip()
                            amount_str = row.get('amount', '').strip()
                            category = row.get('category', '').strip()
                            date_str = row.get('date', '').strip()
                            
                            if not description or not amount_str:
                                errors.append(f"Row missing description or amount: {row}")
                                continue
                            
                            # Parse amount
                            try:
                                amount = float(amount_str)
                            except ValueError:
                                errors.append(f"Invalid amount in row: {row}")
                                continue
                            
                            # Auto-categorize if category is missing
                            if not category:
                                category = categorize_transaction(description, amount)
                            
                            # Parse date
                            try:
                                if date_str:
                                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                                else:
                                    date_obj = datetime.now().date()
                            except ValueError:
                                date_obj = datetime.now().date()
                            
                            # Create expense
                            cursor.execute('''
                                INSERT INTO expense (user_id, description, amount, category, date)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (current_user.id, description, amount, category, date_obj.isoformat()))
                            imported_count += 1
                            
                        except Exception as e:
                            errors.append(f"Error processing row {row}: {str(e)}")
                            continue
                    
                    db.commit()
                    
                    if imported_count > 0:
                        flash(f'Successfully imported {imported_count} expenses!', 'success')
                    if errors:
                        flash(f'Encountered {len(errors)} errors during import.', 'warning')
                    
            except Exception as e:
                flash(f'Error reading CSV file: {str(e)}', 'error')
            finally:
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            return redirect(url_for('routes.upload'))
        else:
            flash('Please upload a valid CSV file.', 'error')
    
    return render_template('upload.html', form=form)


@bp.route('/export')
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
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Description', 'Amount', 'Category', 'Date'])
    
    # Write data
    for expense in expenses:
        writer.writerow([
            expense['description'],
            expense['amount'],
            expense['category'],
            expense['date']
        ])
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'expenses_{datetime.now().strftime("%Y%m%d")}.csv'
    )


@bp.route('/api/charts/category')
@login_required
def api_category_chart():
    """API endpoint for category pie chart data"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM expense WHERE user_id = ?', (current_user.id,))
    expenses_rows = cursor.fetchall()
    expenses = [dict(row) for row in expenses_rows]
    category_totals = calculate_category_totals(expenses)
    
    return jsonify({
        'labels': list(category_totals.keys()),
        'data': list(category_totals.values())
    })


@bp.route('/api/charts/monthly')
@login_required
def api_monthly_chart():
    """API endpoint for monthly trend line chart data"""
    today = datetime.now().date()
    monthly_trends = {}
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_key = f"{month_date.strftime('%b %Y')}"
        monthly_trends[month_key] = get_monthly_total(current_user.id, month_date.month, month_date.year)
    
    return jsonify({
        'labels': list(monthly_trends.keys()),
        'data': list(monthly_trends.values())
    })


@bp.route('/api/charts/category-monthly')
@login_required
def api_category_monthly_chart():
    """API endpoint for category monthly comparison bar chart"""
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year
    
    # Get last month
    prev_month = current_month - 1
    prev_year = current_year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    
    # Get categories
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT DISTINCT category FROM expense WHERE user_id = ?', (current_user.id,))
    categories_rows = cursor.fetchall()
    categories = [row['category'] for row in categories_rows]
    
    current_data = []
    previous_data = []
    
    for category in categories:
        # Get category-specific totals
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expense
            WHERE user_id = ? AND category = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
        ''', (current_user.id, category, f"{current_month:02d}", str(current_year)))
        result = cursor.fetchone()
        current_cat_total = result['total'] if result else 0.0
        
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expense
            WHERE user_id = ? AND category = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
        ''', (current_user.id, category, f"{prev_month:02d}", str(prev_year)))
        result = cursor.fetchone()
        previous_cat_total = result['total'] if result else 0.0
        
        current_data.append(current_cat_total)
        previous_data.append(previous_cat_total)
    
    return jsonify({
        'labels': categories,
        'current': current_data,
        'previous': previous_data
    })
