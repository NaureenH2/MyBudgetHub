// Register page functionality
document.addEventListener('DOMContentLoaded', async () => {
    // Check if already authenticated
    const user = await checkAuthentication();
    if (user) {
        redirectTo('/dashboard.html');
        return;
    }

    // Setup register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(registerForm);
            const username = formData.get('username');
            const email = formData.get('email');
            const password = formData.get('password');
            const confirmPassword = formData.get('confirm_password');

            // Client-side validation
            if (password !== confirmPassword) {
                showMessage('Passwords do not match', 'error');
                return;
            }

            try {
                const response = await API.register(username, email, password, confirmPassword);
                showMessage('Registration successful! Redirecting...', 'success');
                setTimeout(() => {
                    redirectTo('/dashboard.html');
                }, 1000);
            } catch (error) {
                showMessage(error.message || 'Registration failed', 'error');
            }
        });
    }
});

