// Main JavaScript for Portfolio Tracker

// Utility function to format currency in MXN
function formatCurrency(value) {
    if (value === null || value === undefined) {
        return 'N/A';
    }
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

// Utility function to format percentage
function formatPercentage(value) {
    if (value === null || value === undefined) {
        return 'N/A';
    }
    return value.toFixed(2) + '%';
}

// Utility function to format date to DD/MM/AAAA
function formatDate(dateString) {
    // Handle YYYY-MM-DD format
    const parts = dateString.split('-');
    if (parts.length === 3) {
        const year = parts[0];
        const month = parts[1];
        const day = parts[2];
        return `${day}/${month}/${year}`;
    }

    // Fallback to Date parsing
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
}

// Utility function to get gain/loss class
function getGainLossClass(value) {
    if (value === null || value === undefined) {
        return 'neutral';
    }
    return value >= 0 ? 'gain' : 'loss';
}

// Show message (success or error)
function showMessage(message, type = 'success') {
    const messageDiv = document.getElementById('formMessage');
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';

    messageDiv.innerHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="bi bi-${icon}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = messageDiv.querySelector('.alert');
        if (alert) {
            alert.classList.remove('show');
            setTimeout(() => {
                messageDiv.innerHTML = '';
            }, 150);
        }
    }, 5000);
}

// Set max date to today for date input
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('purchase_date');
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('max', today);
    dateInput.value = today;

    // Market selector change handler
    const marketSelect = document.getElementById('market');
    if (marketSelect) {
        marketSelect.addEventListener('change', function() {
            const tickerInput = document.getElementById('ticker');
            const tickerHint = document.getElementById('ticker-hint');

            if (this.value === 'MX') {
                tickerInput.placeholder = 'Ej: FUNO11, DANHOS13';
                tickerHint.textContent = 'Sin .MX (se agrega automáticamente)';
            } else {
                tickerInput.placeholder = 'Ej: AAPL, MSFT';
                tickerHint.textContent = 'Ingresa el ticker sin sufijo';
            }
        });
    }

    // Edit modal market selector change handler
    const editMarketSelect = document.getElementById('edit-market');
    if (editMarketSelect) {
        editMarketSelect.addEventListener('change', function() {
            const editTickerHint = document.getElementById('edit-ticker-hint');

            if (this.value === 'MX') {
                editTickerHint.textContent = 'Sin .MX (se agrega automáticamente)';
            } else {
                editTickerHint.textContent = 'Ingresa el ticker sin sufijo';
            }
        });
    }
});

