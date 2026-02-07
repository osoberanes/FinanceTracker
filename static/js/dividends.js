// ============================================
// DIVIDENDS.JS - Tracking de Dividendos
// ============================================

let summaryData = null;
let expectedData = null;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    loadDividendsSummary();
    loadExpectedYield();
    loadDividendsHistory();
    loadTickersForSelect();

    // Listener para cambio de tabs
    document.querySelectorAll('#dividendTabs button').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            if (e.target.id === 'by-month-tab') {
                renderMonthChart();
            } else if (e.target.id === 'by-ticker-tab') {
                renderTickerChart();
            }
        });
    });
});

// Cargar resumen de dividendos
async function loadDividendsSummary() {
    try {
        const year = new Date().getFullYear();
        const response = await fetch(`/api/dividends/summary?year=${year}`);
        summaryData = await response.json();

        // Actualizar cards
        document.getElementById('total-dividends').textContent =
            `$${summaryData.total_dividends.toLocaleString('es-MX', {minimumFractionDigits: 2})}`;
        document.getElementById('dividend-yield').textContent =
            `${summaryData.dividend_yield_percent.toFixed(2)}%`;
        document.getElementById('dividend-count').textContent = summaryData.count;

        // Renderizar gráficos
        renderMonthChart();
        renderTickerTable();

    } catch (error) {
        console.error('Error cargando resumen:', error);
    }
}

// Cargar yield esperado
async function loadExpectedYield() {
    try {
        const response = await fetch('/api/dividends/expected-yield');
        expectedData = await response.json();

        document.getElementById('expected-yield').textContent =
            `${expectedData.portfolio_yield_percent.toFixed(2)}%`;

    } catch (error) {
        console.error('Error cargando yield esperado:', error);
    }
}

