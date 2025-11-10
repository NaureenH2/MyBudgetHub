// Expenses page functionality
let editingExpenseId = null;
let categories = [];

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const user = await checkAuthentication();
    if (!user) {
        redirectTo('/login.html');
        return;
    }

    // Set default date to today
    document.getElementById('date').valueAsDate = new Date();

    // Load expenses and categories
    await loadExpenses();
    await loadCategories();

    // Setup forms
    setupExpenseForm();
    setupBudgetForm();
    setupFilterForm();
});

async function loadExpenses() {
    try {
        const filters = getFilters();
        const data = await API.getExpenses(filters);
        
        // Update categories if not loaded
        if (categories.length === 0) {
            categories = data.categories || [];
            updateCategoryFilter();
        }
        
        displayExpenses(data.expenses || []);
    } catch (error) {
        console.error('Failed to load expenses:', error);
        showMessage('Failed to load expenses', 'error');
    }
}

async function loadCategories() {
    try {
        const data = await API.getExpenses();
        categories = data.categories || [];
        updateCategoryFilter();
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

function updateCategoryFilter() {
    const filterCategory = document.getElementById('filterCategory');
    if (filterCategory) {
        // Keep "All Categories" option
        const currentValue = filterCategory.value;
        filterCategory.innerHTML = '<option value="">All Categories</option>';
        
        categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            filterCategory.appendChild(option);
        });
        
        if (currentValue) {
            filterCategory.value = currentValue;
        }
    }
}

function getFilters() {
    const search = document.getElementById('search').value;
    const category = document.getElementById('filterCategory').value;
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const sortBy = document.getElementById('sortBy').value;

    const filters = {};
    if (search) filters.search = search;
    if (category) filters.category = category;
    if (dateFrom) filters.date_from = dateFrom;
    if (dateTo) filters.date_to = dateTo;
    if (sortBy) filters.sort = sortBy;

    return filters;
}

function displayExpenses(expenses) {
    const expensesList = document.getElementById('expensesList');
    document.getElementById('expenseCount').textContent = expenses.length;

    if (expenses.length === 0) {
        expensesList.innerHTML = '<p>No expenses found. <a href="/expenses.html">Add your first expense</a>!</p>';
        return;
    }

    let html = `
        <table class="expense-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Category</th>
                    <th>Amount</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    expenses.forEach(expense => {
        html += `
            <tr>
                <td>${expense.date}</td>
                <td>${expense.description}</td>
                <td><span class="category-badge">${expense.category}</span></td>
                <td>${formatCurrency(expense.amount)}</td>
                <td>
                    <button class="btn btn-small btn-edit" onclick="editExpense(${expense.id})">Edit</button>
                    <button class="btn btn-small btn-delete" onclick="deleteExpense(${expense.id})">Delete</button>
                </td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    expensesList.innerHTML = html;
}

function setupExpenseForm() {
    const form = document.getElementById('expenseForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const expense = {
            description: document.getElementById('description').value,
            amount: parseFloat(document.getElementById('amount').value),
            category: document.getElementById('category').value,
            date: document.getElementById('date').value
        };

        try {
            if (editingExpenseId) {
                await API.updateExpense(editingExpenseId, expense);
                showMessage('Expense updated successfully!', 'success');
            } else {
                await API.createExpense(expense);
                showMessage('Expense added successfully!', 'success');
            }

            // Reset form
            form.reset();
            document.getElementById('date').valueAsDate = new Date();
            editingExpenseId = null;
            document.getElementById('formTitle').textContent = 'Add New Expense';
            document.getElementById('submitBtn').textContent = 'Add Expense';
            document.getElementById('cancelBtn').style.display = 'none';

            // Reload expenses
            await loadExpenses();
        } catch (error) {
            showMessage(error.message || 'Failed to save expense', 'error');
        }
    });
}

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
        } catch (error) {
            showMessage(error.message || 'Failed to set budget', 'error');
        }
    });
}

function setupFilterForm() {
    const form = document.getElementById('filterForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await loadExpenses();
    });
}

function clearFilters() {
    document.getElementById('search').value = '';
    document.getElementById('filterCategory').value = '';
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    document.getElementById('sortBy').value = 'date_desc';
    loadExpenses();
}

async function editExpense(id) {
    try {
        const response = await API.getExpense(id);
        const expense = response.expense;

        document.getElementById('expenseId').value = expense.id;
        document.getElementById('description').value = expense.description;
        document.getElementById('amount').value = expense.amount;
        document.getElementById('category').value = expense.category;
        document.getElementById('date').value = expense.date;

        editingExpenseId = expense.id;
        document.getElementById('formTitle').textContent = 'Edit Expense';
        document.getElementById('submitBtn').textContent = 'Update Expense';
        document.getElementById('cancelBtn').style.display = 'inline-block';

        // Scroll to form
        document.getElementById('expenseForm').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        showMessage(error.message || 'Failed to load expense', 'error');
    }
}

function cancelEdit() {
    editingExpenseId = null;
    document.getElementById('expenseForm').reset();
    document.getElementById('date').valueAsDate = new Date();
    document.getElementById('formTitle').textContent = 'Add New Expense';
    document.getElementById('submitBtn').textContent = 'Add Expense';
    document.getElementById('cancelBtn').style.display = 'none';
}

async function deleteExpense(id) {
    if (!confirm('Are you sure you want to delete this expense?')) {
        return;
    }

    try {
        await API.deleteExpense(id);
        showMessage('Expense deleted successfully!', 'success');
        await loadExpenses();
    } catch (error) {
        showMessage(error.message || 'Failed to delete expense', 'error');
    }
}

// Export for use in HTML
window.editExpense = editExpense;
window.deleteExpense = deleteExpense;
window.clearFilters = clearFilters;
window.cancelEdit = cancelEdit;

