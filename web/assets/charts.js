/* Dashboard Charts - Chart.js Integration */

// Chart instances storage (for updating)
let chartInstances = {};

// Initialize all charts on dashboard
async function initializeCharts() {
  // Check if api function is available
  if (typeof api === 'undefined') {
    console.warn('API function not available yet, retrying...');
    setTimeout(initializeCharts, 500);
    return;
  }

  try {
    // Get date range from selector
    const dateRange = document.getElementById('analyticsDateRange');
    const days = dateRange ? parseInt(dateRange.value) || 30 : 30;

    // Fetch all analytics data
    const [deviceStats, alertTrends, healthMetrics] = await Promise.all([
      api('/api/analytics/devices/stats'),
      api(`/api/analytics/alerts/trends?days=${days}`),
      api('/api/analytics/health/metrics')
    ]);

    // Destroy existing charts before creating new ones
    Object.values(chartInstances).forEach(chart => {
      if (chart && typeof chart.destroy === 'function') {
        chart.destroy();
      }
    });
    chartInstances = {};

    // Render all charts
    renderDeviceStatusChart(deviceStats);
    renderDeviceTypeChart(deviceStats);
    renderAlertTrendsChart(alertTrends, days);
    renderAlertSeverityChart(alertTrends);
    renderHealthMetrics(healthMetrics);
    renderTopAlertingDevices(healthMetrics);
  } catch (error) {
    console.error('Failed to load charts:', error);
    // Don't block page load if charts fail
  }
}

// Update charts when date range changes
async function updateChartsDateRange() {
  await initializeCharts();
}

// Device Status Pie Chart
function renderDeviceStatusChart(data) {
  const ctx = document.getElementById('deviceStatusChart');
  if (!ctx) return;

  const statusData = data.status_breakdown;
  
  chartInstances.deviceStatus = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Online', 'Offline', 'Error'],
      datasets: [{
        data: [
          statusData.online || 0,
          statusData.offline || 0,
          statusData.error || 0
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',   // Green - online
          'rgba(148, 163, 184, 0.8)', // Gray - offline
          'rgba(239, 68, 68, 0.8)'    // Red - error
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(148, 163, 184, 1)',
          'rgba(239, 68, 68, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#0f172a',
            padding: 15,
            font: { size: 12 }
          }
        },
        title: {
          display: true,
          text: 'Device Status Distribution',
          color: '#0f172a',
          font: { size: 16, weight: 'bold' },
          padding: { bottom: 20 }
        }
      }
    }
  });
}

// Device Type Pie Chart
function renderDeviceTypeChart(data) {
  const ctx = document.getElementById('deviceTypeChart');
  if (!ctx) return;

  const typeData = data.type_breakdown;
  const labels = Object.keys(typeData);
  const values = Object.values(typeData);
  
  // Generate colors
  const colors = [
    'rgba(59, 130, 246, 0.8)',  // Blue
    'rgba(168, 85, 247, 0.8)',  // Purple
    'rgba(236, 72, 153, 0.8)',  // Pink
    'rgba(251, 146, 60, 0.8)',  // Orange
    'rgba(14, 165, 233, 0.8)',  // Cyan
    'rgba(139, 92, 246, 0.8)'   // Violet
  ];

  chartInstances.deviceType = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: colors.slice(0, labels.length).map(c => c.replace('0.8', '1')),
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#0f172a',
            padding: 15,
            font: { size: 12 }
          }
        },
        title: {
          display: true,
          text: 'Devices by Type',
          color: '#0f172a',
          font: { size: 16, weight: 'bold' },
          padding: { bottom: 20 }
        }
      }
    }
  });
}

// Alert Trends Line Chart
function renderAlertTrendsChart(data, days = 30) {
  const ctx = document.getElementById('alertTrendsChart');
  if (!ctx) return;

  const timeline = data.timeline || [];
  const labels = timeline.map(t => {
    const date = new Date(t.date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  const counts = timeline.map(t => t.count);

  chartInstances.alertTrends = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Alerts',
        data: counts,
        borderColor: 'rgba(59, 130, 246, 1)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgba(59, 130, 246, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: `Alert Trends (Last ${days} Days)`,
          color: '#0f172a',
          font: { size: 16, weight: 'bold' },
          padding: { bottom: 20 }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          titleColor: '#e2e8f0',
          bodyColor: '#e2e8f0',
          borderColor: 'rgba(59, 130, 246, 0.5)',
          borderWidth: 1,
          padding: 12,
          displayColors: false
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(148, 163, 184, 0.1)',
            drawBorder: false
          },
          ticks: {
            color: '#475569',
            maxRotation: 45,
            minRotation: 45
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(148, 163, 184, 0.1)',
            drawBorder: false
          },
          ticks: {
            color: '#475569',
            precision: 0
          }
        }
      }
    }
  });
}

