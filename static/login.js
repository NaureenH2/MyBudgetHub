// Login page functionality
document.addEventListener('DOMContentLoaded', async () => {
    // Check if already authenticated
    const user = await checkAuthentication();
    if (user) {
        redirectTo('/dashboard.html');
        return;
    }

    // Setup login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(loginForm);
            const username = formData.get('username');
            const password = formData.get('password');

            try {
                const response = await API.login(username, password);
                showMessage('Login successful!', 'success');
                setTimeout(() => {
                    redirectTo('/dashboard.html');
                }, 500);
            } catch (error) {
                showMessage(error.message || 'Login failed', 'error');
            }
        });
    }
});

