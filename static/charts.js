// Chart.js initialization and configuration
// This file handles all chart rendering for the dashboard

/**
 * Initialize the category pie chart
 * @param {string} apiUrl - URL to fetch category chart data
 */
function initCategoryChart(apiUrl) {
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('categoryChart');
            if (!ctx) {
                console.error('Category chart canvas not found');
                return;
            }

            new Chart(ctx.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.data,
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
                            '#4BC0C0', '#FF6384'
                        ],
                        hoverBackgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
                            '#4BC0C0', '#FF6384'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                padding: 15,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    const value = context.parsed || 0;
                                    label += '$' + value.toLocaleString('en-US', {
                                        minimumFractionDigits: 2,
                                        maximumFractionDigits: 2
                                    });
                                    return label;
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading category chart:', error);
        });
}

/**
 * Initialize the monthly trend line chart
 * @param {string} apiUrl - URL to fetch monthly chart data
 */
function initMonthlyChart(apiUrl) {
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('monthlyChart');
            if (!ctx) {
                console.error('Monthly chart canvas not found');
                return;
            }

            new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Monthly Spending',
                        data: data.data,
                        borderColor: '#36A2EB',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#36A2EB',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    const value = context.parsed.y || 0;
                                    label += '$' + value.toLocaleString('en-US', {
                                        minimumFractionDigits: 2,
                                        maximumFractionDigits: 2
                                    });
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString('en-US');
                                },
                                font: {
                                    size: 11
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                font: {
                                    size: 11
                                }
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading monthly chart:', error);
        });
}

/**
 * Initialize the category monthly comparison bar chart
 * @param {string} apiUrl - URL to fetch category monthly comparison data
 */
function initCategoryMonthlyChart(apiUrl) {
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('categoryMonthlyChart');
            if (!ctx) {
                console.error('Category monthly chart canvas not found');
                return;
            }

            new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: 'Current Month',
                            data: data.current,
                            backgroundColor: '#36A2EB',
                            borderColor: '#36A2EB',
                            borderWidth: 1
                        },
                        {
                            label: 'Previous Month',
                            data: data.previous,
                            backgroundColor: '#C9CBCF',
                            borderColor: '#C9CBCF',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    const value = context.parsed.y || 0;
                                    label += '$' + value.toLocaleString('en-US', {
                                        minimumFractionDigits: 2,
                                        maximumFractionDigits: 2
                                    });
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString('en-US');
                                },
                                font: {
                                    size: 11
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                font: {
                                    size: 11
                                }
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading category monthly chart:', error);
        });
}

/**
 * Initialize all charts on the dashboard
 * This function should be called when the DOM is ready
 */
function initDashboardCharts() {
    // Get API URLs from data attributes on canvas elements
    const categoryChart = document.getElementById('categoryChart');
    const monthlyChart = document.getElementById('monthlyChart');
    const categoryMonthlyChart = document.getElementById('categoryMonthlyChart');

    if (categoryChart) {
        const categoryApiUrl = categoryChart.getAttribute('data-api-url');
        if (categoryApiUrl) {
            initCategoryChart(categoryApiUrl);
        }
    }

    if (monthlyChart) {
        const monthlyApiUrl = monthlyChart.getAttribute('data-api-url');
        if (monthlyApiUrl) {
            initMonthlyChart(monthlyApiUrl);
        }
    }

    if (categoryMonthlyChart) {
        const categoryMonthlyApiUrl = categoryMonthlyChart.getAttribute('data-api-url');
        if (categoryMonthlyApiUrl) {
            initCategoryMonthlyChart(categoryMonthlyApiUrl);
        }
    }
}

// Initialize charts when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboardCharts);
} else {
    // DOM is already loaded
    initDashboardCharts();
}

