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

// Utility function to format quantity (respects decimals for crypto)
function formatQuantity(value, isCrypto = false) {
    if (value === null || value === undefined) {
        return 'N/A';
    }
    const decimals = isCrypto ? 8 : 0;
    return new Intl.NumberFormat('es-MX', {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimals
    }).format(value);
}

// Validate quantity based on asset type
function validateQuantity(quantity, assetType) {
    const qty = parseFloat(quantity);

    if (isNaN(qty) || qty <= 0) {
        return { valid: false, error: 'La cantidad debe ser mayor a 0' };
    }

    if (assetType !== 'crypto') {
        // Acciones: solo enteros
        if (!Number.isInteger(qty)) {
            return {
                valid: false,
                error: 'Las acciones solo permiten cantidades enteras (sin decimales)'
            };
        }
    }

    return { valid: true, quantity: qty };
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

// Handle market change (show/hide crypto selector and adjust form)
function handleMarketChange() {
    const market = document.getElementById('market').value;
    const tickerInputContainer = document.getElementById('ticker-input-container');
    const cryptoSelectContainer = document.getElementById('crypto-select-container');
    const stakingContainer = document.getElementById('staking-container');
    const tickerInput = document.getElementById('ticker');
    const tickerHint = document.getElementById('ticker-hint');
    const priceInput = document.getElementById('purchase_price');
    const quantityInput = document.getElementById('quantity');
    const quantityFormatHint = document.getElementById('quantity-format-hint');

    if (market === 'CRYPTO') {
        // Show crypto selector, hide ticker input
        tickerInputContainer.style.display = 'none';
        cryptoSelectContainer.style.display = 'block';
        stakingContainer.style.display = 'block';
        tickerInput.required = false;
        document.getElementById('crypto_ticker').required = true;

        // Adjust decimal precision for crypto (8 decimals)
        priceInput.step = '0.00000001';
        quantityInput.step = '0.00000001';
        quantityInput.placeholder = 'Ej: 0.05, 1.5, 12.75';
        if (quantityFormatHint) {
            quantityFormatHint.textContent = 'Crypto: Se permiten hasta 8 decimales';
        }
    } else {
        // Show ticker input, hide crypto selector
        tickerInputContainer.style.display = 'block';
        cryptoSelectContainer.style.display = 'none';
        stakingContainer.style.display = 'none';
        tickerInput.required = true;
        document.getElementById('crypto_ticker').required = false;

        // Reset to integer precision for stocks
        priceInput.step = '0.01';
        quantityInput.step = '1';
        quantityInput.placeholder = 'Ej: 10, 50, 100';
        if (quantityFormatHint) {
            quantityFormatHint.textContent = 'Acciones: Solo numeros enteros';
        }

        // Update ticker hint
        if (market === 'MX') {
            tickerInput.placeholder = 'Ej: FUNO11, DANHOS13';
            tickerHint.textContent = 'Sin .MX (se agrega automaticamente)';
        } else {
            tickerInput.placeholder = 'Ej: AAPL, MSFT';
            tickerHint.textContent = 'Ingresa el ticker sin sufijo';
        }
    }

    // Update available quantity hint if selling
    updateAvailableQuantityHint();
}

// Handle crypto selection change (enable/disable staking for ETH/SOL)
function handleCryptoChange() {
    const cryptoTicker = document.getElementById('crypto_ticker').value;
    const generatesStakingCheckbox = document.getElementById('generates_staking');
    const stakingLabel = document.querySelector('label[for="generates_staking"]');

    // ETH and SOL support staking
    const stakingCryptos = ['ETH', 'SOL'];

    if (stakingCryptos.includes(cryptoTicker)) {
        generatesStakingCheckbox.disabled = false;
        stakingLabel.classList.remove('text-muted');
    } else {
        generatesStakingCheckbox.disabled = true;
        generatesStakingCheckbox.checked = false;
        stakingLabel.classList.add('text-muted');
        document.getElementById('staking-rewards-container').style.display = 'none';
        document.getElementById('staking_rewards').value = '0';
    }

    // Update available quantity hint
    updateAvailableQuantityHint();
}

// Handle transaction type change
function handleTransactionTypeChange() {
    updateAvailableQuantityHint();
}

// Update available quantity hint for sells
async function updateAvailableQuantityHint() {
    const transactionType = document.getElementById('transaction_type').value;
    const market = document.getElementById('market').value;
    const hint = document.getElementById('available-quantity-hint');

    if (!hint) return;

    if (transactionType !== 'sell') {
        hint.classList.add('d-none');
        return;
    }

    // Get ticker
    let ticker = '';
    if (market === 'CRYPTO') {
        ticker = document.getElementById('crypto_ticker').value;
    } else {
        ticker = document.getElementById('ticker').value.toUpperCase();
        if (market === 'MX' && ticker && !ticker.endsWith('.MX')) {
            ticker = ticker + '.MX';
        }
    }

    if (!ticker) {
        hint.classList.add('d-none');
        return;
    }

    try {
        const response = await fetch(`/api/available-quantity/${ticker}`);
        const data = await response.json();

        if (data.available_quantity !== undefined) {
            hint.textContent = `Disponible para venta: ${formatQuantity(data.available_quantity, market === 'CRYPTO')}`;
            hint.classList.remove('d-none');
        } else {
            hint.classList.add('d-none');
        }
    } catch (error) {
        console.error('Error fetching available quantity:', error);
        hint.classList.add('d-none');
    }
}

// Set max date to today for date input
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('purchase_date');
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('max', today);
    dateInput.value = today;

    // Add event listeners for transaction type and ticker changes
    const transactionTypeSelect = document.getElementById('transaction_type');
    if (transactionTypeSelect) {
        transactionTypeSelect.addEventListener('change', handleTransactionTypeChange);
    }

    const tickerInput = document.getElementById('ticker');
    if (tickerInput) {
        tickerInput.addEventListener('change', updateAvailableQuantityHint);
        tickerInput.addEventListener('blur', updateAvailableQuantityHint);
    }

    // Load custodians dropdown
    loadCustodiansDropdown();

    // Market selector change handler
    const marketSelect = document.getElementById('market');
    if (marketSelect) {
        marketSelect.addEventListener('change', handleMarketChange);
    }

    // Crypto ticker change handler
    const cryptoTickerSelect = document.getElementById('crypto_ticker');
    if (cryptoTickerSelect) {
        cryptoTickerSelect.addEventListener('change', handleCryptoChange);
    }

    // Generates staking checkbox handler
    const generatesStakingCheckbox = document.getElementById('generates_staking');
    if (generatesStakingCheckbox) {
        generatesStakingCheckbox.addEventListener('change', function() {
            const stakingRewardsContainer = document.getElementById('staking-rewards-container');
            if (this.checked) {
                stakingRewardsContainer.style.display = 'block';
            } else {
                stakingRewardsContainer.style.display = 'none';
                document.getElementById('staking_rewards').value = '0';
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
    let ticker;

    // Get ticker based on market type
    if (market === 'CRYPTO') {
        ticker = document.getElementById('crypto_ticker').value;
        if (!ticker) {
            showMessage('Por favor selecciona una criptomoneda', 'error');
            return;
        }
    } else {
        ticker = document.getElementById('ticker').value.toUpperCase().trim();

        // Auto-format Mexican tickers
        if (market === 'MX') {
            // Si el ticker termina en MX sin punto (ej: VWOMX), corregir
            if (ticker.endsWith('MX') && !ticker.includes('.MX')) {
                ticker = ticker.slice(0, -2) + '.MX';
            }
            // Si no tiene .MX al final, agregarlo
            else if (!ticker.endsWith('.MX')) {
                ticker = ticker + '.MX';
            }
        }
    }

    const transactionType = document.getElementById('transaction_type').value;
    const purchaseDate = document.getElementById('purchase_date').value;
    const purchasePrice = parseFloat(document.getElementById('purchase_price').value);
    const quantityValue = document.getElementById('quantity').value;
    const custodianId = document.getElementById('custodian').value;
    const generatesStaking = document.getElementById('generates_staking').checked;
    const stakingRewards = parseFloat(document.getElementById('staking_rewards').value) || 0;
    const assetClass = document.getElementById('asset_class').value;

    // Determine asset type for validation
    const assetType = market === 'CRYPTO' ? 'crypto' : 'stock';

    // Validate quantity
    const validation = validateQuantity(quantityValue, assetType);
    if (!validation.valid) {
        showMessage(validation.error, 'error');
        return;
    }
    const quantity = validation.quantity;

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
        const requestBody = {
            asset_type: assetType,
            market: market,
            ticker: ticker,
            transaction_type: transactionType,
            purchase_date: purchaseDate,
            purchase_price: purchasePrice,
            quantity: quantity
        };

        // Add custodian_id if selected
        if (custodianId) {
            requestBody.custodian_id = parseInt(custodianId);
        }

        // Add crypto-specific fields
        if (market === 'CRYPTO') {
            requestBody.generates_staking = generatesStaking;
            requestBody.staking_rewards = stakingRewards;
        }

        // Add asset_class if manually selected
        if (assetClass) {
            requestBody.asset_class = assetClass;
        }

        const response = await fetch('/api/transactions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (response.ok) {
            const assetIcon = market === 'CRYPTO' ? '🪙' : '📊';
            showMessage(`${assetIcon} Transacción agregada exitosamente: ${ticker}`, 'success');

            // Reset form
            e.target.reset();
            document.getElementById('market').value = 'MX';
            document.getElementById('purchase_date').value = new Date().toISOString().split('T')[0];
            handleMarketChange(); // Reset form UI

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
            const isCrypto = trans.asset_type === 'crypto';
            const transTypeIcon = trans.transaction_type === 'buy'
                ? '<span class="badge bg-success">Compra</span>'
                : '<span class="badge bg-danger">Venta</span>';

            return `
                <tr class="fade-in-row">
                    <td>${formatDate(trans.purchase_date)}</td>
                    <td>${transTypeIcon}</td>
                    <td><span class="ticker-badge">${trans.ticker}</span></td>
                    <td class="text-end">${formatCurrency(trans.purchase_price)}</td>
                    <td class="text-end">${formatQuantity(trans.quantity, isCrypto)}</td>
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

// Global variables for chart data
let portfolioChartData = null;
let currentChartRange = 'ALL';

// Load portfolio evolution chart
async function loadPortfolioChart(range = 'ALL') {
    const chartDiv = document.getElementById('portfolioChart');

    try {
        // Clear any existing content (including spinner)
        chartDiv.innerHTML = '';

        const response = await fetch('/api/portfolio/history');
        const data = await response.json();

        // Convert new format [{date, value}] to old format {dates: [], values: []}
        let convertedData = data;
        if (Array.isArray(data) && data.length > 0 && data[0].date) {
            // New format - convert it
            convertedData = {
                dates: data.map(item => item.date),
                values: data.map(item => item.value)
            };
        }

        // Store full data for range filtering
        portfolioChartData = convertedData;

        // Check if we have data
        if (!convertedData || !convertedData.dates || convertedData.dates.length === 0) {
            chartDiv.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="bi bi-graph-up" style="font-size: 2rem;"></i>
                    <p class="mt-3">No hay datos suficientes para mostrar el grafico</p>
                    <p class="text-muted">Agrega transacciones para ver la evolucion de tu cartera</p>
                </div>
            `;
            return;
        }

        // Render with current range
        renderPortfolioChart(range);
    } catch (error) {
        console.error('Error loading chart:', error);
        chartDiv.innerHTML = `
            <div class="text-center text-danger py-5">
                <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
                <p class="mt-2">Error al cargar el grafico</p>
                <p class="text-muted small">${error.message}</p>
            </div>
        `;
    }
}

// Filter data by range and render chart
function renderPortfolioChart(range) {
    if (!portfolioChartData || !portfolioChartData.dates) return;

    const chartDiv = document.getElementById('portfolioChart');

    // Filter data based on range
    let filteredDates = [...portfolioChartData.dates];
    let filteredValues = [...portfolioChartData.values];

    if (range !== 'ALL') {
        const now = new Date();
        let cutoffDate = new Date();

        switch (range) {
            case '1Y':
                cutoffDate.setFullYear(now.getFullYear() - 1);
                break;
            case '3Y':
                cutoffDate.setFullYear(now.getFullYear() - 3);
                break;
            case '5Y':
                cutoffDate.setFullYear(now.getFullYear() - 5);
                break;
        }

        // Filter data points after cutoff date
        const filteredData = portfolioChartData.dates.reduce((acc, date, index) => {
            const dateObj = new Date(date);
            if (dateObj >= cutoffDate) {
                acc.dates.push(date);
                acc.values.push(portfolioChartData.values[index]);
            }
            return acc;
        }, { dates: [], values: [] });

        filteredDates = filteredData.dates;
        filteredValues = filteredData.values;
    }

    // Check if we have filtered data
    if (filteredDates.length === 0) {
        chartDiv.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="bi bi-calendar-x" style="font-size: 2rem;"></i>
                <p class="mt-3">No hay datos para el rango seleccionado</p>
                <p class="text-muted">Selecciona un rango diferente o "Todo"</p>
            </div>
        `;
        return;
    }

    const trace = {
        x: filteredDates,
        y: filteredValues,
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

    const rangeLabels = {
        '1Y': '1 Ano',
        '3Y': '3 Anos',
        '5Y': '5 Anos',
        'ALL': 'Todo el Historico'
    };

    const layout = {
        title: {
            text: `Evolucion del Valor de la Cartera (${rangeLabels[range]})`,
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

    // Render the chart
    Plotly.newPlot(chartDiv, [trace], layout, config);
}

// Set chart range and update button states
function setChartRange(range) {
    currentChartRange = range;

    // Update button states
    const ranges = ['1Y', '3Y', '5Y', 'ALL'];
    ranges.forEach(r => {
        const btn = document.getElementById(`btn-range-${r}`);
        if (btn) {
            if (r === range) {
                btn.classList.remove('btn-outline-light');
                btn.classList.add('btn-light', 'active');
            } else {
                btn.classList.remove('btn-light', 'active');
                btn.classList.add('btn-outline-light');
            }
        }
    });

    // Re-render chart with new range
    if (portfolioChartData) {
        renderPortfolioChart(range);
    }
}

// Load all data
function loadAllData() {
    loadTransactions();
    loadPositions();
    loadPortfolioChart();
    loadAssetClassPieChart();
    loadCustodianPieChart();
    loadPerformanceTable();
}

// CRUD Operations - Edit and Delete

let transactionToDelete = null;

// Handle edit modal market change
function handleEditMarketChange() {
    const market = document.getElementById('edit-market').value;
    const tickerContainer = document.getElementById('edit-ticker-container');
    const cryptoContainer = document.getElementById('edit-crypto-container');
    const stakingContainer = document.getElementById('edit-staking-container');
    const priceInput = document.getElementById('edit-price');
    const quantityInput = document.getElementById('edit-quantity');

    if (market === 'CRYPTO') {
        tickerContainer.style.display = 'none';
        cryptoContainer.style.display = 'block';
        stakingContainer.style.display = 'block';
        priceInput.step = '0.00000001';
        quantityInput.step = '0.00000001';
    } else {
        tickerContainer.style.display = 'block';
        cryptoContainer.style.display = 'none';
        stakingContainer.style.display = 'none';
        priceInput.step = '0.01';
        quantityInput.step = '0.01';
    }
}

// Handle edit staking checkbox change
function handleEditStakingChange() {
    const checkbox = document.getElementById('edit-generates-staking');
    const rewardsContainer = document.getElementById('edit-staking-rewards-container');
    rewardsContainer.style.display = checkbox.checked ? 'block' : 'none';
}

// Open edit modal
async function editTransaction(id) {
    try {
        const response = await fetch(`/api/transactions/${id}`);
        const transaction = await response.json();

        // Fill form with transaction data
        document.getElementById('edit-id').value = transaction.id;
        document.getElementById('edit-asset-type').value = transaction.asset_type || 'stock';

        // Set market
        const market = transaction.market || 'MX';
        document.getElementById('edit-market').value = market;

        // Handle crypto vs stock
        if (market === 'CRYPTO' || transaction.asset_type === 'crypto') {
            document.getElementById('edit-market').value = 'CRYPTO';
            document.getElementById('edit-crypto-ticker').value = transaction.ticker;
            document.getElementById('edit-ticker').value = '';

            // Show crypto fields
            document.getElementById('edit-ticker-container').style.display = 'none';
            document.getElementById('edit-crypto-container').style.display = 'block';
            document.getElementById('edit-staking-container').style.display = 'block';

            // Set staking values
            document.getElementById('edit-generates-staking').checked = transaction.generates_staking || false;
            document.getElementById('edit-staking-rewards').value = transaction.staking_rewards || 0;

            // Show/hide rewards based on checkbox
            document.getElementById('edit-staking-rewards-container').style.display =
                transaction.generates_staking ? 'block' : 'none';

            // Set precision for crypto
            document.getElementById('edit-price').step = '0.00000001';
            document.getElementById('edit-quantity').step = '0.00000001';
        } else {
            // Stock
            document.getElementById('edit-ticker-container').style.display = 'block';
            document.getElementById('edit-crypto-container').style.display = 'none';
            document.getElementById('edit-staking-container').style.display = 'none';

            // Remove .MX suffix for display
            let displayTicker = transaction.ticker.replace('.MX', '');
            document.getElementById('edit-ticker').value = displayTicker;

            // Set precision for stocks
            document.getElementById('edit-price').step = '0.01';
            document.getElementById('edit-quantity').step = '0.01';
        }

        document.getElementById('edit-date').value = transaction.purchase_date;
        document.getElementById('edit-price').value = transaction.purchase_price;
        document.getElementById('edit-quantity').value = transaction.quantity;

        // Set transaction type
        const editTransactionType = document.getElementById('edit-transaction-type');
        if (editTransactionType) {
            editTransactionType.value = transaction.transaction_type || 'buy';
        }

        // Set asset class
        const editAssetClass = document.getElementById('edit-asset-class');
        if (editAssetClass) {
            editAssetClass.value = transaction.asset_class || '';
        }

        // Update quantity hint
        const editQuantityHint = document.getElementById('edit-quantity-hint');
        if (editQuantityHint) {
            if (transaction.asset_type === 'crypto') {
                editQuantityHint.textContent = 'Crypto: Se permiten hasta 8 decimales';
                document.getElementById('edit-quantity').step = '0.00000001';
            } else {
                editQuantityHint.textContent = 'Acciones: Solo numeros enteros';
                document.getElementById('edit-quantity').step = '1';
            }
        }

        // Set custodian
        const editCustodianSelect = document.getElementById('edit-custodian');
        if (editCustodianSelect && transaction.custodian_id) {
            editCustodianSelect.value = transaction.custodian_id;
        } else if (editCustodianSelect) {
            editCustodianSelect.value = '';
        }

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading transaction:', error);
        showMessage('Error al cargar la transaccion: ' + error.message, 'error');
    }
}

// Save edited transaction
async function saveEdit() {
    const id = document.getElementById('edit-id').value;
    const market = document.getElementById('edit-market').value;
    const transactionType = document.getElementById('edit-transaction-type')?.value || 'buy';
    const purchaseDate = document.getElementById('edit-date').value;
    const purchasePrice = parseFloat(document.getElementById('edit-price').value);
    const quantityValue = document.getElementById('edit-quantity').value;
    const custodianId = document.getElementById('edit-custodian')?.value;
    const assetClassValue = document.getElementById('edit-asset-class')?.value;

    // Get ticker based on market type
    let ticker;
    let assetType;

    if (market === 'CRYPTO') {
        ticker = document.getElementById('edit-crypto-ticker').value;
        assetType = 'crypto';
        if (!ticker) {
            showMessage('Por favor selecciona una criptomoneda', 'error');
            return;
        }
    } else {
        ticker = document.getElementById('edit-ticker').value.trim().toUpperCase();
        assetType = 'stock';
        if (!ticker) {
            showMessage('Por favor ingresa el ticker', 'error');
            return;
        }

        // Auto-format Mexican tickers
        if (market === 'MX') {
            // Si el ticker termina en MX sin punto (ej: VWOMX), corregir
            if (ticker.endsWith('MX') && !ticker.includes('.MX')) {
                ticker = ticker.slice(0, -2) + '.MX';
            }
            // Si no tiene .MX al final, agregarlo
            else if (!ticker.endsWith('.MX')) {
                ticker = ticker + '.MX';
            }
        }
    }

    // Validate quantity
    const validation = validateQuantity(quantityValue, assetType);
    if (!validation.valid) {
        showMessage(validation.error, 'error');
        return;
    }
    const quantity = validation.quantity;

    // Validation
    if (!purchaseDate || !purchasePrice || !quantity) {
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
        asset_type: assetType,
        transaction_type: transactionType,
        purchase_date: purchaseDate,
        purchase_price: purchasePrice,
        quantity: quantity
    };

    // Add staking fields for crypto
    if (market === 'CRYPTO') {
        data.generates_staking = document.getElementById('edit-generates-staking').checked;
        data.staking_rewards = parseFloat(document.getElementById('edit-staking-rewards').value) || 0;
    }

    // Add custodian_id if selected
    if (custodianId) {
        data.custodian_id = parseInt(custodianId);
    }

    // Add asset_class if selected
    if (assetClassValue) {
        data.asset_class = assetClassValue;
    }

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

            showMessage('Transaccion actualizada exitosamente', 'success');

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

// Load custodians for dropdown
async function loadCustodiansDropdown() {
    try {
        const response = await fetch('/api/custodians');
        const custodians = await response.json();

        // Fill dropdown in main form
        const select = document.getElementById('custodian');
        if (select) {
            // Clear existing options except first (Sin asignar)
            select.innerHTML = '<option value="">Sin asignar</option>';

            custodians.forEach(custodian => {
                const option = document.createElement('option');
                option.value = custodian.id;
                option.textContent = custodian.name;
                select.appendChild(option);
            });
        }

        // Fill dropdown in edit modal
        const editSelect = document.getElementById('edit-custodian');
        if (editSelect) {
            editSelect.innerHTML = '<option value="">Sin asignar</option>';

            custodians.forEach(custodian => {
                const option = document.createElement('option');
                option.value = custodian.id;
                option.textContent = custodian.name;
                editSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading custodians:', error);
    }
}

// Load pie chart for asset class composition (Swensen diversification)
async function loadAssetClassPieChart() {
    const chartDiv = document.getElementById('asset-class-pie-chart');

    try {
        // Clear any existing content (including spinner)
        chartDiv.innerHTML = '';

        const response = await fetch('/api/portfolio/by-asset-class');
        const data = await response.json();

        if (!data.asset_classes || data.asset_classes.length === 0) {
            chartDiv.innerHTML = '<p class="text-muted text-center py-5">Sin datos para mostrar</p>';
            return;
        }

        // Fetch colors from API
        const colorsResponse = await fetch('/api/asset-class-colors');
        const colorsMap = await colorsResponse.json();

        const labels = data.asset_classes.map(item => `${item.emoji} ${item.name}`);
        const values = data.asset_classes.map(item => item.value || 0);
        const colors = data.asset_classes.map(item => colorsMap[item.asset_class] || '#6C757D');

        const pieData = [{
            values: values,
            labels: labels,
            type: 'pie',
            hole: 0.4,
            textinfo: 'label+percent',
            textposition: 'outside',
            automargin: true,
            marker: {
                colors: colors
            },
            hovertemplate: '<b>%{label}</b><br>Valor: $%{value:,.2f}<br>Porcentaje: %{percent}<extra></extra>'
        }];

        const layout = {
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0,
                y: -0.2
            },
            margin: { t: 20, b: 20, l: 20, r: 20 },
            height: 350
        };

        await Plotly.newPlot('asset-class-pie-chart', pieData, layout, { responsive: true });
    } catch (error) {
        console.error('Error loading asset class pie chart:', error);
        chartDiv.innerHTML = '<p class="text-danger text-center py-5">Error al cargar grafico</p>';
    }
}

// Load pie chart for custodian composition
async function loadCustodianPieChart() {
    const chartDiv = document.getElementById('custodian-pie-chart');

    try {
        // Clear any existing content (including spinner)
        chartDiv.innerHTML = '';

        const response = await fetch('/api/portfolio/by-custodian');
        const data = await response.json();

        if (!data || data.length === 0) {
            chartDiv.innerHTML = '<p class="text-muted text-center py-5">Sin datos de custodios</p>';
            return;
        }

        const custodians = data.map(item => item.custodian || 'Sin asignar');
        const values = data.map(item => item.current_value || 0);

        const pieData = [{
            values: values,
            labels: custodians,
            type: 'pie',
            hole: 0.4,
            textinfo: 'label+percent',
            textposition: 'outside',
            automargin: true,
            marker: {
                colors: ['#6f42c1', '#007bff', '#28a745', '#ffc107', '#dc3545',
                         '#17a2b8', '#fd7e14', '#20c997', '#e83e8c', '#6c757d']
            }
        }];

        const layout = {
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0,
                y: -0.2
            },
            margin: { t: 20, b: 20, l: 20, r: 20 },
            height: 350
        };

        await Plotly.newPlot('custodian-pie-chart', pieData, layout, { responsive: true });
    } catch (error) {
        console.error('Error loading custodian pie chart:', error);
        chartDiv.innerHTML = '<p class="text-danger text-center py-5">Error al cargar gráfico</p>';
    }
}

// Load performance table (top gainers and losers)
async function loadPerformanceTable() {
    try {
        const response = await fetch('/api/portfolio/summary');
        const data = await response.json();

        if (!data.positions || data.positions.length === 0) {
            document.getElementById('top-gainers').innerHTML =
                '<tr><td colspan="3" class="text-center text-muted">Sin datos</td></tr>';
            document.getElementById('top-losers').innerHTML =
                '<tr><td colspan="3" class="text-center text-muted">Sin datos</td></tr>';
            return;
        }

        // Filter positions with valid gain/loss data
        const validPositions = data.positions.filter(item =>
            item.gain_loss_percent !== null && item.gain_loss_percent !== undefined
        );

        if (validPositions.length === 0) {
            document.getElementById('top-gainers').innerHTML =
                '<tr><td colspan="3" class="text-center text-muted">Sin datos</td></tr>';
            document.getElementById('top-losers').innerHTML =
                '<tr><td colspan="3" class="text-center text-muted">Sin datos</td></tr>';
            return;
        }

        // Sort by gain/loss percentage
        const sorted = [...validPositions].sort((a, b) => b.gain_loss_percent - a.gain_loss_percent);

        // Top 5 gainers
        const gainers = sorted.slice(0, 5);
        const gainersHtml = gainers.map(item => `
            <tr>
                <td><strong>${item.ticker}</strong></td>
                <td class="text-end text-success">${formatCurrency(item.gain_loss_dollar)}</td>
                <td class="text-end text-success"><strong>${formatPercentage(item.gain_loss_percent)}</strong></td>
            </tr>
        `).join('');
        document.getElementById('top-gainers').innerHTML = gainersHtml ||
            '<tr><td colspan="3" class="text-center text-muted">Sin datos</td></tr>';

        // Top 5 losers (reverse order)
        const losers = sorted.slice(-5).reverse();
        const losersHtml = losers.map(item => `
            <tr>
                <td><strong>${item.ticker}</strong></td>
                <td class="text-end text-danger">${formatCurrency(item.gain_loss_dollar)}</td>
                <td class="text-end text-danger"><strong>${formatPercentage(item.gain_loss_percent)}</strong></td>
            </tr>
        `).join('');
        document.getElementById('top-losers').innerHTML = losersHtml ||
            '<tr><td colspan="3" class="text-center text-muted">Sin datos</td></tr>';

    } catch (error) {
        console.error('Error loading performance table:', error);
        document.getElementById('top-gainers').innerHTML =
            '<tr><td colspan="3" class="text-center text-danger">Error al cargar</td></tr>';
        document.getElementById('top-losers').innerHTML =
            '<tr><td colspan="3" class="text-center text-danger">Error al cargar</td></tr>';
    }
}

// Initial load
document.addEventListener('DOMContentLoaded', function() {
    loadAllData();

    // Auto-refresh every 5 minutes
    setInterval(loadAllData, 5 * 60 * 1000);
});
