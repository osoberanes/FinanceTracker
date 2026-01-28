let custodianToDelete = null;

// Cargar custodios al iniciar
document.addEventListener('DOMContentLoaded', function() {
    loadCustodians();
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
