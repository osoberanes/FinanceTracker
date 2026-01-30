/**
 * Analysis page JavaScript
 * Handles Swensen diversification analysis and custodian summary
 */

// Global cache for asset class colors
let assetClassColorsCache = null;

// Cargar datos al iniciar
document.addEventListener('DOMContentLoaded', async function() {
    // Cargar colores primero
    await loadAssetClassColors();

    // Luego cargar los datos
    loadCustodianSummary();
    loadSwensenAnalysis();
    loadRecommendations();
});

// Cargar paleta de colores
async function loadAssetClassColors() {
    try {
        const response = await fetch('/api/asset-class-colors');
        assetClassColorsCache = await response.json();
    } catch (error) {
        console.error('Error cargando colores:', error);
        assetClassColorsCache = {};
    }
}

// Obtener color por asset class
function getAssetClassColor(assetClass) {
    if (!assetClassColorsCache) return '#6C757D';
    return assetClassColorsCache[assetClass] || '#6C757D';
}

// ===================================
// RESUMEN POR CUSTODIO
// ===================================

async function loadCustodianSummary() {
    try {
        const response = await fetch('/api/portfolio/by-custodian');
        const data = await response.json();

        if (data.error) {
            console.error('Error:', data.error);
            showCustodianError(data.error);
            return;
        }

        renderCustodianTable(data);
        renderCustodianPieChart(data);

    } catch (error) {
        console.error('Error cargando resumen por custodio:', error);
        showCustodianError(error.message);
    }
}

function showCustodianError(message) {
    document.getElementById('custodian-tbody').innerHTML = `
        <tr>
            <td colspan="6" class="text-center text-danger py-4">
                <i class="bi bi-exclamation-triangle"></i> Error: ${message}
            </td>
        </tr>
    `;
}

