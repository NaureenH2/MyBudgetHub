// API client for making requests to the backend
const API_BASE_URL = '/api';

class API {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {},
            credentials: 'include', // Include cookies for session
            ...options
        };

        // Only set Content-Type for JSON requests (not FormData)
        if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
            config.headers['Content-Type'] = 'application/json';
            config.body = JSON.stringify(options.body);
        } else if (options.body) {
            config.body = options.body;
        }

        try {
            const response = await fetch(url, config);
            
            // Handle non-JSON responses (like CSV export)
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Request failed');
                }

                return data;
            } else {
                // Return response object for non-JSON (like file downloads)
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || 'Request failed');
                }
                return response;
            }
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Auth endpoints
    static async register(username, email, password, confirmPassword) {
        return this.request('/auth/register', {
            method: 'POST',
            body: { username, email, password, confirm_password: confirmPassword }
        });
    }

    static async login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: { username, password }
        });
    }

    static async logout() {
        return this.request('/auth/logout', {
            method: 'POST'
        });
    }

    static async checkAuth() {
        return this.request('/auth/check');
    }

    // Dashboard
    static async getDashboard() {
        return this.request('/dashboard');
    }

    // Expenses
    static async getExpenses(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/expenses?${params.toString()}`);
    }

    static async getExpense(id) {
        return this.request(`/expenses/${id}`);
    }

    static async createExpense(expense) {
        return this.request('/expenses', {
            method: 'POST',
            body: expense
        });
    }

    static async updateExpense(id, expense) {
        return this.request(`/expenses/${id}`, {
            method: 'PUT',
            body: expense
        });
    }

    static async deleteExpense(id) {
        return this.request(`/expenses/${id}`, {
            method: 'DELETE'
        });
    }

    // Budgets
    static async getBudgets() {
        return this.request('/budgets');
    }

    static async createBudget(budget) {
        return this.request('/budgets', {
            method: 'POST',
            body: budget
        });
    }

    // Charts
    static async getCategoryChart() {
        return this.request('/charts/category');
    }

    static async getMonthlyChart() {
        return this.request('/charts/monthly');
    }

    // Export
    static async exportExpenses() {
        try {
            const response = await fetch(`${API_BASE_URL}/export`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || 'Export failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `expenses_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Export failed:', error);
            throw error;
        }
    }

    // Upload
    static async uploadCSV(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Upload failed');
        }

        return data;
    }
}

// Utility functions
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '$0.00';
    return `$${parseFloat(amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `flash-message flash-${type}`;
    messageDiv.textContent = message;
    
    const container = document.querySelector('.main-content');
    if (container) {
        container.insertBefore(messageDiv, container.firstChild);
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}

function redirectTo(path) {
    window.location.href = path;
}

// Check authentication on page load
async function checkAuthentication() {
    try {
        const response = await API.checkAuth();
        if (response.authenticated) {
            // Update navigation
            const navLinks = document.getElementById('navLinks');
            if (navLinks) {
                navLinks.innerHTML = `
                    <a href="/dashboard.html">Dashboard</a>
                    <a href="/expenses.html">Expenses</a>
                    <a href="/budgets.html">Budgets</a>
                    <a href="/upload.html">Upload CSV</a>
                    <a href="#" onclick="handleLogout()">Logout (${response.user.username})</a>
                `;
            }
            return response.user;
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
    return null;
}

async function handleLogout() {
    try {
        await API.logout();
        redirectTo('/login.html');
    } catch (error) {
        console.error('Logout failed:', error);
        redirectTo('/login.html');
    }
}

// Export for use in other scripts
window.API = API;
window.formatCurrency = formatCurrency;
window.showMessage = showMessage;
window.redirectTo = redirectTo;
window.checkAuthentication = checkAuthentication;
window.handleLogout = handleLogout;

