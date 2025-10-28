// Global variables for charts
let categoryChart = null;
let trendChart = null;

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardSummary();
    loadBudgetAlerts();
    loadExpenses();
    loadBudgets();
    setupEventListeners();
    setDefaultDate();
});

// Set today's date as default
function setDefaultDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('date').value = today;
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('expenseForm').addEventListener('submit', handleAddExpense);
    document.getElementById('budgetForm').addEventListener('submit', handleAddBudget);
    document.getElementById('importForm').addEventListener('submit', handleImportCSV);
}

// Load dashboard summary
async function loadDashboardSummary() {
    try {
        const response = await fetch('/api/stats/dashboard-summary');
        const data = await response.json();
        
        document.getElementById('thisWeek').textContent = `$${data.this_week.toFixed(2)}`;
        document.getElementById('lastWeek').textContent = `$${data.last_week.toFixed(2)}`;
        document.getElementById('monthlyTotal').textContent = `$${data.monthly_total.toFixed(2)}`;
        
        // Calculate trend
        const trendElement = document.getElementById('weekTrend');
        if (data.last_week > 0) {
            const change = ((data.this_week - data.last_week) / data.last_week) * 100;
            if (change > 0) {
                trendElement.textContent = `↑ ${Math.abs(change).toFixed(1)}%`;
                trendElement.className = 'trend positive';
            } else {
                trendElement.textContent = `↓ ${Math.abs(change).toFixed(1)}%`;
                trendElement.className = 'trend negative';
            }
        } else {
            trendElement.textContent = '-';
        }
    } catch (error) {
        console.error('Error loading dashboard summary:', error);
    }
}

// Load budget alerts
async function loadBudgetAlerts() {
    try {
        const response = await fetch('/api/stats/budget-alerts');
        const alerts = await response.json();
        
        const alertsContainer = document.getElementById('budgetAlerts');
        alertsContainer.innerHTML = '';
        
        if (alerts.length === 0) {
            alertsContainer.innerHTML = '<p style="color: #51cf66;">✓ No budget alerts. You\'re on track!</p>';
            return;
        }
        
        alerts.forEach(alert => {
            const alertCard = document.createElement('div');
            alertCard.className = alert.percentage >= 100 ? 'alert-card critical' : 'alert-card';
            
            const percentageColor = alert.percentage >= 100 ? '#dc3545' : '#ffc107';
            
            alertCard.innerHTML = `
                <h4>${alert.category}</h4>
                <p>Spent: $${alert.spent.toFixed(2)} / Budget: $${alert.budget.toFixed(2)}</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.min(alert.percentage, 100)}%; background: ${percentageColor};"></div>
                </div>
                <p style="margin-top: 5px; color: ${percentageColor}; font-weight: bold;">
                    ${alert.percentage.toFixed(1)}% of budget used
                </p>
            `;
            
            alertsContainer.appendChild(alertCard);
        });
    } catch (error) {
        console.error('Error loading budget alerts:', error);
    }
}

