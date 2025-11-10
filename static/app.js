// Main application JavaScript
// This file handles common app functionality

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication on all pages
    await checkAuthentication();
    
    // Add any global event listeners or initialization code here
    console.log('MyBudgetHub app initialized');
});

