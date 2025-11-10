// Budgets page functionality
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const user = await checkAuthentication();
    if (!user) {
        redirectTo('/login.html');
        return;
    }

    // Setup budget form
    setupBudgetForm();

    // Load budgets
    await loadBudgets();
});

function setupBudgetForm() {
    const form = document.getElementById('budgetForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const budget = {
            category: document.getElementById('budgetCategory').value,
            amount: parseFloat(document.getElementById('budgetAmount').value)
        };

        try {
            await API.createBudget(budget);
            showMessage('Budget set successfully!', 'success');
            form.reset();
            await loadBudgets();
        } catch (error) {
            showMessage(error.message || 'Failed to set budget', 'error');
        }
    });
}

async function loadBudgets() {
    try {
        const response = await API.getBudgets();
        const budgets = response.budgets || [];

        if (budgets.length === 0) {
            document.getElementById('budgetStatus').style.display = 'none';
            return;
        }

        document.getElementById('budgetStatus').style.display = 'block';
        const budgetsList = document.getElementById('budgetsList');
        budgetsList.innerHTML = '';

        budgets.forEach(budgetItem => {
            const budget = budgetItem.budget;
            const progressWidth = Math.min(budgetItem.percentage, 100);

            const budgetDiv = document.createElement('div');
            budgetDiv.className = `budget-item ${budgetItem.is_over ? 'over-budget' : budgetItem.is_warning ? 'warning' : ''}`;
            
            budgetDiv.innerHTML = `
                <div class="budget-header">
                    <h3>${budget.category}</h3>
                    <span class="budget-amount">${formatCurrency(budget.amount)}</span>
                </div>
                <div class="budget-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progressWidth}%"></div>
                    </div>
                    <div class="budget-details">
                        <span>Spent: ${formatCurrency(budgetItem.spent)}</span>
                        <span>Remaining: ${formatCurrency(budgetItem.remaining)}</span>
                        <span>${budgetItem.percentage.toFixed(1)}%</span>
                    </div>
                </div>
            `;

            budgetsList.appendChild(budgetDiv);
        });

    } catch (error) {
        console.error('Failed to load budgets:', error);
        showMessage('Failed to load budgets', 'error');
    }
}

