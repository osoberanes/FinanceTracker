let custodianToDelete = null;

// Variables globales
let assetClassesCache = [];

// Cargar custodios, clasificaciones y configuracion Swensen al iniciar
document.addEventListener('DOMContentLoaded', function() {
    loadCustodians();
    loadAssetClasses();
    loadClassifications();
    loadSwensenConfig();
});

// Cargar lista de custodios
async function loadCustodians() {
    try {
        const response = await fetch('/api/custodians');
        const custodians = await response.json();

        const tbody = document.getElementById('custodians-table');
        tbody.innerHTML = '';

        if (custodians.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No hay custodios registrados</td></tr>';
            return;
        }

        custodians.forEach(custodian => {
            const typeLabels = {
                'broker': '<i class="bi bi-graph-up"></i> Casa de Bolsa',
                'bank': '<i class="bi bi-bank"></i> Banco',
                'crypto_exchange': '<i class="bi bi-currency-bitcoin"></i> Exchange Crypto',
                'government': '<i class="bi bi-building"></i> Gobierno',
                'other': '<i class="bi bi-folder"></i> Otro'
            };

            const row = `
                <tr>
                    <td><strong>${custodian.name}</strong></td>
                    <td>${typeLabels[custodian.type] || custodian.type}</td>
                    <td><span class="badge bg-secondary">0</span></td>
                    <td>${custodian.notes || '<span class="text-muted">-</span>'}</td>
                    <td>
                        <button class="btn btn-sm btn-warning" onclick="editCustodian(${custodian.id})" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteCustodian(${custodian.id}, '${custodian.name}')" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    } catch (error) {
        console.error('Error al cargar custodios:', error);
        const tbody = document.getElementById('custodians-table');
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error al cargar custodios</td></tr>';
    }
}

// Mostrar modal para agregar custodio
function showAddCustodianModal() {
    document.getElementById('custodianModalTitle').textContent = 'Agregar Custodio';
    document.getElementById('custodian-form').reset();
    document.getElementById('custodian-id').value = '';

    const modal = new bootstrap.Modal(document.getElementById('custodianModal'));
    modal.show();
}

// Editar custodio
async function editCustodian(id) {
    try {
        const response = await fetch('/api/custodians');
        const custodians = await response.json();
        const custodian = custodians.find(c => c.id === id);

        if (!custodian) {
            alert('Custodio no encontrado');
            return;
        }

        document.getElementById('custodianModalTitle').textContent = 'Editar Custodio';
        document.getElementById('custodian-id').value = custodian.id;
        document.getElementById('custodian-name').value = custodian.name;
        document.getElementById('custodian-type').value = custodian.type;
        document.getElementById('custodian-notes').value = custodian.notes || '';

        const modal = new bootstrap.Modal(document.getElementById('custodianModal'));
        modal.show();
    } catch (error) {
        console.error('Error al cargar custodio:', error);
        alert('Error al cargar custodio');
    }
}

// Guardar custodio (crear o actualizar)
async function saveCustodian() {
    const id = document.getElementById('custodian-id').value;
    const name = document.getElementById('custodian-name').value.trim();
    const type = document.getElementById('custodian-type').value;
    const notes = document.getElementById('custodian-notes').value.trim();

    if (!name) {
        alert('El nombre es requerido');
        return;
    }

    const data = { name, type, notes };

    try {
        const url = id ? `/api/custodians/${id}` : '/api/custodians';
        const method = id ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('custodianModal')).hide();
            loadCustodians();
            alert(id ? 'Custodio actualizado' : 'Custodio creado exitosamente');
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'No se pudo guardar'));
        }
    } catch (error) {
        console.error('Error al guardar custodio:', error);
        alert('Error al guardar custodio');
    }
}

// Preparar eliminación
function deleteCustodian(id, name) {
    custodianToDelete = id;
    document.getElementById('delete-custodian-details').innerHTML =
        `<strong>Custodio:</strong> ${name}`;

    const modal = new bootstrap.Modal(document.getElementById('deleteCustodianModal'));
    modal.show();
}

// Confirmar eliminación
async function confirmDeleteCustodian() {
    if (!custodianToDelete) return;

    try {
        const response = await fetch(`/api/custodians/${custodianToDelete}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('deleteCustodianModal')).hide();
            loadCustodians();
            const result = await response.json();
            alert(result.message);
        } else {
            alert('Error al eliminar custodio');
        }
    } catch (error) {
        console.error('Error al eliminar custodian:', error);
        alert('Error al eliminar custodio');
    }
}


