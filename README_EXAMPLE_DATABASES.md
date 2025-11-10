# Example Databases

This directory contains scripts to create example databases for testing and demonstration purposes.

## Database 1: Student/Freelancer Profile (`example_db1.db`)

**Profile**: Moderate spending, typical student or freelancer lifestyle

### Credentials:
- **Username**: `demo_user`
- **Password**: `demo123`
- **Email**: `demo@example.com`

### Characteristics:
- **Budget Categories**: Food ($400), Transport ($150), Entertainment ($100), Shopping ($200), Rent ($800), Utilities ($100)
- **Expenses**: ~90 transactions over the last 3 months
- **Spending Pattern**: Moderate, realistic daily expenses
- **Categories**: Food, Transport, Entertainment, Shopping, Rent, Utilities, Health, Education

### Use Case:
Perfect for testing budget alerts, category filtering, and expense tracking with realistic but moderate spending patterns.

---

## Database 2: Young Professional Profile (`example_db2.db`)

**Profile**: Higher spending, active professional lifestyle

### Credentials:
- **Username**: `test_user`
- **Password**: `test123`
- **Email**: `test@example.com`

### Characteristics:
- **Budget Categories**: Food ($600), Transport ($250), Entertainment ($200), Shopping ($400), Rent ($1200), Utilities ($150), Travel ($500), Health ($150)
- **Expenses**: ~150+ transactions over the last 4 months
- **Spending Pattern**: Higher frequency, larger amounts, more diverse categories
- **Categories**: All categories including Travel

### Use Case:
Ideal for testing:
- Budget overrun scenarios
- Complex filtering and search
- Monthly trend analysis
- Category comparisons
- Travel expense tracking

---

## How to Create Example Databases

### Option 1: Using Python Scripts

1. **Create Database 1 (Student/Freelancer)**:
   ```bash
   python create_example_db1.py
   ```

2. **Create Database 2 (Young Professional)**:
   ```bash
   python create_example_db2.py
   ```

### Option 2: Using the Application

1. Start the Flask application:
   ```bash
   python app.py
   ```

2. Register a new account or use the demo credentials
3. Add expenses manually or upload a CSV file
4. Set budgets for different categories

---

## Using Example Databases

### To use an example database with your application:

1. **Backup your current database** (if you have one):
   ```bash
   cp finance_app.db finance_app.db.backup
   ```

2. **Replace with example database**:
   ```bash
   cp example_db1.db finance_app.db
   # or
   cp example_db2.db finance_app.db
   ```

3. **Start the application**:
   ```bash
   python app.py
   ```

4. **Login with the example credentials**:
   - Database 1: `demo_user` / `demo123`
   - Database 2: `test_user` / `test123`

### To use a specific database file:

You can also set the `DATABASE_URL` environment variable:

```bash
# Windows
set DATABASE_URL=example_db1.db
python app.py

# Mac/Linux
export DATABASE_URL=example_db1.db
python app.py
```

---

## Database Schema

Both databases use the same schema:

### Tables:
- **user**: User accounts with authentication
- **expense**: Expense transactions with categories and dates
- **budget**: Monthly budget limits per category

### Indexes:
- Indexes on `user_id`, `date`, and `category` for fast queries
- Indexes on budget `month` and `year` for efficient filtering

---

## Data Features

### Realistic Data:
- ✅ Varied transaction amounts
- ✅ Realistic descriptions (e.g., "Coffee Shop", "Gas Station")
- ✅ Proper date distribution over months
- ✅ Category-appropriate descriptions
- ✅ Monthly recurring expenses (Rent, Utilities)

### Testing Scenarios:
- ✅ Budget alerts (some categories may exceed budgets)
- ✅ Date range filtering
- ✅ Category filtering
- ✅ Search functionality
- ✅ Monthly trends and comparisons
- ✅ CSV export/import

---

## Notes

- Both databases use hashed passwords (Werkzeug security)
- Dates are stored in ISO format (YYYY-MM-DD)
- All amounts are in USD
- Expenses are randomly generated but follow realistic patterns
- Budgets are set for the current month only

---

## Troubleshooting

### Database locked error:
- Make sure the Flask application is not running
- Close any database connections
- Delete the database file and recreate it

### Cannot login:
- Verify you're using the correct credentials
- Check that the password hash was generated correctly
- Try recreating the database

### No data showing:
- Verify the database file is in the correct location
- Check that expenses were inserted successfully
- Verify the user_id matches between tables

---

## Customization

You can modify the scripts to:
- Change spending amounts and frequencies
- Add more categories
- Adjust date ranges
- Modify budget amounts
- Add custom descriptions

Edit the Python scripts and run them again to generate custom databases.