function renderCustodianTable(data) {
    const tbody = document.getElementById('custodian-tbody');
    const tfoot = document.getElementById('custodian-tfoot');

    if (!data || data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <i class="bi bi-inbox"></i> No hay datos disponibles
                </td>
            </tr>
        `;
        return;
    }

    // Limpiar
    tbody.innerHTML = '';

    let totalInvested = 0;
    let totalCurrent = 0;
    let totalPositions = 0;

    // Renderizar filas
    data.forEach(item => {
        const tr = document.createElement('tr');

        const gainLossClass = item.gain_loss_dollar >= 0 ? 'text-success' : 'text-danger';
        const gainLossSign = item.gain_loss_dollar >= 0 ? '+' : '';

        // Calcular posiciones (estimado basado en valor)
        const positions = item.positions || 1;

        tr.innerHTML = `
            <td><strong>${item.custodian}</strong></td>
            <td class="text-end">${positions}</td>
            <td class="text-end">$${item.invested.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
            <td class="text-end">$${item.current_value.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
            <td class="text-end ${gainLossClass}">
                ${gainLossSign}$${Math.abs(item.gain_loss_dollar).toLocaleString('es-MX', {minimumFractionDigits: 2})}
            </td>
            <td class="text-end ${gainLossClass}">
                ${gainLossSign}${item.gain_loss_percent.toFixed(2)}%
            </td>
        `;

        tbody.appendChild(tr);

        totalInvested += item.invested;
        totalCurrent += item.current_value;
        totalPositions += positions;
    });

    // Totales
    const totalGainLoss = totalCurrent - totalInvested;
    const totalGainLossPct = totalInvested > 0 ? (totalGainLoss / totalInvested * 100) : 0;
    const totalGLClass = totalGainLoss >= 0 ? 'text-success' : 'text-danger';
    const totalGLSign = totalGainLoss >= 0 ? '+' : '';

    tfoot.innerHTML = `
        <tr>
            <td><strong>TOTAL</strong></td>
            <td class="text-end">${totalPositions}</td>
            <td class="text-end">$${totalInvested.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
            <td class="text-end">$${totalCurrent.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
            <td class="text-end ${totalGLClass}">
                ${totalGLSign}$${Math.abs(totalGainLoss).toLocaleString('es-MX', {minimumFractionDigits: 2})}
            </td>
            <td class="text-end ${totalGLClass}">
                ${totalGLSign}${totalGainLossPct.toFixed(2)}%
            </td>
        </tr>
    `;
}

function renderCustodianPieChart(data) {
    if (!data || data.length === 0) {
        document.getElementById('custodian-pie-chart').innerHTML = '<p class="text-center text-muted">Sin datos</p>';
        return;
    }

    const labels = data.map(item => item.custodian);
    const values = data.map(item => item.current_value);

    const trace = {
        labels: labels,
        values: values,
        type: 'pie',
        hole: 0.4,
        textinfo: 'label+percent',
        textposition: 'outside',
        automargin: true,
        marker: {
            colors: ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1', '#20c997', '#fd7e14', '#6c757d']
        }
    };

    const layout = {
        showlegend: true,
        legend: { orientation: 'h', y: -0.1 },
        margin: { t: 30, b: 50, l: 30, r: 30 }
    };

    Plotly.newPlot('custodian-pie-chart', [trace], layout, {responsive: true});
}

// ===================================
// ANALISIS SWENSEN
// ===================================

async function loadSwensenAnalysis() {
    try {
        const response = await fetch('/api/portfolio/by-asset-class');
        const data = await response.json();

        if (data.error) {
            console.error('Error:', data.error);
            showSwensenError(data.error);
            return;
        }

        renderSwensenTable(data.asset_classes, data.total_value);
        renderSwensenCurrentPie(data.asset_classes);
        renderSwensenIdealPie();
        renderSwensenComparisonBar(data.asset_classes);

    } catch (error) {
        console.error('Error cargando analisis Swensen:', error);
        showSwensenError(error.message);
    }
}

function showSwensenError(message) {
    document.getElementById('swensen-tbody').innerHTML = `
        <tr>
            <td colspan="7" class="text-center text-danger py-4">
                <i class="bi bi-exclamation-triangle"></i> Error: ${message}
            </td>
        </tr>
    `;
}

function renderSwensenTable(assetClasses, totalValue) {
    const tbody = document.getElementById('swensen-tbody');

    if (!assetClasses || assetClasses.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <i class="bi bi-inbox"></i> No hay datos disponibles
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = '';

    assetClasses.forEach(item => {
        const tr = document.createElement('tr');

        // Determinar color de diferencia
        let diffClass = '';
        if (Math.abs(item.diff) > 15) {
            diffClass = item.diff > 0 ? 'bg-danger text-white' : 'bg-warning';
        } else if (Math.abs(item.diff) > 5) {
            diffClass = item.diff > 0 ? 'text-danger' : 'text-warning';
        }

        const diffSign = item.diff > 0 ? '+' : '';

        const glClass = item.gain_loss >= 0 ? 'text-success' : 'text-danger';
        const glSign = item.gain_loss >= 0 ? '+' : '';

        // Mostrar tickers como badges
        const tickerBadges = item.tickers ?
            item.tickers.slice(0, 3).map(t => `<span class="badge bg-secondary me-1">${t}</span>`).join('') +
            (item.tickers.length > 3 ? `<span class="badge bg-light text-dark">+${item.tickers.length - 3}</span>` : '')
            : '-';

        tr.innerHTML = `
            <td>
                <span class="me-2">${item.emoji}</span>
                <strong>${item.name}</strong>
                <br><small class="text-muted">${item.description}</small>
            </td>
            <td class="text-end">$${item.value.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
            <td class="text-end"><strong>${item.percentage.toFixed(1)}%</strong></td>
            <td class="text-end">${item.swensen_target}%</td>
            <td class="text-end ${diffClass}">
                <strong>${diffSign}${item.diff.toFixed(1)}%</strong>
            </td>
            <td class="text-end ${glClass}">
                ${glSign}$${Math.abs(item.gain_loss).toLocaleString('es-MX', {minimumFractionDigits: 0})}
            </td>
            <td>${tickerBadges}</td>
        `;

        tbody.appendChild(tr);
    });

    // Agregar fila de total
    const totalRow = document.createElement('tr');
    totalRow.className = 'table-secondary fw-bold';
    totalRow.innerHTML = `
        <td colspan="2">TOTAL</td>
        <td class="text-end">$${totalValue.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
        <td class="text-end">100%</td>
        <td class="text-end">100%</td>
        <td colspan="2"></td>
    `;
    tbody.appendChild(totalRow);
}

function renderSwensenCurrentPie(assetClasses) {
    if (!assetClasses || assetClasses.length === 0) {
        document.getElementById('swensen-current-pie').innerHTML = '<p class="text-center text-muted">Sin datos</p>';
        return;
    }

    const labels = assetClasses.map(item => `${item.emoji} ${item.name}`);
    const values = assetClasses.map(item => item.percentage);
    const colors = assetClasses.map(item => getAssetClassColor(item.asset_class));

    const trace = {
        labels: labels,
        values: values,
        type: 'pie',
        hole: 0.4,
        textinfo: 'percent',
        textposition: 'inside',
        automargin: true,
        marker: { colors: colors }
    };

    const layout = {
        showlegend: true,
        legend: { orientation: 'v', x: 1, y: 0.5 },
        margin: { t: 20, b: 20, l: 20, r: 100 }
    };

    Plotly.newPlot('swensen-current-pie', [trace], layout, {responsive: true});
}

async function renderSwensenIdealPie() {
    // Obtener modelo ideal desde la API para usar colores consistentes
    try {
        const response = await fetch('/api/asset-classes');
        const assetClasses = await response.json();

        // Filtrar solo los que tienen target > 0
        const idealData = assetClasses.filter(ac => ac.swensen_target > 0);

        const labels = idealData.map(item => `${item.emoji} ${item.name}`);
        const values = idealData.map(item => item.swensen_target);
        const colors = idealData.map(item => item.color);

        const trace = {
            labels: labels,
            values: values,
            type: 'pie',
            hole: 0.4,
            textinfo: 'percent',
            textposition: 'inside',
            automargin: true,
            marker: { colors: colors }
        };

        const layout = {
            showlegend: true,
            legend: { orientation: 'v', x: 1, y: 0.5 },
            margin: { t: 20, b: 20, l: 20, r: 100 }
        };

        Plotly.newPlot('swensen-ideal-pie', [trace], layout, {responsive: true});
    } catch (error) {
        console.error('Error renderizando pie ideal:', error);
        document.getElementById('swensen-ideal-pie').innerHTML = '<p class="text-center text-muted">Error al cargar</p>';
    }
}

function renderSwensenComparisonBar(assetClasses) {
    if (!assetClasses || assetClasses.length === 0) {
        document.getElementById('swensen-comparison-bar').innerHTML = '<p class="text-center text-muted">Sin datos</p>';
        return;
    }

    const names = assetClasses.map(item => `${item.emoji} ${item.name}`);
    const currentPct = assetClasses.map(item => item.percentage);
    const idealPct = assetClasses.map(item => item.swensen_target);
    const colors = assetClasses.map(item => getAssetClassColor(item.asset_class));

    const trace1 = {
        x: currentPct,
        y: names,
        name: 'Tu Portfolio',
        type: 'bar',
        orientation: 'h',
        marker: { color: colors },
        text: currentPct.map(v => v.toFixed(1) + '%'),
        textposition: 'outside'
    };

    const trace2 = {
        x: idealPct,
        y: names,
        name: 'Meta Swensen',
        type: 'bar',
        orientation: 'h',
        marker: { color: '#6c757d', opacity: 0.5 },
        text: idealPct.map(v => v + '%'),
        textposition: 'outside'
    };

    const layout = {
        barmode: 'group',
        xaxis: {
            title: 'Porcentaje (%)',
            range: [0, Math.max(...currentPct, ...idealPct) + 10]
        },
        yaxis: { automargin: true },
        legend: { orientation: 'h', y: 1.1 },
        margin: { l: 200, r: 50, t: 50, b: 50 }
    };

    Plotly.newPlot('swensen-comparison-bar', [trace1, trace2], layout, {responsive: true});
}

// ===================================
// RECOMENDACIONES
// ===================================

async function loadRecommendations() {
    try {
        const response = await fetch('/api/portfolio/rebalancing-recommendations');
        const data = await response.json();

        if (data.error) {
            console.error('Error:', data.error);
            showRecommendationsError(data.error);
            return;
        }

        renderRecommendations(data.recommendations, data.total_value);

    } catch (error) {
        console.error('Error cargando recomendaciones:', error);
        showRecommendationsError(error.message);
    }
}

function showRecommendationsError(message) {
    document.getElementById('recommendations-container').innerHTML = `
        <div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle"></i> Error: ${message}
        </div>
    `;
}

function renderRecommendations(recommendations, totalValue) {
    const container = document.getElementById('recommendations-container');

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = `
            <div class="alert alert-success">
                <h5><i class="bi bi-check-circle"></i> Portfolio Balanceado</h5>
                <p class="mb-0">
                    Tu portfolio esta bien distribuido segun el modelo Swensen adaptado.
                    No se requieren ajustes significativos en este momento.
                </p>
            </div>
            <div class="card mt-3">
                <div class="card-body text-center">
                    <i class="bi bi-trophy text-warning" style="font-size: 3rem;"></i>
                    <h5 class="mt-3">Excelente diversificacion</h5>
                    <p class="text-muted">
                        Continua monitoreando tu portfolio periodicamente.
                    </p>
                </div>
            </div>
        `;
        return;
    }

    // Titulo con resumen
    let html = `
        <div class="alert alert-info mb-4">
            <h5><i class="bi bi-graph-up"></i> Analisis de Rebalanceo</h5>
            <p class="mb-2">
                Se encontraron <strong>${recommendations.length}</strong> desviaciones significativas (>5%) del modelo ideal.
            </p>
            <p class="mb-0">
                Valor total del portfolio: <strong>$${totalValue.toLocaleString('es-MX', {minimumFractionDigits: 2})}</strong>
            </p>
        </div>
    `;

    // Separar por accion
    const toReduce = recommendations.filter(r => r.action === 'reduce');
    const toIncrease = recommendations.filter(r => r.action === 'increase');

    // Mostrar las que hay que reducir
    if (toReduce.length > 0) {
        html += `<h6 class="text-danger mb-3"><i class="bi bi-arrow-down-circle"></i> Posiciones Sobreexpuestas (Reducir)</h6>`;
        toReduce.forEach(rec => {
            html += createRecommendationCard(rec);
        });
    }

    // Mostrar las que hay que aumentar
    if (toIncrease.length > 0) {
        html += `<h6 class="text-success mb-3 mt-4"><i class="bi bi-arrow-up-circle"></i> Posiciones Subexpuestas (Aumentar)</h6>`;
        toIncrease.forEach(rec => {
            html += createRecommendationCard(rec);
        });
    }

    container.innerHTML = html;
}

function createRecommendationCard(rec) {
    const isReduce = rec.action === 'reduce';
    const cardBorder = rec.severity === 'high' ? (isReduce ? 'border-danger' : 'border-warning') : 'border-secondary';
    const headerBg = isReduce ? 'bg-danger text-white' : 'bg-success text-white';
    const actionText = isReduce ? 'REDUCIR' : 'AUMENTAR';
    const actionIcon = isReduce ? 'bi-arrow-down' : 'bi-arrow-up';

    return `
        <div class="card mb-3 ${cardBorder}">
            <div class="card-header ${headerBg}">
                <h6 class="mb-0">
                    <i class="bi ${actionIcon}"></i> ${actionText}: ${rec.emoji} ${rec.name}
                </h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p class="mb-2">
                            <strong>Tu Portfolio:</strong> ${rec.current_pct.toFixed(1)}%<br>
                            <strong>Meta Swensen:</strong> ${rec.ideal_pct}%<br>
                            <strong>Diferencia:</strong>
                            <span class="${isReduce ? 'text-danger' : 'text-warning'}">
                                ${Math.abs(rec.diff_pct).toFixed(1)}% de ${isReduce ? 'sobrepeso' : 'subpeso'}
                            </span>
                        </p>
                    </div>
                    <div class="col-md-6">
                        <p class="mb-2">
                            <strong>Monto sugerido a ${actionText.toLowerCase()}:</strong><br>
                            <span class="fs-4 fw-bold ${isReduce ? 'text-danger' : 'text-success'}">
                                $${Math.abs(rec.amount).toLocaleString('es-MX', {minimumFractionDigits: 0})}
                            </span>
                        </p>
                    </div>
                </div>

                ${rec.severity === 'high' ? `
                    <div class="alert alert-${isReduce ? 'danger' : 'warning'} mb-0 mt-2">
                        <small>
                            <i class="bi bi-exclamation-triangle"></i>
                            <strong>Prioridad Alta:</strong> Esta desviacion es significativa (>15%)
                        </small>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}


// ===================================
// CALCULADORA DE INVERSION
// ===================================

async function calculateInvestment() {
    const amountInput = document.getElementById('investment-amount');
    const amount = parseFloat(amountInput.value);

    if (!amount || amount <= 0) {
        alert('Por favor ingresa un monto valido mayor a 0');
        amountInput.focus();
        return;
    }

    try {
        const response = await fetch('/api/investment-calculator', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount })
        });

        const data = await response.json();

        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }

        renderInvestmentResult(data);

    } catch (error) {
        console.error('Error en calculadora:', error);
        alert('Error al calcular distribucion');
    }
}

function clearInvestmentResult() {
    document.getElementById('investment-amount').value = '';
    document.getElementById('investment-result').style.display = 'none';
}

function renderInvestmentResult(data) {
    const resultDiv = document.getElementById('investment-result');
    const distributionDiv = document.getElementById('investment-distribution');

    resultDiv.style.display = 'block';

    // Filtrar solo los que tienen monto sugerido > 0
    const validDistribution = data.distribution.filter(item => item.suggested_amount > 0);

    // Tabla de distribucion
    let html = `
        <div class="alert alert-success">
            <div class="row">
                <div class="col-md-4">
                    <strong><i class="bi bi-cash"></i> Nueva inversion:</strong><br>
                    <span class="fs-5">$${data.new_investment.toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
                </div>
                <div class="col-md-4">
                    <strong><i class="bi bi-wallet2"></i> Portfolio actual:</strong><br>
                    <span class="fs-5">$${data.current_total.toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
                </div>
                <div class="col-md-4">
                    <strong><i class="bi bi-graph-up-arrow"></i> Portfolio futuro:</strong><br>
                    <span class="fs-5 text-success">$${data.future_total.toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
                </div>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>Clase de Activo</th>
                        <th class="text-end">Valor Actual</th>
                        <th class="text-end">Monto Sugerido</th>
                        <th class="text-end">% de Inversion</th>
                    </tr>
                </thead>
                <tbody>
    `;

    validDistribution.forEach(item => {
        html += `
            <tr>
                <td>${item.emoji} <strong>${item.name}</strong></td>
                <td class="text-end text-muted">
                    $${item.current_value.toLocaleString('es-MX', {minimumFractionDigits: 0})}
                </td>
                <td class="text-end">
                    <span class="fw-bold text-success">
                        $${item.suggested_amount.toLocaleString('es-MX', {minimumFractionDigits: 0})}
                    </span>
                </td>
                <td class="text-end">
                    <span class="badge bg-primary">${item.suggested_pct.toFixed(1)}%</span>
                </td>
            </tr>
        `;
    });

    // Total
    const totalSuggested = validDistribution.reduce((sum, item) => sum + item.suggested_amount, 0);

    html += `
                </tbody>
                <tfoot class="table-secondary">
                    <tr>
                        <td><strong>TOTAL</strong></td>
                        <td></td>
                        <td class="text-end">
                            <strong class="text-success">
                                $${totalSuggested.toLocaleString('es-MX', {minimumFractionDigits: 0})}
                            </strong>
                        </td>
                        <td class="text-end">
                            <span class="badge bg-success">100%</span>
                        </td>
                    </tr>
                </tfoot>
            </table>
        </div>
    `;

    distributionDiv.innerHTML = html;

    // Renderizar grafico
    renderInvestmentPieChart(validDistribution);
}

function renderInvestmentPieChart(distribution) {
    if (!distribution || distribution.length === 0) {
        document.getElementById('investment-pie-chart').innerHTML = '<p class="text-center text-muted">Sin datos</p>';
        return;
    }

    const labels = distribution.map(item => `${item.emoji} ${item.name}`);
    const values = distribution.map(item => item.suggested_amount);
    const colors = distribution.map(item => getAssetClassColor(item.asset_class));

    const trace = {
        labels: labels,
        values: values,
        type: 'pie',
        hole: 0.4,
        textinfo: 'label+percent',
        textposition: 'outside',
        automargin: true,
        marker: { colors: colors }
    };

    const layout = {
        showlegend: false,
        height: 350,
        margin: { t: 30, b: 30, l: 30, r: 30 },
        annotations: [{
            text: 'Nueva<br>Inversion',
            showarrow: false,
            font: { size: 14 }
        }]
    };

    Plotly.newPlot('investment-pie-chart', [trace], layout, {responsive: true});
}
