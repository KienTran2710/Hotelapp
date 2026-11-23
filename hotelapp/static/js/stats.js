function renderHotelCharts(revLabels, revData, occLabels, occData, maxDays) {
    const revCtx = document.getElementById('revenueChart');
    if (revCtx) {
        new Chart(revCtx, {
            type: 'doughnut',
            data: {
                labels: revLabels,
                datasets: [{
                    data: revData,
                    backgroundColor: ['#0d6efd', '#ffc107', '#198754', '#6f42c1', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Bieu do ty le doanh thu theo loai phong'
                    }
                }
            }
        });
    }

    const occCtx = document.getElementById('occupancyChart');
    if (occCtx) {
        new Chart(occCtx, {
            type: 'bar',
            data: {
                labels: occLabels,
                datasets: [{
                    label: 'So ngay thue trong thang',
                    data: occData,
                    backgroundColor: '#0d6efd'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: maxDays
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Bieu do mat do su dung phong trong thang'
                    }
                }
            }
        });
    }
}