// Handle form submission
document.getElementById('transactionForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const market = document.getElementById('market').value;
    const ticker = document.getElementById('ticker').value.toUpperCase().trim();
    const purchaseDate = document.getElementById('purchase_date').value;
    const purchasePrice = parseFloat(document.getElementById('purchase_price').value);
    const quantity = parseFloat(document.getElementById('quantity').value);

    // Basic validation
    if (!market || !ticker || !purchaseDate || !purchasePrice || !quantity) {
        showMessage('Por favor completa todos los campos', 'error');
        return;
    }

    // Disable submit button
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Guardando...';

    try {
        const response = await fetch('/api/transactions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                market: market,
                ticker: ticker,
                purchase_date: purchaseDate,
                purchase_price: purchasePrice,
                quantity: quantity
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(`Transacción agregada exitosamente: ${ticker}`, 'success');

            // Reset form
            e.target.reset();
            document.getElementById('market').value = 'MX';
            document.getElementById('purchase_date').value = new Date().toISOString().split('T')[0];

            // Reload data
            loadAllData();
        } else {
            showMessage(data.error || 'Error al agregar transacción', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error de conexión con el servidor', 'error');
    } finally {
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    }
});

// Load transactions history
async function loadTransactions() {
    const tbody = document.getElementById('transactionsTableBody');

    try {
        const response = await fetch('/api/transactions');
        const transactions = await response.json();

        if (transactions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center text-muted py-4">
                        <i class="bi bi-inbox" style="font-size: 2rem;"></i>
                        <p class="mt-2">No hay transacciones registradas. ¡Agrega tu primera inversión!</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = transactions.map(trans => {
            const gainLossClass = getGainLossClass(trans.gain_loss_dollar);

            return `
                <tr class="fade-in-row">
                    <td>${formatDate(trans.purchase_date)}</td>
                    <td><span class="ticker-badge">${trans.ticker}</span></td>
                    <td class="text-end">${formatCurrency(trans.purchase_price)}</td>
                    <td class="text-end">${trans.quantity.toFixed(4)}</td>
                    <td class="text-end">${trans.current_price ? formatCurrency(trans.current_price) : 'N/A'}</td>
                    <td class="text-end">${formatCurrency(trans.invested_value)}</td>
                    <td class="text-end">${trans.current_value ? formatCurrency(trans.current_value) : 'N/A'}</td>
                    <td class="text-end ${gainLossClass}">
                        ${trans.gain_loss_dollar !== null ? formatCurrency(trans.gain_loss_dollar) : 'N/A'}
                    </td>
                    <td class="text-end ${gainLossClass}">
                        ${trans.gain_loss_percent !== null ? formatPercentage(trans.gain_loss_percent) : 'N/A'}
                    </td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-warning me-1" onclick="editTransaction(${trans.id})" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteTransaction(${trans.id})" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading transactions:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle"></i> Error al cargar transacciones
                </td>
            </tr>
        `;
    }
}

// Load consolidated positions
async function loadPositions() {
    const tbody = document.getElementById('positionsTableBody');
    const tfoot = document.getElementById('positionsTotalRow');

    try {
        const response = await fetch('/api/portfolio/summary');
        const data = await response.json();

        if (data.positions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center text-muted py-4">
                        <i class="bi bi-pie-chart" style="font-size: 2rem;"></i>
                        <p class="mt-2">No hay posiciones en la cartera</p>
                    </td>
                </tr>
            `;
            tfoot.innerHTML = '';
            return;
        }

        // Populate table body
        tbody.innerHTML = data.positions.map(pos => {
            const gainLossClass = getGainLossClass(pos.gain_loss_dollar);

            return `
                <tr class="fade-in-row">
                    <td><span class="ticker-badge">${pos.ticker}</span></td>
                    <td class="text-end">${pos.total_quantity.toFixed(4)}</td>
                    <td class="text-end">${formatCurrency(pos.avg_purchase_price)}</td>
                    <td class="text-end">${pos.current_price ? formatCurrency(pos.current_price) : 'N/A'}</td>
                    <td class="text-end">${formatCurrency(pos.total_invested)}</td>
                    <td class="text-end">${pos.current_value ? formatCurrency(pos.current_value) : 'N/A'}</td>
                    <td class="text-end ${gainLossClass}">
                        ${pos.gain_loss_dollar !== null ? formatCurrency(pos.gain_loss_dollar) : 'N/A'}
                    </td>
                    <td class="text-end ${gainLossClass}">
                        ${pos.gain_loss_percent !== null ? formatPercentage(pos.gain_loss_percent) : 'N/A'}
                    </td>
                    <td class="text-end">${pos.weight_percent !== null ? formatPercentage(pos.weight_percent) : 'N/A'}</td>
                </tr>
            `;
        }).join('');

        // Populate totals footer
        const totals = data.totals;
        const totalGainLossClass = getGainLossClass(totals.total_gain_loss_dollar);

        tfoot.innerHTML = `
            <tr>
                <td colspan="4" class="text-end">TOTAL CARTERA</td>
                <td class="text-end">${formatCurrency(totals.total_invested)}</td>
                <td class="text-end">${formatCurrency(totals.total_current_value)}</td>
                <td class="text-end ${totalGainLossClass}">${formatCurrency(totals.total_gain_loss_dollar)}</td>
                <td class="text-end ${totalGainLossClass}">${formatPercentage(totals.total_gain_loss_percent)}</td>
                <td class="text-end">100.00%</td>
            </tr>
        `;

        // Update KPI cards
        updateKPIs(totals);
    } catch (error) {
        console.error('Error loading positions:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle"></i> Error al cargar posiciones
                </td>
            </tr>
        `;
    }
}

// Update KPI cards
function updateKPIs(totals) {
    document.getElementById('kpi-invested').textContent = formatCurrency(totals.total_invested);
    document.getElementById('kpi-current').textContent = formatCurrency(totals.total_current_value);

    const gainDollarElement = document.getElementById('kpi-gain-dollar');
    const gainPercentElement = document.getElementById('kpi-gain-percent');

    gainDollarElement.textContent = formatCurrency(totals.total_gain_loss_dollar);
    gainPercentElement.textContent = formatPercentage(totals.total_gain_loss_percent);

    const gainLossClass = getGainLossClass(totals.total_gain_loss_dollar);
    gainDollarElement.className = `mb-0 ${gainLossClass}`;
    gainPercentElement.className = `mb-0 ${gainLossClass}`;

    document.getElementById('kpi-positions').textContent = totals.num_positions;
    document.getElementById('kpi-transactions').textContent = totals.num_transactions;
}

// Load portfolio evolution chart
async function loadPortfolioChart() {
    const chartDiv = document.getElementById('portfolioChart');

    try {
        const response = await fetch('/api/portfolio/history');
        const data = await response.json();

        if (data.dates.length === 0) {
            chartDiv.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-graph-up"></i>
                    <p>No hay datos suficientes para mostrar el gráfico</p>
                    <p class="text-muted">Agrega transacciones para ver la evolución de tu cartera</p>
                </div>
            `;
            return;
        }

        const trace = {
            x: data.dates,
            y: data.values,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Valor de Cartera',
            line: {
                color: '#007bff',
                width: 3
            },
            marker: {
                color: '#007bff',
                size: 6
            },
            hovertemplate: '<b>%{x}</b><br>Valor: $%{y:,.2f}<extra></extra>'
        };

        const layout = {
            title: {
                text: 'Evolución del Valor de la Cartera',
                font: { size: 16 }
            },
            xaxis: {
                title: 'Fecha',
                showgrid: true,
                gridcolor: '#e9ecef'
            },
            yaxis: {
                title: 'Valor Total (MXN)',
                tickformat: '$,.0f',
                showgrid: true,
                gridcolor: '#e9ecef'
            },
            hovermode: 'closest',
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff',
            margin: { t: 50, r: 30, b: 50, l: 80 }
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d']
        };

        Plotly.newPlot(chartDiv, [trace], layout, config);
    } catch (error) {
        console.error('Error loading chart:', error);
        chartDiv.innerHTML = `
            <div class="text-center text-danger py-5">
                <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
                <p class="mt-2">Error al cargar el gráfico</p>
            </div>
        `;
    }
}

// Load all data
function loadAllData() {
    loadTransactions();
    loadPositions();
    loadPortfolioChart();
}

// CRUD Operations - Edit and Delete

let transactionToDelete = null;

// Open edit modal
async function editTransaction(id) {
    try {
        const response = await fetch(`/api/transactions/${id}`);
        const transaction = await response.json();

        // Fill form with transaction data
        document.getElementById('edit-id').value = transaction.id;

        // Set market
        const market = transaction.market || 'MX';
        document.getElementById('edit-market').value = market;

        // Remove .MX suffix for display
        let displayTicker = transaction.ticker.replace('.MX', '');
        document.getElementById('edit-ticker').value = displayTicker;

        document.getElementById('edit-date').value = transaction.purchase_date;
        document.getElementById('edit-price').value = transaction.purchase_price;
        document.getElementById('edit-quantity').value = transaction.quantity;

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading transaction:', error);
        showMessage('Error al cargar la transacción: ' + error.message, 'error');
    }
}

// Save edited transaction
async function saveEdit() {
    const id = document.getElementById('edit-id').value;
    const market = document.getElementById('edit-market').value;
    const ticker = document.getElementById('edit-ticker').value.trim().toUpperCase();
    const purchaseDate = document.getElementById('edit-date').value;
    const purchasePrice = parseFloat(document.getElementById('edit-price').value);
    const quantity = parseFloat(document.getElementById('edit-quantity').value);

    // Validation
    if (!market || !ticker || !purchaseDate || !purchasePrice || !quantity) {
        showMessage('Por favor completa todos los campos', 'error');
        return;
    }

    if (purchasePrice <= 0 || quantity <= 0) {
        showMessage('El precio y cantidad deben ser mayores a 0', 'error');
        return;
    }

    const data = {
        market: market,
        ticker: ticker,
        purchase_date: purchaseDate,
        purchase_price: purchasePrice,
        quantity: quantity
    };

    try {
        const response = await fetch(`/api/transactions/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
            modal.hide();

            showMessage('Transacción actualizada exitosamente', 'success');

            // Reload data
            loadAllData();
        } else {
            showMessage(result.error || 'Error al actualizar', 'error');
        }
    } catch (error) {
        console.error('Error saving transaction:', error);
        showMessage('Error al guardar: ' + error.message, 'error');
    }
}

// Open delete confirmation modal
async function deleteTransaction(id) {
    try {
        const response = await fetch(`/api/transactions/${id}`);
        const transaction = await response.json();

        transactionToDelete = id;

        // Show transaction details
        document.getElementById('delete-details').innerHTML = `
            <strong>Ticker:</strong> ${transaction.ticker}<br>
            <strong>Fecha:</strong> ${formatDate(transaction.purchase_date)}<br>
            <strong>Cantidad:</strong> ${transaction.quantity.toFixed(4)}<br>
            <strong>Precio:</strong> ${formatCurrency(transaction.purchase_price)}
        `;

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading transaction:', error);
        showMessage('Error al cargar la transacción: ' + error.message, 'error');
    }
}

// Confirm and execute deletion
async function confirmDelete() {
    if (!transactionToDelete) return;

    try {
        const response = await fetch(`/api/transactions/${transactionToDelete}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
            modal.hide();

            showMessage('Transacción eliminada exitosamente', 'success');

            // Clear the ID
            transactionToDelete = null;

            // Reload data
            loadAllData();
        } else {
            showMessage(result.error || 'Error al eliminar', 'error');
        }
    } catch (error) {
        console.error('Error deleting transaction:', error);
        showMessage('Error al eliminar: ' + error.message, 'error');
    }
}

// Initial load
document.addEventListener('DOMContentLoaded', function() {
    loadAllData();

    // Auto-refresh every 5 minutes
    setInterval(loadAllData, 5 * 60 * 1000);
});
