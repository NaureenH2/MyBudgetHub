# Migration from Jinja2 to Pure JavaScript Frontend

This document explains the migration from Jinja2 templating to a pure JavaScript frontend with REST API backend.

## Architecture Changes

### Before (Jinja2)
- Flask routes rendered HTML templates with server-side data
- Templates used Jinja2 syntax for data binding
- Server-side template rendering

### After (Pure JavaScript)
- Flask routes return JSON data via REST API
- Static HTML files served from `/static` directory
- JavaScript fetches data from API and renders client-side
- No server-side templating

## File Structure

### Backend (Python/Flask)
- `finance_app/api.py` - REST API endpoints (new)
- `finance_app/routes.py` - Old template routes (can be removed)
- `finance_app/__init__.py` - Updated to serve static files
- `finance_app/models.py` - User model (updated)
- `finance_app/database.py` - Database setup (unchanged)
- `finance_app/utils.py` - Utility functions (unchanged)
- `finance_app/forms.py` - Forms (no longer used in API)

### Frontend (JavaScript/HTML)
- `static/index.html` - Home page
- `static/login.html` - Login page
- `static/register.html` - Register page
- `static/dashboard.html` - Dashboard page
- `static/expenses.html` - Expenses management page
- `static/budgets.html` - Budgets management page
- `static/upload.html` - CSV upload page
- `static/api.js` - API client for making requests
- `static/app.js` - Main app initialization
- `static/login.js` - Login page logic
- `static/register.js` - Register page logic
- `static/dashboard.js` - Dashboard page logic
- `static/expenses.js` - Expenses page logic
- `static/budgets.js` - Budgets page logic
- `static/upload.js` - Upload page logic
- `static/charts.js` - Chart initialization (updated)
- `static/style.css` - Styles (unchanged)

## API Endpoints

All API endpoints are under `/api/`:

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/check` - Check authentication status

### Dashboard
- `GET /api/dashboard` - Get dashboard data

### Expenses
- `GET /api/expenses` - Get expenses (with filters)
- `POST /api/expenses` - Create expense
- `GET /api/expenses/<id>` - Get single expense
- `PUT /api/expenses/<id>` - Update expense
- `DELETE /api/expenses/<id>` - Delete expense

### Budgets
- `GET /api/budgets` - Get budgets
- `POST /api/budgets` - Create/update budget

### Charts
- `GET /api/charts/category` - Get category chart data
- `GET /api/charts/monthly` - Get monthly trend data

### Other
- `GET /api/export` - Export expenses as CSV
- `POST /api/upload` - Upload and import CSV

## How to Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python app.py
   ```

3. **Open your browser**:
   Navigate to `http://127.0.0.1:5000`

## Key Changes

1. **No Jinja2**: All templates removed, replaced with static HTML
2. **REST API**: All data access through JSON API endpoints
3. **Client-side rendering**: JavaScript renders all dynamic content
4. **Session-based auth**: Flask-Login handles sessions, API checks authentication
5. **Static file serving**: Flask serves HTML/CSS/JS files directly

## Benefits

- ✅ Separation of concerns (frontend/backend)
- ✅ Can easily swap frontend framework (React, Vue, etc.)
- ✅ API can be used by mobile apps or other clients
- ✅ Better performance (static file serving)
- ✅ Easier to test (API endpoints)
- ✅ No server-side template rendering overhead

## Migration Notes

- Old template files in `templates/` directory are no longer used
- `finance_app/routes.py` can be removed (functionality moved to `api.py`)
- `finance_app/forms.py` is no longer used (validation done in API)
- All data formatting (currency, dates) now happens in JavaScript
- Authentication still uses Flask-Login sessions (cookies)

## Testing

To test the API directly:

```bash
# Login
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_user","password":"demo123"}' \
  -c cookies.txt

# Get dashboard data
curl http://127.0.0.1:5000/api/dashboard -b cookies.txt

# Get expenses
curl http://127.0.0.1:5000/api/expenses -b cookies.txt
```