// ===================================
// CONFIGURACION SWENSEN
// ===================================

async function loadSwensenConfig() {
    try {
        const response = await fetch('/api/swensen-config');
        const data = await response.json();

        if (data.error) {
            console.error('Error:', data.error);
            return;
        }

        renderSwensenConfigTable(data);

    } catch (error) {
        console.error('Error cargando configuracion Swensen:', error);
    }
}

function renderSwensenConfigTable(configs) {
    const tbody = document.getElementById('swensen-config-tbody');
    tbody.innerHTML = '';

    configs.forEach(config => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <span class="me-2">${config.emoji}</span>
                <strong>${config.name}</strong>
                <br><small class="text-muted">${config.description}</small>
            </td>
            <td>
                <input type="number"
                       class="form-control form-control-sm swensen-target-input"
                       id="target-${config.asset_class}"
                       data-asset-class="${config.asset_class}"
                       value="${config.target_percentage}"
                       min="0"
                       max="100"
                       step="0.5"
                       onchange="updateSwensenTotal()">
            </td>
            <td>
                <div class="form-check form-switch">
                    <input class="form-check-input swensen-active-input"
                           type="checkbox"
                           id="active-${config.asset_class}"
                           data-asset-class="${config.asset_class}"
                           ${config.is_active ? 'checked' : ''}
                           onchange="updateSwensenTotal()">
                </div>
            </td>
            <td>
                <input type="text"
                       class="form-control form-control-sm"
                       id="notes-${config.asset_class}"
                       data-asset-class="${config.asset_class}"
                       value="${config.notes || ''}"
                       placeholder="Notas opcionales">
            </td>
        `;
        tbody.appendChild(tr);
    });

    updateSwensenTotal();
}

function updateSwensenTotal() {
    const inputs = document.querySelectorAll('.swensen-target-input');
    let total = 0;

    inputs.forEach(input => {
        const assetClass = input.dataset.assetClass;
        const activeCheckbox = document.getElementById(`active-${assetClass}`);

        // Solo sumar si esta activo
        if (activeCheckbox && activeCheckbox.checked) {
            total += parseFloat(input.value) || 0;
        }
    });

    const totalSpan = document.getElementById('swensen-total');
    const statusSpan = document.getElementById('swensen-total-status');
    totalSpan.textContent = total.toFixed(1);

    // Colorear segun si suma 100%
    if (Math.abs(total - 100) < 0.5) {
        totalSpan.className = 'fw-bold text-success';
        statusSpan.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
    } else {
        totalSpan.className = 'fw-bold text-danger';
        statusSpan.innerHTML = '<i class="bi bi-exclamation-circle-fill text-danger"></i>';
    }
}

async function saveSwensenConfig() {
    try {
        // Recolectar datos
        const configs = [];
        const inputs = document.querySelectorAll('.swensen-target-input');

        inputs.forEach(input => {
            const assetClass = input.dataset.assetClass;
            const target = parseFloat(input.value) || 0;
            const active = document.getElementById(`active-${assetClass}`).checked;
            const notes = document.getElementById(`notes-${assetClass}`).value;

            configs.push({
                asset_class: assetClass,
                target_percentage: target,
                is_active: active,
                notes: notes
            });
        });

        // Validar que sume 100%
        const total = configs.filter(c => c.is_active).reduce((sum, c) => sum + c.target_percentage, 0);
        if (Math.abs(total - 100) > 0.5) {
            alert('Los porcentajes de clases activas deben sumar 100%. Actual: ' + total.toFixed(1) + '%');
            return;
        }

        // Enviar al servidor
        const response = await fetch('/api/swensen-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ configs: configs })
        });

        if (response.ok) {
            alert('Configuracion guardada exitosamente');
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }

    } catch (error) {
        console.error('Error guardando configuracion:', error);
        alert('Error al guardar configuracion');
    }
}

async function resetToDefaultSwensen() {
    if (!confirm('Restaurar valores por defecto del modelo Swensen? Se perderan los cambios actuales.')) {
        return;
    }

    try {
        const response = await fetch('/api/swensen-config/reset', {
            method: 'POST'
        });

        if (response.ok) {
            alert('Configuracion restaurada a valores por defecto');
            loadSwensenConfig(); // Recargar
        } else {
            alert('Error al restaurar configuracion');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Error al restaurar configuracion');
    }
}


// ===================================
// CLASIFICACIONES DE ACTIVOS
// ===================================

async function loadAssetClasses() {
    try {
        const response = await fetch('/api/asset-classes');
        assetClassesCache = await response.json();
        renderColorPalette();
    } catch (error) {
        console.error('Error cargando clases de activo:', error);
    }
}

function renderColorPalette() {
    const container = document.getElementById('color-palette');
    if (!container) return;

    container.innerHTML = assetClassesCache.map(ac => `
        <span class="badge" style="background-color: ${ac.color}; color: white; padding: 8px 12px;">
            ${ac.emoji} ${ac.name}
        </span>
    `).join('');
}

async function loadClassifications() {
    try {
        const response = await fetch('/api/classifications');
        const classifications = await response.json();

        const tbody = document.getElementById('classifications-tbody');
        if (!tbody) return;

        if (classifications.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No hay activos para clasificar</td></tr>';
            return;
        }

        tbody.innerHTML = classifications.map(item => {
            const colorBadge = item.asset_class_color
                ? `<span class="badge" style="background-color: ${item.asset_class_color}; color: white;">${item.asset_class_emoji} ${item.asset_class_name}</span>`
                : '<span class="badge bg-secondary">Sin clasificar</span>';

            const marketLabel = {
                'MX': 'Mexico',
                'US': 'Estados Unidos',
                'CRYPTO': 'Crypto'
            }[item.market] || item.market;

            return `
                <tr>
                    <td><strong>${item.ticker}</strong></td>
                    <td>${marketLabel}</td>
                    <td>${colorBadge}</td>
                    <td>
                        <select class="form-select form-select-sm classification-select"
                                data-ticker="${item.ticker}"
                                style="min-width: 200px;">
                            <option value="">-- Seleccionar --</option>
                            ${assetClassesCache.map(ac => `
                                <option value="${ac.code}" ${item.asset_class === ac.code ? 'selected' : ''}>
                                    ${ac.emoji} ${ac.name}
                                </option>
                            `).join('')}
                        </select>
                    </td>
                    <td class="text-center">
                        <span class="badge bg-secondary">${item.transaction_count}</span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="saveClassification('${item.ticker}')">
                            <i class="bi bi-check-lg"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (error) {
        console.error('Error cargando clasificaciones:', error);
        const tbody = document.getElementById('classifications-tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Error al cargar clasificaciones</td></tr>';
        }
    }
}

async function saveClassification(ticker) {
    const select = document.querySelector(`select[data-ticker="${ticker}"]`);
    if (!select) return;

    const newAssetClass = select.value;

    if (!newAssetClass) {
        alert('Por favor selecciona una clasificacion');
        return;
    }

    try {
        const response = await fetch(`/api/classifications/${encodeURIComponent(ticker)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ asset_class: newAssetClass })
        });

        if (response.ok) {
            const result = await response.json();
            alert(`Clasificacion actualizada: ${result.transactions_updated} transacciones`);
            loadClassifications(); // Recargar
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }

    } catch (error) {
        console.error('Error guardando clasificacion:', error);
        alert('Error al guardar clasificacion');
    }
}

async function autoClassifyAll() {
    if (!confirm('Esto reclasificara automaticamente TODOS los activos. Continuar?')) {
        return;
    }

    try {
        const response = await fetch('/api/classifications/auto-classify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force: true })
        });

        if (response.ok) {
            const result = await response.json();
            alert(`Auto-clasificacion completada:\n- Procesados: ${result.total_processed}\n- Reclasificados: ${result.reclassified}`);
            loadClassifications(); // Recargar
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }

    } catch (error) {
        console.error('Error en auto-clasificacion:', error);
        alert('Error al auto-clasificar');
    }
}
