# Small helper functions (e.g. format currency, calculate totals, etc.)
from datetime import datetime, timedelta
from finance_app.database import get_db
from collections import defaultdict


def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"


def calculate_category_totals(expenses):
    """Calculate total spending per category"""
    totals = defaultdict(float)
    for expense in expenses:
        totals[expense['category']] += expense['amount']
    return dict(totals)


def calculate_monthly_totals(expenses):
    """Calculate total spending per month"""
    totals = defaultdict(float)
    for expense in expenses:
        date_str = expense['date']
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date_obj = date_str
        key = f"{date_obj.year}-{date_obj.month:02d}"
        totals[key] += expense['amount']
    return dict(totals)


def get_budget_status(user_id, category, month, year):
    """Get budget status for a category in a given month"""
    db = get_db()
    cursor = db.cursor()
    
    # Get budget
    cursor.execute(
        'SELECT * FROM budget WHERE user_id = ? AND category = ? AND month = ? AND year = ?',
        (user_id, category, month, year)
    )
    budget_row = cursor.fetchone()
    
    if not budget_row:
        return None, None, None, None, None, None
    
    budget_amount = budget_row['amount']
    
    # Calculate total expenses for this category in this month
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE user_id = ? AND category = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
    ''', (user_id, category, f"{month:02d}", str(year)))
    
    result = cursor.fetchone()
    total_spent = result['total'] if result else 0.0
    
    remaining = budget_amount - total_spent
    percentage_spent = (total_spent / budget_amount) * 100 if budget_amount > 0 else 0
    is_over_budget = total_spent > budget_amount
    is_warning = percentage_spent >= 80 and not is_over_budget
    
    return budget_amount, total_spent, remaining, percentage_spent, is_over_budget, is_warning


def get_weekly_comparison(user_id):
    """Compare this week's spending to last week's"""
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    start_of_last_week = start_of_week - timedelta(days=7)
    end_of_last_week = start_of_last_week + timedelta(days=6)
    
    db = get_db()
    cursor = db.cursor()
    
    # This week
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE user_id = ? AND date >= ? AND date <= ?
    ''', (user_id, start_of_week.isoformat(), end_of_week.isoformat()))
    result = cursor.fetchone()
    this_week = result['total'] if result else 0.0
    
    # Last week
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE user_id = ? AND date >= ? AND date <= ?
    ''', (user_id, start_of_last_week.isoformat(), end_of_last_week.isoformat()))
    result = cursor.fetchone()
    last_week = result['total'] if result else 0.0
    
    if last_week == 0:
        change_percentage = 0 if this_week == 0 else 100
    else:
        change_percentage = ((this_week - last_week) / last_week) * 100
    
    return this_week, last_week, change_percentage


def get_monthly_total(user_id, month=None, year=None):
    """Get total spending for a specific month"""
    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
    ''', (user_id, f"{month:02d}", str(year)))
    
    result = cursor.fetchone()
    return result['total'] if result else 0.0


def get_top_categories(user_id, month=None, year=None, limit=3):
    """Get top N spending categories for a month"""
    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT category, SUM(amount) as total
        FROM expense
        WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
        GROUP BY category
        ORDER BY total DESC
        LIMIT ?
    ''', (user_id, f"{month:02d}", str(year), limit))
    
    results = cursor.fetchall()
    return [(row['category'], row['total']) for row in results]


def get_category_comparison(user_id, category, month=None, year=None):
    """Compare category spending between current and previous month"""
    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year
    
    db = get_db()
    cursor = db.cursor()
    
    # Current month
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE user_id = ? AND category = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
    ''', (user_id, category, f"{month:02d}", str(year)))
    result = cursor.fetchone()
    current_total = result['total'] if result else 0.0
    
    # Previous month
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE user_id = ? AND category = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
    ''', (user_id, category, f"{prev_month:02d}", str(prev_year)))
    result = cursor.fetchone()
    previous_total = result['total'] if result else 0.0
    
    if previous_total == 0:
        change_percentage = 0 if current_total == 0 else 100
    else:
        change_percentage = ((current_total - previous_total) / previous_total) * 100
    
    return current_total, previous_total, change_percentage


def predict_budget_overrun(user_id, category, month=None, year=None):
    """Predict if user will exceed budget based on current spending pace"""
    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year
    
    db = get_db()
    cursor = db.cursor()
    
    # Get budget
    cursor.execute(
        'SELECT * FROM budget WHERE user_id = ? AND category = ? AND month = ? AND year = ?',
        (user_id, category, month, year)
    )
    budget_row = cursor.fetchone()
    
    if not budget_row:
        return None, None, None
    
    budget_amount = budget_row['amount']
    
    # Get current date and days passed in month
    today = datetime.now().date()
    # Calculate days in month
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    days_in_month = (datetime(next_year, next_month, 1) - timedelta(days=1)).day
    days_passed = min(today.day, days_in_month)
    
    # Calculate current spending
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE user_id = ? AND category = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
    ''', (user_id, category, f"{month:02d}", str(year)))
    result = cursor.fetchone()
    current_spending = result['total'] if result else 0.0
    
    # Projected spending based on current pace
    if days_passed > 0:
        daily_average = current_spending / days_passed
        projected_total = daily_average * days_in_month
    else:
        projected_total = 0
    
    will_exceed = projected_total > budget_amount
    projected_overrun = projected_total - budget_amount if will_exceed else 0
    
    return will_exceed, projected_total, projected_overrun


def categorize_transaction(description, amount):
    """Auto-categorize transaction based on description keywords"""
    description_lower = description.lower()
    
    # Food keywords
    if any(keyword in description_lower for keyword in ['grocery', 'supermarket', 'restaurant', 'food', 'cafe', 'coffee', 'pizza', 'mcdonald', 'burger', 'starbucks']):
        return 'Food'
    
    # Transport keywords
    if any(keyword in description_lower for keyword in ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'metro', 'bus', 'train', 'parking', 'toll']):
        return 'Transport'
    
    # Entertainment keywords
    if any(keyword in description_lower for keyword in ['movie', 'cinema', 'netflix', 'spotify', 'game', 'concert', 'theater', 'entertainment']):
        return 'Entertainment'
    
    # Shopping keywords
    if any(keyword in description_lower for keyword in ['amazon', 'store', 'shop', 'mall', 'clothing', 'shoes', 'retail']):
        return 'Shopping'
    
    # Utilities keywords
    if any(keyword in description_lower for keyword in ['electric', 'water', 'gas bill', 'internet', 'phone', 'utility', 'power']):
        return 'Utilities'
    
    # Health keywords
    if any(keyword in description_lower for keyword in ['pharmacy', 'hospital', 'doctor', 'medical', 'drug', 'health']):
        return 'Health'
    
    # Travel keywords
    if any(keyword in description_lower for keyword in ['hotel', 'flight', 'airline', 'travel', 'vacation', 'trip']):
        return 'Travel'
    
    # Education keywords
    if any(keyword in description_lower for keyword in ['school', 'tuition', 'book', 'education', 'course', 'university']):
        return 'Education'
    
    # Rent keywords
    if any(keyword in description_lower for keyword in ['rent', 'lease', 'apartment', 'housing']):
        return 'Rent'
    
    # Default to Other
    return 'Other'
