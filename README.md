# MyBudgetHub - Personal Finance Dashboard

A smart personal finance web application that helps you track expenses, visualize spending patterns, and manage budgets with interactive charts and intelligent data organization.

## 🎯 Features

- **💰 Expense Tracking**: Add, edit, and delete expenses with categories and dates
- **📊 Data Visualization**: Interactive pie charts for category spending and line graphs for monthly trends using Chart.js
- **🔔 Budget Alerts**: Automatic warnings when spending exceeds 80% of budget
- **🔍 Search & Filter**: Filter expenses by date range, category, or keyword
- **📁 CSV Import**: Upload bank statements (CSV format) and automatically parse transactions
- **💾 CSV Export**: Export all expense data as CSV
- **📈 Dashboard Summaries**: Weekly comparisons and monthly spending overviews

## 🚀 Tech Stack

- **Backend**: Python with Flask
- **Database**: SQLite (SQL)
- **Frontend**: JavaScript + Chart.js for interactive visualizations
- **Styling**: Modern CSS with gradient design

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/MyBudgetHub.git
   cd MyBudgetHub
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install Flask
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://127.0.0.1:5000`

## 📝 Usage

### Adding Expenses
- Fill out the expense form with description, amount, category, and date
- Click "Add Expense" to save
- Expenses are immediately reflected in the dashboard and charts

### Setting Budgets
- Select a category and enter a monthly budget amount
- Click "Set Budget" to save
- Budget alerts will appear when spending exceeds 80% of the budget

### Filtering Expenses
- Use the search box to find specific expenses by description
- Filter by category using the dropdown
- Set date ranges to view expenses within specific periods

### Importing CSV Files
The CSV should have the following columns:
- `description`: Description of the expense
- `amount`: Amount (numeric)
- `category`: Category name
- `date`: Date in YYYY-MM-DD format

Example CSV format:
```csv
description,amount,category,date
Groceries,125.50,Food,2024-10-15
Gas,45.00,Transport,2024-10-16
Movie,12.00,Entertainment,2024-10-17
```

### Exporting Data
- Click "Export to CSV" to download all expenses as a CSV file

## 🎨 Dashboard Features

1. **Summary Cards**: View this week's, last week's, and monthly spending totals
2. **Budget Alerts**: Red alerts for categories exceeding budget
3. **Category Pie Chart**: Visual breakdown of spending by category
4. **Trend Line Chart**: Monthly spending trends over the last 6 months
5. **Expense Table**: Complete list of all expenses with edit/delete options

## 💼 Resume Pitch

> "Built a personal finance dashboard with SQL-backed persistence, interactive data visualizations using Chart.js, and predictive analytics to forecast spending trends. Implemented CSV imports for bank statement parsing and anomaly detection to demonstrate backend automation and frontend data visualization. Features include budget tracking with alert systems, advanced filtering with SQL queries, and real-time expense management."

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Chart.js for beautiful data visualizations
- Flask for the backend framework
- SQLite for reliable data persistence

---

**Built with ❤️ for better financial management**
