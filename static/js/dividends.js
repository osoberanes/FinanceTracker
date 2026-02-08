// ============================================
// DIVIDENDS.JS - Tracking de Dividendos con Auto-Sync
// ============================================

let summaryData = null;
let expectedData = null;

// Inicialización
document.addEventListener('DOMContentLoaded', async function() {
    // Auto-sync al cargar la página (silent mode)
    await syncDividends(true);

    // Cargar datos
    await loadDividendsSummary();
    await loadExpectedYield();
    await loadDividendsHistory();
    await loadTickersForSelect();

    // Listener para tabs
    document.querySelectorAll('#dividendTabs button').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            if (e.target.id === 'by-month-tab') {
                renderMonthChart();
            } else if (e.target.id === 'by-ticker-tab') {
                renderTickerChart();
                renderTickerTable();
            }
        });
    });
});

// Sincronizar dividendos
async function syncDividends(silent = false) {
    const btn = document.getElementById('sync-btn');

    if (!silent && btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-arrow-repeat spin"></i> Sincronizando...';
    }

    try {
        const response = await fetch('/api/dividends/sync', { method: 'POST' });
        const result = await response.json();

        if (!silent) {
            if (result.synced > 0) {
                showAlert('success', `Se encontraron ${result.synced} dividendos nuevos`);
            } else {
                showAlert('info', 'No hay dividendos nuevos');
            }

            // Recargar datos
            await loadDividendsSummary();
            await loadDividendsHistory();
        }

    } catch (error) {
        if (!silent) {
            showAlert('danger', 'Error al sincronizar');
        }
        console.error('Error sync:', error);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Sincronizar';
        }
    }
}

// Cargar resumen
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
        document.getElementById('pending-count').textContent = summaryData.pending_count;

        // Mostrar alerta de pendientes
        const pendingAlert = document.getElementById('pending-alert');
        if (summaryData.pending_count > 0) {
            pendingAlert.classList.remove('d-none');
            document.getElementById('pending-message').textContent =
                `Tienes ${summaryData.pending_count} dividendo(s) pendiente(s) por confirmar (~$${summaryData.pending_amount.toLocaleString('es-MX')})`;
        } else {
            pendingAlert.classList.add('d-none');
        }

        // Renderizar gráficos si están visibles
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

