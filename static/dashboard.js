// Dashboard page functionality
let categoryChart = null;
let monthlyChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const user = await checkAuthentication();
    if (!user) {
        redirectTo('/login.html');
        return;
    }

    // Load dashboard data
    await loadDashboard();
});

async function loadDashboard() {
    try {
        const data = await API.getDashboard();
        
        // Update summary cards
        document.getElementById('thisWeek').textContent = formatCurrency(data.this_week);
        document.getElementById('lastWeek').textContent = formatCurrency(data.last_week);
        
        const weekChangeEl = document.getElementById('weekChange');
        if (data.week_change !== 0) {
            weekChangeEl.textContent = `${data.week_change.toFixed(1)}% vs last week`;
            weekChangeEl.className = `change ${data.week_change > 0 ? 'positive' : 'negative'}`;
            weekChangeEl.style.display = 'block';
        } else {
            weekChangeEl.style.display = 'none';
        }
        
        document.getElementById('monthlyTotal').textContent = formatCurrency(data.monthly_total);
        
        // Budget alerts
        if (data.budget_alerts && data.budget_alerts.length > 0) {
            const alertsDiv = document.getElementById('budgetAlerts');
            const alertsList = document.getElementById('alertsList');
            alertsDiv.style.display = 'block';
            alertsList.innerHTML = '';
            
            data.budget_alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert ${alert.is_over ? 'alert-danger' : 'alert-warning'}`;
                alertDiv.innerHTML = `
                    <strong>${alert.category}:</strong> 
                    Spent ${formatCurrency(alert.spent)} of ${formatCurrency(alert.budget)} 
                    (${alert.percentage.toFixed(1)}%)
                    ${alert.is_over ? 
                        `- Over budget by ${formatCurrency(Math.abs(alert.remaining))}` : 
                        `- Warning: ${(100 - alert.percentage).toFixed(1)}% remaining`
                    }
                `;
                alertsList.appendChild(alertDiv);
            });
        }
        
        // Insights
        if (data.insights && data.insights.length > 0) {
            const insightsDiv = document.getElementById('insights');
            const insightsList = document.getElementById('insightsList');
            insightsDiv.style.display = 'block';
            insightsList.innerHTML = '';
            
            data.insights.forEach(insight => {
                const li = document.createElement('li');
                li.textContent = insight;
                insightsList.appendChild(li);
            });
        }
        
        // Recent expenses
        const recentExpensesDiv = document.getElementById('recentExpenses');
        if (data.recent_expenses && data.recent_expenses.length > 0) {
            let html = `
                <table class="expense-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Description</th>
                            <th>Category</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.recent_expenses.forEach(expense => {
                html += `
                    <tr>
                        <td>${expense.date}</td>
                        <td>${expense.description}</td>
                        <td><span class="category-badge">${expense.category}</span></td>
                        <td>${formatCurrency(expense.amount)}</td>
                    </tr>
                `;
            });
            
            html += `
                    </tbody>
                </table>
            `;
            recentExpensesDiv.innerHTML = html;
        } else {
            recentExpensesDiv.innerHTML = '<p>No expenses yet. <a href="/expenses.html">Add your first expense</a>!</p>';
        }
        
        // Load charts
        await loadCharts();
        
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showMessage('Failed to load dashboard data', 'error');
    }
}

async function loadCharts() {
    try {
        // Category chart
        const categoryData = await API.getCategoryChart();
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        
        if (categoryChart) {
            categoryChart.destroy();
        }
        
        categoryChart = new Chart(categoryCtx, {
            type: 'pie',
            data: {
                labels: categoryData.labels,
                datasets: [{
                    data: categoryData.data,
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
                        '#4BC0C0', '#FF6384'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + formatCurrency(context.parsed);
                            }
                        }
                    }
                }
            }
        });
        
        // Monthly chart
        const monthlyData = await API.getMonthlyChart();
        const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
        
        if (monthlyChart) {
            monthlyChart.destroy();
        }
        
        monthlyChart = new Chart(monthlyCtx, {
            type: 'line',
            data: {
                labels: monthlyData.labels,
                datasets: [{
                    label: 'Monthly Spending',
                    data: monthlyData.data,
                    borderColor: '#36A2EB',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Monthly Spending: ' + formatCurrency(context.parsed.y);
                            }
                        }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Failed to load charts:', error);
    }
}