// Load and display category spending chart
async function loadCategoryChart() {
    try {
        const response = await fetch('/api/stats/category-spending');
        const data = await response.json();
        
        const ctx = document.getElementById('categoryChart').getContext('2d');
        
        if (categoryChart) {
            categoryChart.destroy();
        }
        
        categoryChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.categories,
                datasets: [{
                    label: 'Spending',
                    data: data.amounts,
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#4facfe',
                        '#43e97b',
                        '#fa709a',
                        '#30cfd0',
                        '#a8edea'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading category chart:', error);
    }
}

// Load and display monthly trends chart
async function loadTrendChart() {
    try {
        const response = await fetch('/api/stats/monthly-trends');
        const data = await response.json();
        
        const ctx = document.getElementById('trendChart').getContext('2d');
        
        if (trendChart) {
            trendChart.destroy();
        }
        
        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.months,
                datasets: [{
                    label: 'Monthly Spending',
                    data: data.totals,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading trend chart:', error);
    }
}

// Load expenses with filters
async function loadExpenses() {
    try {
        const category = document.getElementById('categoryFilter').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const search = document.getElementById('searchInput').value;
        
        let url = '/api/expenses?';
        if (category) url += `category=${category}&`;
        if (startDate) url += `start_date=${startDate}&`;
        if (endDate) url += `end_date=${endDate}&`;
        if (search) url += `search=${search}&`;
        
        const response = await fetch(url);
        const expenses = await response.json();
        
        displayExpenses(expenses);
        
        // Load charts after expenses are loaded
        loadCategoryChart();
        loadTrendChart();
    } catch (error) {
        console.error('Error loading expenses:', error);
    }
}

// Display expenses in table
function displayExpenses(expenses) {
    const tableContainer = document.getElementById('expensesTable');
    
    if (expenses.length === 0) {
        tableContainer.innerHTML = '<p>No expenses found.</p>';
        return;
    }
    
    let html = '<table><thead><tr><th>Date</th><th>Description</th><th>Amount</th><th>Category</th><th>Actions</th></tr></thead><tbody>';
    
    expenses.forEach(expense => {
        html += `
            <tr>
                <td>${expense.date}</td>
                <td>${expense.description}</td>
                <td>$${expense.amount.toFixed(2)}</td>
                <td>${expense.category}</td>
                <td class="action-buttons">
                    <button class="btn-small btn-edit" onclick="editExpense(${expense.id})">Edit</button>
                    <button class="btn-small btn-delete" onclick="deleteExpense(${expense.id})">Delete</button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

// Load budgets
async function loadBudgets() {
    try {
        const response = await fetch('/api/budgets');
        const budgets = await response.json();
        
        displayBudgets(budgets);
        
        // Populate category filter
        const categoryFilter = document.getElementById('categoryFilter');
        const categories = ['Food', 'Transport', 'Entertainment', 'Bills', 'Shopping', 'Healthcare', 'Education', 'Other'];
        
        // Keep only the "All Categories" option and add other options
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        
        categories.forEach(cat => {
            if (!budgets.find(b => b.category === cat)) {
                const option = document.createElement('option');
                option.value = cat;
                option.textContent = cat;
                categoryFilter.appendChild(option);
            }
        });
        
        budgets.forEach(budget => {
            const option = document.createElement('option');
            option.value = budget.category;
            option.textContent = budget.category;
            categoryFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading budgets:', error);
    }
}

// Display budgets
function displayBudgets(budgets) {
    const budgetsList = document.getElementById('budgetsList');
    
    if (budgets.length === 0) {
        budgetsList.innerHTML = '<p>No budgets set.</p>';
        return;
    }
    
    let html = '';
    budgets.forEach(budget => {
        html += `
            <div class="budget-item">
                <div class="budget-info">
                    <strong>${budget.category}</strong>: 
                    <span class="budget-amount">$${budget.monthly_budget.toFixed(2)}/month</span>
                </div>
                <button class="btn-small btn-delete" onclick="deleteBudget(${budget.id})">Delete</button>
            </div>
        `;
    });
    
    budgetsList.innerHTML = html;
}

// Handle add expense
async function handleAddExpense(event) {
    event.preventDefault();
    
    const expense = {
        description: document.getElementById('description').value,
        amount: parseFloat(document.getElementById('amount').value),
        category: document.getElementById('category').value,
        date: document.getElementById('date').value
    };
    
    try {
        const response = await fetch('/api/expenses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(expense)
        });
        
        if (response.ok) {
            document.getElementById('expenseForm').reset();
            setDefaultDate();
            loadExpenses();
            loadDashboardSummary();
            loadBudgetAlerts();
            alert('Expense added successfully!');
        }
    } catch (error) {
        console.error('Error adding expense:', error);
        alert('Error adding expense');
    }
}

// Handle add budget
async function handleAddBudget(event) {
    event.preventDefault();
    
    const budget = {
        category: document.getElementById('budgetCategory').value,
        monthly_budget: parseFloat(document.getElementById('monthlyBudget').value)
    };
    
    try {
        const response = await fetch('/api/budgets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(budget)
        });
        
        if (response.ok) {
            document.getElementById('budgetForm').reset();
            loadBudgets();
            loadBudgetAlerts();
            alert('Budget set successfully!');
        }
    } catch (error) {
        console.error('Error adding budget:', error);
        alert('Error setting budget');
    }
}

// Delete expense
async function deleteExpense(id) {
    if (!confirm('Are you sure you want to delete this expense?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/expenses/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadExpenses();
            loadDashboardSummary();
            loadBudgetAlerts();
            alert('Expense deleted successfully!');
        }
    } catch (error) {
        console.error('Error deleting expense:', error);
        alert('Error deleting expense');
    }
}

// Edit expense
async function editExpense(id) {
    // Get expense details and populate form
    const expenses = await fetch('/api/expenses').then(r => r.json());
    const expense = expenses.find(e => e.id === id);
    
    if (expense) {
        document.getElementById('description').value = expense.description;
        document.getElementById('amount').value = expense.amount;
        document.getElementById('category').value = expense.category;
        document.getElementById('date').value = expense.date;
        
        // Scroll to form
        document.getElementById('expenseForm').scrollIntoView({ behavior: 'smooth' });
        
        // Remove the old expense
        deleteExpense(id);
    }
}

// Delete budget
async function deleteBudget(id) {
    if (!confirm('Are you sure you want to delete this budget?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/budgets/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadBudgets();
            loadBudgetAlerts();
            alert('Budget deleted successfully!');
        }
    } catch (error) {
        console.error('Error deleting budget:', error);
        alert('Error deleting budget');
    }
}

// Apply filters
function applyFilters() {
    loadExpenses();
}

// Reset filters
function resetFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    loadExpenses();
}

// Handle CSV import
async function handleImportCSV(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a CSV file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/import-csv', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            alert(result.message);
            fileInput.value = '';
            loadExpenses();
            loadDashboardSummary();
            loadBudgetAlerts();
        } else {
            alert('Error importing CSV');
        }
    } catch (error) {
        console.error('Error importing CSV:', error);
        alert('Error importing CSV');
    }
}

// Export CSV
function exportCSV() {
    window.location.href = '/api/export-csv';
}