// Cargar historial
async function loadDividendsHistory() {
    try {
        const response = await fetch('/api/dividends');
        const dividends = await response.json();

        const tbody = document.querySelector('#dividends-table tbody');
        tbody.innerHTML = '';

        const typeLabels = {
            'dividend': '<span class="badge bg-success">Dividendo</span>',
            'coupon': '<span class="badge bg-info">Cupón</span>',
            'staking': '<span class="badge bg-warning text-dark">Staking</span>'
        };

        const sourceLabels = {
            'yfinance': '<span class="badge bg-secondary">Auto</span>',
            'manual': '<span class="badge bg-primary">Manual</span>',
            'auto': '<span class="badge bg-secondary">Auto</span>'
        };

        dividends.forEach(div => {
            const row = document.createElement('tr');

            // Clase para pendientes
            if (!div.is_confirmed) {
                row.classList.add('table-warning');
            }

            const statusBadge = div.is_confirmed
                ? '<span class="badge bg-success">✓ Confirmado</span>'
                : '<span class="badge bg-warning text-dark">⚠️ Pendiente</span>';

            const grossAmount = div.gross_amount
                ? `$${parseFloat(div.gross_amount).toLocaleString('es-MX', {minimumFractionDigits: 2})}`
                : '-';

            row.innerHTML = `
                <td>${statusBadge}</td>
                <td>${formatDate(div.payment_date)}</td>
                <td><strong>${div.ticker}</strong></td>
                <td>${typeLabels[div.dividend_type] || div.dividend_type}</td>
                <td class="text-end">${grossAmount}</td>
                <td class="text-end text-success">$${parseFloat(div.net_amount).toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
                <td>${sourceLabels[div.source] || div.source}</td>
                <td>
                    ${!div.is_confirmed ? `
                        <button class="btn btn-sm btn-warning me-1" onclick="openConfirmModal(${div.id})" title="Confirmar">
                            <i class="bi bi-check-lg"></i>
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editDividend(${div.id})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteDividend(${div.id})" title="Eliminar">
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

// Cargar tickers para select
async function loadTickersForSelect() {
    try {
        const response = await fetch('/api/transactions');
        const transactions = await response.json();

        const tickers = [...new Set(transactions.map(t => t.ticker))].sort();

        const select = document.getElementById('dividend-ticker');
        select.innerHTML = '<option value="">Seleccionar...</option>';

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

// Abrir modal de confirmación
function openConfirmModal(id) {
    fetch('/api/dividends')
        .then(res => res.json())
        .then(dividends => {
            const div = dividends.find(d => d.id === id);
            if (!div) return;

            document.getElementById('confirm-dividend-id').value = div.id;
            document.getElementById('confirm-ticker').value = div.ticker;
            document.getElementById('confirm-date').value = formatDate(div.payment_date);
            document.getElementById('confirm-gross').value = div.gross_amount
                ? `$${parseFloat(div.gross_amount).toFixed(2)}`
                : 'N/A';
            document.getElementById('confirm-net').value = div.net_amount;

            new bootstrap.Modal(document.getElementById('confirmDividendModal')).show();
        });
}

// Confirmar dividendo
async function confirmDividend() {
    const id = document.getElementById('confirm-dividend-id').value;
    const netAmount = parseFloat(document.getElementById('confirm-net').value);

    try {
        const response = await fetch(`/api/dividends/${id}/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ net_amount: netAmount })
        });

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('confirmDividendModal')).hide();
            showAlert('success', 'Dividendo confirmado');
            await loadDividendsSummary();
            await loadDividendsHistory();
        } else {
            const result = await response.json();
            showAlert('danger', result.error || 'Error al confirmar');
        }
    } catch (error) {
        showAlert('danger', 'Error de conexión');
    }
}

// Scroll a pendientes
function scrollToPending() {
    document.querySelector('#history-tab').click();
    setTimeout(() => {
        const pendingRow = document.querySelector('#dividends-table .table-warning');
        if (pendingRow) {
            pendingRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 300);
}

// Renderizar gráfico por mes
function renderMonthChart() {
    if (!summaryData || !summaryData.by_month) return;

    const months = Object.keys(summaryData.by_month);
    const values = Object.values(summaryData.by_month);

    if (months.length === 0) {
        document.getElementById('chart-by-month').innerHTML =
            '<p class="text-muted text-center mt-5">No hay dividendos confirmados para mostrar</p>';
        return;
    }

    const trace = {
        x: months,
        y: values,
        type: 'bar',
        marker: { color: '#28a745' },
        hovertemplate: '%{x}<br>$%{y:,.2f} MXN<extra></extra>'
    };

    const layout = {
        title: 'Dividendos Confirmados por Mes',
        xaxis: { title: 'Mes' },
        yaxis: { title: 'Monto Neto (MXN)', tickformat: '$,.0f' },
        margin: { t: 50, b: 50, l: 60, r: 20 }
    };

    Plotly.newPlot('chart-by-month', [trace], layout, { responsive: true });
}

// Renderizar gráfico por ticker
function renderTickerChart() {
    if (!summaryData || !summaryData.by_ticker) return;

    const tickers = Object.keys(summaryData.by_ticker);
    const values = Object.values(summaryData.by_ticker);

    if (tickers.length === 0) {
        document.getElementById('chart-by-ticker').innerHTML =
            '<p class="text-muted text-center mt-5">No hay dividendos confirmados</p>';
        return;
    }

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

    if (Object.keys(summaryData.by_ticker).length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-muted text-center">Sin datos</td></tr>';
        return;
    }

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

// Guardar dividendo manual
async function saveDividend() {
    const form = document.getElementById('dividend-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    if (data.gross_amount) data.gross_amount = parseFloat(data.gross_amount);
    data.net_amount = parseFloat(data.net_amount);
    data.is_confirmed = true;  // Manuales ya están confirmados

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
            showAlert('success', 'Dividendo registrado');
            await loadDividendsSummary();
            await loadDividendsHistory();
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
        const response = await fetch('/api/dividends');
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
        showAlert('danger', 'Error al cargar');
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
        notes: document.getElementById('edit-dividend-notes').value,
        is_confirmed: true  // Al editar, se confirma automáticamente
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
            await loadDividendsSummary();
            await loadDividendsHistory();
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
            await loadDividendsSummary();
            await loadDividendsHistory();
        } else {
            showAlert('danger', 'Error al eliminar');
        }
    } catch (error) {
        showAlert('danger', 'Error de conexión');
    }
}

// Utilidades
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr + 'T00:00:00');
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

// CSS para spinner
const style = document.createElement('style');
style.textContent = `
    .spin {
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
