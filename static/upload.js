// Upload page functionality
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const user = await checkAuthentication();
    if (!user) {
        redirectTo('/login.html');
        return;
    }

    // Setup upload form
    const uploadForm = document.getElementById('uploadForm');
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];

        if (!file) {
            showMessage('Please select a file', 'error');
            return;
        }

        if (!file.name.endsWith('.csv')) {
            showMessage('Please upload a CSV file', 'error');
            return;
        }

        try {
            showMessage('Uploading and processing file...', 'info');
            const response = await API.uploadCSV(file);
            
            if (response.error_count && response.error_count > 0) {
                showMessage(`Imported ${response.imported_count} expenses. ${response.error_count} errors encountered.`, 'warning');
            } else {
                showMessage(`Successfully imported ${response.imported_count} expenses!`, 'success');
            }

            // Reset form
            fileInput.value = '';
            
            // Redirect to expenses page after a delay
            setTimeout(() => {
                redirectTo('/expenses.html');
            }, 2000);
        } catch (error) {
            showMessage(error.message || 'Upload failed', 'error');
        }
    });
});