// Cargar historial de dividendos
async function loadDividendsHistory() {
    try {
        const response = await fetch('/api/dividends');
        const dividends = await response.json();

        const tbody = document.querySelector('#dividends-table tbody');
        tbody.innerHTML = '';

        const typeLabels = {
            'dividend': '<span class="badge bg-success">Dividendo</span>',
            'coupon': '<span class="badge bg-info">Cupón</span>',
            'staking': '<span class="badge bg-warning">Staking</span>'
        };

        dividends.forEach(div => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${formatDate(div.payment_date)}</td>
                <td><strong>${div.ticker}</strong></td>
                <td>${typeLabels[div.dividend_type] || div.dividend_type}</td>
                <td class="text-end text-success">$${parseFloat(div.net_amount).toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
                <td>${div.notes || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editDividend(${div.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteDividend(${div.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });

    } catch (error) {
        console.error('Error cargando historial:', error);
    }
}

// Cargar tickers para el select del formulario
async function loadTickersForSelect() {
    try {
        const response = await fetch('/api/transactions');
        const transactions = await response.json();

        // Obtener tickers únicos
        const tickers = [...new Set(transactions.map(t => t.ticker))].sort();

        const select = document.getElementById('dividend-ticker');
        tickers.forEach(ticker => {
            const option = document.createElement('option');
            option.value = ticker;
            option.textContent = ticker;
            select.appendChild(option);
        });

    } catch (error) {
        console.error('Error cargando tickers:', error);
    }
}

// Renderizar gráfico por mes
function renderMonthChart() {
    if (!summaryData || !summaryData.by_month) return;

    const months = Object.keys(summaryData.by_month);
    const values = Object.values(summaryData.by_month);

    const trace = {
        x: months,
        y: values,
        type: 'bar',
        marker: { color: '#28a745' },
        hovertemplate: '%{x}<br>$%{y:,.2f} MXN<extra></extra>'
    };

    const layout = {
        title: 'Dividendos Recibidos por Mes',
        xaxis: { title: 'Mes' },
        yaxis: { title: 'Monto (MXN)', tickformat: '$,.0f' },
        margin: { t: 50, b: 50, l: 60, r: 20 }
    };

    Plotly.newPlot('chart-by-month', [trace], layout, { responsive: true });
}

// Renderizar gráfico por ticker
function renderTickerChart() {
    if (!summaryData || !summaryData.by_ticker) return;

    const tickers = Object.keys(summaryData.by_ticker);
    const values = Object.values(summaryData.by_ticker);

    const trace = {
        labels: tickers,
        values: values,
        type: 'pie',
        hovertemplate: '%{label}<br>$%{value:,.2f} MXN<br>%{percent}<extra></extra>'
    };

    const layout = {
        margin: { t: 20, b: 20, l: 20, r: 20 }
    };

    Plotly.newPlot('chart-by-ticker', [trace], layout, { responsive: true });
}

// Renderizar tabla por ticker
function renderTickerTable() {
    if (!summaryData || !summaryData.by_ticker) return;

    const tbody = document.querySelector('#table-by-ticker tbody');
    tbody.innerHTML = '';

    const total = summaryData.total_dividends;

    Object.entries(summaryData.by_ticker).forEach(([ticker, amount]) => {
        const pct = total > 0 ? (amount / total * 100) : 0;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${ticker}</strong></td>
            <td class="text-end">$${amount.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
            <td class="text-end">${pct.toFixed(1)}%</td>
        `;
        tbody.appendChild(row);
    });
}

// Guardar nuevo dividendo
async function saveDividend() {
    const form = document.getElementById('dividend-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Convertir valores numéricos
    if (data.gross_amount) data.gross_amount = parseFloat(data.gross_amount);
    data.net_amount = parseFloat(data.net_amount);

    try {
        const response = await fetch('/api/dividends', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addDividendModal')).hide();
            form.reset();
            showAlert('success', 'Dividendo registrado exitosamente');
            loadDividendsSummary();
            loadDividendsHistory();
        } else {
            showAlert('danger', result.error || 'Error al registrar');
        }
    } catch (error) {
        showAlert('danger', 'Error de conexión');
    }
}

// Editar dividendo
async function editDividend(id) {
    try {
        const response = await fetch(`/api/dividends`);
        const dividends = await response.json();
        const dividend = dividends.find(d => d.id === id);

        if (!dividend) return;

        document.getElementById('edit-dividend-id').value = dividend.id;
        document.getElementById('edit-dividend-ticker').value = dividend.ticker;
        document.getElementById('edit-dividend-type').value = dividend.dividend_type;
        document.getElementById('edit-dividend-date').value = dividend.payment_date;
        document.getElementById('edit-dividend-gross').value = dividend.gross_amount || '';
        document.getElementById('edit-dividend-net').value = dividend.net_amount;
        document.getElementById('edit-dividend-notes').value = dividend.notes || '';

        new bootstrap.Modal(document.getElementById('editDividendModal')).show();

    } catch (error) {
        showAlert('danger', 'Error al cargar dividendo');
    }
}

// Actualizar dividendo
async function updateDividend() {
    const id = document.getElementById('edit-dividend-id').value;

    const data = {
        dividend_type: document.getElementById('edit-dividend-type').value,
        payment_date: document.getElementById('edit-dividend-date').value,
        gross_amount: parseFloat(document.getElementById('edit-dividend-gross').value) || null,
        net_amount: parseFloat(document.getElementById('edit-dividend-net').value),
        notes: document.getElementById('edit-dividend-notes').value
    };

    try {
        const response = await fetch(`/api/dividends/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('editDividendModal')).hide();
            showAlert('success', 'Dividendo actualizado');
            loadDividendsSummary();
            loadDividendsHistory();
        } else {
            const result = await response.json();
            showAlert('danger', result.error || 'Error al actualizar');
        }
    } catch (error) {
        showAlert('danger', 'Error de conexión');
    }
}

// Eliminar dividendo
async function deleteDividend(id) {
    if (!confirm('¿Eliminar este dividendo?')) return;

    try {
        const response = await fetch(`/api/dividends/${id}`, { method: 'DELETE' });

        if (response.ok) {
            showAlert('success', 'Dividendo eliminado');
            loadDividendsSummary();
            loadDividendsHistory();
        } else {
            showAlert('danger', 'Error al eliminar');
        }
    } catch (error) {
        showAlert('danger', 'Error de conexión');
    }
}

// Utilidades
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-MX');
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = 9999;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
}