// Alert Severity Bar Chart
function renderAlertSeverityChart(data) {
  const ctx = document.getElementById('alertSeverityChart');
  if (!ctx) return;

  const severityData = data.severity_breakdown;

  chartInstances.alertSeverity = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Low', 'Medium', 'High', 'Critical'],
      datasets: [{
        label: 'Alerts',
        data: [
          severityData.low || 0,
          severityData.medium || 0,
          severityData.high || 0,
          severityData.critical || 0
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',   // Green - low
          'rgba(245, 158, 11, 0.8)',  // Yellow - medium
          'rgba(249, 115, 22, 0.8)',  // Orange - high
          'rgba(239, 68, 68, 0.8)'    // Red - critical
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(249, 115, 22, 1)',
          'rgba(239, 68, 68, 1)'
        ],
        borderWidth: 2,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: 'Alerts by Severity',
          color: '#0f172a',
          font: { size: 16, weight: 'bold' },
          padding: { bottom: 20 }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          titleColor: '#e2e8f0',
          bodyColor: '#e2e8f0',
          borderColor: 'rgba(59, 130, 246, 0.5)',
          borderWidth: 1,
          padding: 12
        }
      },
      scales: {
        x: {
          grid: {
            display: false,
            drawBorder: false
          },
          ticks: {
            color: '#475569'
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(148, 163, 184, 0.1)',
            drawBorder: false
          },
          ticks: {
            color: '#475569',
            precision: 0
          }
        }
      }
    }
  });
}

// Health Metrics Cards
function renderHealthMetrics(data) {
  // System Health Score
  const healthScore = document.getElementById('healthScore');
  if (healthScore) {
    const score = data.health_score || 0;
    let color = '#22c55e'; // Green
    if (score < 70) color = '#f59e0b'; // Yellow
    if (score < 50) color = '#ef4444'; // Red
    
    healthScore.innerHTML = `
      <div style="font-size: 48px; font-weight: bold; color: ${color}; margin-bottom: 8px;">
        ${score.toFixed(0)}%
      </div>
      <div style="font-size: 14px; color: var(--muted);">System Health Score</div>
    `;
  }

  // Uptime Percentage
  const uptimeCard = document.getElementById('uptimePercentage');
  if (uptimeCard) {
    const uptime = data.uptime_percentage || 0;
    uptimeCard.innerHTML = `
      <div style="font-size: 36px; font-weight: bold; color: var(--ok); margin-bottom: 8px;">
        ${uptime.toFixed(1)}%
      </div>
      <div style="font-size: 14px; color: var(--muted);">Device Uptime</div>
      <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">
        ${data.online_devices}/${data.total_devices} devices online
      </div>
    `;
  }

  // Recent Alerts
  const recentAlerts = document.getElementById('recentAlerts');
  if (recentAlerts) {
    const alerts = data.alerts_last_24h || 0;
    let alertColor = '#22c55e';
    if (alerts > 10) alertColor = '#f59e0b';
    if (alerts > 20) alertColor = '#ef4444';
    
    recentAlerts.innerHTML = `
      <div style="font-size: 36px; font-weight: bold; color: ${alertColor}; margin-bottom: 8px;">
        ${alerts}
      </div>
      <div style="font-size: 14px; color: var(--muted);">Alerts (24h)</div>
    `;
  }
}

// Top Alerting Devices List
function renderTopAlertingDevices(data) {
  const container = document.getElementById('topAlertingDevices');
  if (!container) return;

  const devices = data.top_alerting_devices || [];
  
  if (devices.length === 0) {
    container.innerHTML = '<div class="hint">No alerts in the last 30 days</div>';
    return;
  }

  container.innerHTML = `
    <table style="width: 100%;">
      <thead>
        <tr>
          <th style="text-align: left;">Device</th>
          <th style="text-align: left;">Type</th>
          <th style="text-align: right;">Alerts</th>
        </tr>
      </thead>
      <tbody>
        ${devices.map(d => `
          <tr>
            <td>${esc(d.device_name)}</td>
            <td>${esc(d.device_type)}</td>
            <td style="text-align: right;">
              <span class="badge b-warn">${d.alert_count}</span>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// Refresh charts (called by refresh button)
async function refreshCharts() {
  await initializeCharts();
}

// Handle window resize for charts with debouncing
let resizeTimeout;
window.addEventListener('resize', () => {
  // Debounce resize to avoid excessive calls
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    // Resize all chart instances when window is resized
    Object.values(chartInstances).forEach(chart => {
      if (chart && typeof chart.resize === 'function') {
        chart.resize();
      }
    });
  }, 150);
});

// Initialize charts when dashboard loads (after app.js has loaded)
window.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('dashboardRoot')) {
    // Wait for app.js to load and page to render
    setTimeout(() => {
      if (typeof api !== 'undefined') {
        // Only initialize if analytics tab is active or if we're on the analytics tab
        const analyticsTab = document.getElementById('tab-analytics');
        if (analyticsTab && analyticsTab.classList.contains('active')) {
          initializeCharts();
        }
      } else {
        // Retry if api function not ready
        setTimeout(() => {
          const analyticsTab = document.getElementById('tab-analytics');
          if (analyticsTab && analyticsTab.classList.contains('active')) {
            initializeCharts();
          }
        }, 1000);
      }
    }, 1000);
  }
});
