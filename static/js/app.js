/**
 * Ukrposhta International Shipping - Application JavaScript
 *
 * Note: The following variables are defined in index.html before this script loads:
 * - countries, shipmentTypes, categories, sender, hsCodes
 */

// Initialize form elements
function initializeForm() {
    // Populate shipment types
    const typeSelect = document.getElementById('shipmentType');
    const filterType = document.getElementById('filterType');

    if (typeSelect) {
        shipmentTypes.forEach(t => {
            typeSelect.innerHTML += `<option value="${t.code}">${t.name}</option>`;
        });
    }

    if (filterType) {
        filterType.innerHTML = '<option value="">All shipments</option>' +
            shipmentTypes.map(t => `<option value="${t.code}">${t.name}</option>`).join('');
    }

    // Populate countries (sorted)
    const countrySelect = document.getElementById('countrySelect');
    const phoneCode = document.getElementById('phoneCode');
    const sorted = [...countries].sort((a,b) => a.name.localeCompare(b.name));

    if (countrySelect) {
        sorted.forEach(c => {
            countrySelect.innerHTML += `<option value="${c.code}" data-phone="${c.phone}">${c.name}</option>`;
        });
    }

    if (phoneCode) {
        phoneCode.innerHTML = sorted.map(c => `<option value="${c.phone}">${c.phone}</option>`).join('');
    }

    // Populate categories
    const catSelect = document.querySelector('select[name="category"]');
    if (catSelect) {
        categories.forEach(c => {
            catSelect.innerHTML += `<option value="${c.code}">${c.name}</option>`;
        });
    }

    // Update sender info
    const senderInfo = document.querySelector('.sender-info');
    if (senderInfo && sender.name) {
        senderInfo.innerHTML = `
            <p><strong>${sender.name}</strong></p>
            <p>Address: <strong>${sender.address}</strong></p>
        `;
    }

    // Initialize HS code autocomplete
    initHsCodeAutocomplete();

    // Load shipments
    loadShipments();
}

// HS Code autocomplete with live search
function initHsCodeAutocomplete() {
    document.querySelectorAll('.hs-code-input').forEach(input => {
        if (input.dataset.autocompleteInit) return;
        input.dataset.autocompleteInit = 'true';

        const wrapper = input.closest('.autocomplete-wrapper');
        const dropdown = wrapper.querySelector('.autocomplete-dropdown');
        const formGroup = input.closest('.form-group');
        const infoDiv = formGroup.querySelector('.hs-selected-info');
        const descInput = input.closest('.attachment-card').querySelector('.hs-description');

        // Highlight matching text
        function highlightMatch(text, query) {
            const regex = new RegExp(`(${query})`, 'gi');
            return text.replace(regex, '<span class="highlight">$1</span>');
        }

        // Update selected info display
        function updateSelectedInfo(code, desc) {
            if (infoDiv) {
                if (code && desc) {
                    infoDiv.innerHTML = `<strong>${code}</strong> — ${desc}`;
                    infoDiv.classList.add('show');
                } else {
                    infoDiv.classList.remove('show');
                }
            }
        }

        // Check if entered value matches an HS code
        function checkExactMatch(value) {
            const match = hsCodes.find(hs => hs.code === value);
            if (match) {
                updateSelectedInfo(match.code, match.description);
                if (descInput && !descInput.value) {
                    descInput.value = match.description;
                }
            } else {
                updateSelectedInfo(null, null);
            }
        }

        input.addEventListener('input', function() {
            const value = this.value.trim();
            const valueLower = value.toLowerCase();

            checkExactMatch(value);

            if (value.length < 2) {
                dropdown.classList.remove('show');
                return;
            }

            // Search by code OR description
            const matches = hsCodes.filter(hs =>
                hs.code.includes(value) || hs.description.toLowerCase().includes(valueLower)
            ).slice(0, 15);

            if (matches.length === 0) {
                dropdown.innerHTML = '<div class="autocomplete-item" style="color:#999;">No matches found</div>';
                dropdown.classList.add('show');
                return;
            }

            dropdown.innerHTML = matches.map(hs => {
                const codeHighlighted = highlightMatch(hs.code, value);
                const descHighlighted = highlightMatch(hs.description, valueLower);
                return `
                    <div class="autocomplete-item" data-code="${hs.code}" data-desc="${hs.description}">
                        <div class="hs-code">${codeHighlighted}</div>
                        <div class="hs-desc">${descHighlighted}</div>
                    </div>
                `;
            }).join('');

            dropdown.querySelectorAll('.autocomplete-item[data-code]').forEach(item => {
                item.addEventListener('click', function() {
                    const code = this.dataset.code;
                    const desc = this.dataset.desc;
                    input.value = code;
                    updateSelectedInfo(code, desc);
                    if (descInput && !descInput.value) {
                        descInput.value = desc;
                    }
                    dropdown.classList.remove('show');
                });
            });

            dropdown.classList.add('show');
        });

        input.addEventListener('blur', function() {
            setTimeout(() => {
                dropdown.classList.remove('show');
                checkExactMatch(this.value.trim());
            }, 200);
        });

        input.addEventListener('focus', function() {
            if (this.value.length >= 2) {
                this.dispatchEvent(new Event('input'));
            }
        });

        if (input.value) {
            checkExactMatch(input.value.trim());
        }
    });
}

// Tab switching
function showTab(tab) {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.content').forEach(c => c.classList.remove('active'));
    document.querySelector(`.nav-tab[onclick="showTab('${tab}')"]`).classList.add('active');
    document.getElementById(`${tab}-content`).classList.add('active');
}

// Sub-tab switching
function showSubTab(subtab) {
    document.querySelectorAll('.content-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[onclick="showSubTab('${subtab}')"]`).classList.add('active');
    document.getElementById('list-subtab').style.display = subtab === 'list' ? 'block' : 'none';
    document.getElementById('shipment-subtab').style.display = subtab === 'shipment' ? 'block' : 'none';
}

// Sidebar navigation
function navigateTo(section) {
    if (section === 'international') {
        showTab('shipments');
    }
}

// Shipments from API
let allShipments = [];

async function loadShipments() {
    const tbody = document.getElementById('shipmentsTableBody');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:40px; color:#666;">Loading shipments...</td></tr>`;

    try {
        const resp = await fetch('/api/shipments?limit=50');
        const data = await resp.json();

        if (data.success && data.data) {
            allShipments = Array.isArray(data.data) ? data.data : [data.data];
            updateShipmentsTable();
        } else {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:40px; color:#c00;">Error: ${data.error || 'Failed to load'}</td></tr>`;
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:40px; color:#c00;">Connection error: ${e.message}</td></tr>`;
    }
}

function updateShipmentsTable() {
    const tbody = document.getElementById('shipmentsTableBody');
    const filterType = document.getElementById('filterType');
    const filterValue = filterType ? filterType.value : '';

    let shipments = allShipments;
    if (filterValue) {
        shipments = shipments.filter(s => s.type === filterValue);
    }

    if (shipments.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align:center; padding:40px; color:#666;">
                    No shipments found. Click "Create shipment" to add a new international shipment.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = shipments.map((s, i) => {
        const recipient = s.recipient || {};
        const recipientAddr = s.recipientAddress || {};
        const date = s.lastModified || s.created || '';
        const formattedDate = date ? new Date(date).toLocaleString('uk-UA') : '-';

        return `
        <tr>
            <td>${i + 1}</td>
            <td><span class="barcode barcode-link" onclick="trackByBarcode('${s.barcode}')" title="Click to track">${s.barcode || '-'}</span></td>
            <td>${formattedDate}</td>
            <td><span class="status-badge-table ${getStatusClass(s.status)}">${s.status || '-'}</span></td>
            <td>${recipient.name || recipient.firstName || '-'}</td>
            <td>${recipient.phoneNumber || '-'}</td>
            <td>${formatAddress(recipientAddr)}</td>
            <td>
                <a href="/api/label/${s.uuid}" class="btn-icon btn-icon-download" target="_blank" title="Download label">📥</a>
                <button class="btn-icon btn-icon-view" onclick="viewShipmentDetails('${s.uuid}')" title="View details">👁</button>
                ${s.status === 'CREATED' ? `<button class="btn-icon" onclick="deleteShipment('${s.uuid}')" title="Delete shipment" style="color:#c0392b;">🗑</button>` : ''}
            </td>
        </tr>
    `}).join('');
}

function formatAddress(addr) {
    if (!addr) return '-';
    const parts = [addr.country, addr.city, addr.street].filter(Boolean);
    return parts.join(', ') || '-';
}

function getStatusClass(status) {
    if (!status) return 'status-pending';
    const s = status.toLowerCase();
    if (s.includes('deliver')) return 'status-delivered';
    if (s.includes('transit') || s.includes('send')) return 'status-transit';
    return 'status-pending';
}

async function viewShipmentDetails(uuid) {
    const detailsDiv = document.getElementById('shipment-subtab');
    detailsDiv.innerHTML = '<p style="text-align:center; padding:20px;">Loading...</p>';
    showSubTab('shipment');

    try {
        const resp = await fetch(`/api/shipment/${uuid}`);
        const data = await resp.json();

        if (data.success && data.data) {
            const s = data.data;
            const recipient = s.recipient || {};
            const recipientAddr = s.recipientAddress || {};

            detailsDiv.innerHTML = `
                <div class="shipment-card">
                    <h3 style="margin-bottom:15px; color:#1a5276;">Shipment Details</h3>
                    <div class="form-row">
                        <p><strong>Barcode:</strong> <span class="barcode">${s.barcode || '-'}</span></p>
                        <p><strong>UUID:</strong> ${s.uuid || '-'}</p>
                    </div>
                    <div class="form-row">
                        <p><strong>Type:</strong> ${s.type || '-'}</p>
                        <p><strong>Status:</strong> ${s.status || '-'}</p>
                    </div>
                    <div class="form-row">
                        <p><strong>Recipient:</strong> ${recipient.name || '-'}</p>
                        <p><strong>Phone:</strong> ${recipient.phoneNumber || '-'}</p>
                    </div>
                    <div class="form-row">
                        <p><strong>Address:</strong> ${formatAddress(recipientAddr)}</p>
                    </div>
                    <div class="form-row">
                        <p><strong>Weight:</strong> ${s.weight || '-'} g</p>
                        <p><strong>Price:</strong> ${s.deliveryPrice || '-'} UAH</p>
                    </div>
                    <div style="margin-top:20px;">
                        <a href="/api/label/${s.uuid}" class="btn btn-secondary" target="_blank">Download Label (PDF)</a>
                        <button class="btn btn-outline" onclick="trackByBarcode('${s.barcode}')" style="margin-left:10px;">Track</button>
                        ${s.status === 'CREATED' ? `<button class="btn" onclick="deleteShipment('${s.uuid}')" style="margin-left:10px; background:#c0392b; color:white;">Delete</button>` : ''}
                    </div>
                </div>
            `;
        } else {
            detailsDiv.innerHTML = `<p style="color:#c00; padding:20px;">Error: ${data.error}</p>`;
        }
    } catch (e) {
        detailsDiv.innerHTML = `<p style="color:#c00; padding:20px;">Connection error</p>`;
    }
}

function trackByBarcode(barcode) {
    if (!barcode) return;
    document.getElementById('barcodeInput').value = barcode;
    showTab('track');
    trackShipment();
}

async function deleteShipment(uuid) {
    if (!confirm('Are you sure you want to delete this shipment?\n\nNote: Only shipments with status CREATED can be deleted.')) {
        return;
    }

    try {
        const resp = await fetch(`/api/shipment/${uuid}`, {
            method: 'DELETE'
        });
        const data = await resp.json();

        if (data.success) {
            alert('Shipment deleted successfully!');
            loadShipments();
        } else {
            alert('Error: ' + (data.error || 'Could not delete shipment'));
        }
    } catch (e) {
        alert('Connection error: ' + e.message);
    }
}

async function importShipment() {
    const barcode = document.getElementById('importBarcode').value.trim();
    const resultDiv = document.getElementById('importResult');

    if (!barcode) {
        resultDiv.innerHTML = '<div class="error-box">Please enter a barcode</div>';
        return;
    }

    resultDiv.innerHTML = '<p>Importing...</p>';

    try {
        const resp = await fetch('/api/import-shipment', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({barcode: barcode})
        });
        const data = await resp.json();

        if (data.success) {
            resultDiv.innerHTML = `<div class="success-box">Shipment ${barcode} imported successfully! Status: ${data.data.status}</div>`;
            document.getElementById('importBarcode').value = '';
            loadShipments();
        } else {
            resultDiv.innerHTML = `<div class="error-box">${data.error}</div>`;
        }
    } catch (e) {
        resultDiv.innerHTML = `<div class="error-box">Connection error</div>`;
    }
}

// Country change
function onCountryChange() {
    const select = document.getElementById('countrySelect');
    const option = select.options[select.selectedIndex];
    if (option && option.dataset.phone) {
        document.getElementById('phoneCode').value = option.dataset.phone;
    }
    updatePrice();
}

// Shipment type change
function onShipmentTypeChange() {
    const select = document.getElementById('shipmentType');
    const type = shipmentTypes.find(t => t.code === select.value);
    if (type) {
        document.getElementById('shipmentTypeInfo').innerHTML = `Shipment type: <strong>${type.name}</strong> (max ${type.maxWeight}g)`;
        document.getElementById('weightInput').max = type.maxWeight;
    }
    updatePrice();
}

// Attachments
let attachmentIndex = 1;

function addAttachment() {
    const container = document.getElementById('attachmentsContainer');
    const card = document.createElement('div');
    card.className = 'attachment-card';
    card.dataset.index = attachmentIndex++;
    card.innerHTML = `
        <div class="attachment-header">
            <h4>Attachment №${attachmentIndex}</h4>
            <button type="button" class="btn-remove-attachment" onclick="removeAttachment(this)">Delete attachment</button>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>CNFEA code (HS Code): <span class="required">*</span></label>
                <div class="autocomplete-wrapper">
                    <input type="text" name="hsCode[]" class="hs-code-input" placeholder="Enter code or name (e.g. 6109100000 or T-shirt)" required autocomplete="off">
                    <div class="autocomplete-dropdown"></div>
                </div>
                <div class="hs-selected-info"></div>
            </div>
            <div class="form-group">
                <label>Detailed description of the attachment EN: <span class="required">*</span></label>
                <input type="text" name="description[]" class="hs-description" placeholder="e.g. Cotton T-Shirt" required>
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Cost of attachment (for tax declaration): <span class="required">*</span></label>
                <div class="input-with-addon">
                    <input type="number" name="itemCost[]" min="0" step="0.01" placeholder="Cost of attachment" required style="flex:1;">
                    <select name="itemCurrency[]">
                        <option value="UAH">UAH</option>
                        <option value="USD">USD</option>
                        <option value="EUR">EUR</option>
                        <option value="GBP">GBP</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>Number of units, unit: <span class="required">*</span></label>
                <input type="number" name="itemQty[]" min="1" value="1" placeholder="Number of units, unit" required>
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Unpackaged attachment weight, g: <span class="required">*</span></label>
                <input type="number" name="itemWeight[]" min="1" placeholder="Unpackaged attachment weight, g" required>
            </div>
            <div class="form-group">
                <label>Attachment's country of origin: <span class="required">*</span></label>
                <select name="itemOrigin[]" required>
                    <option value="UA" selected>Ukraine</option>
                </select>
            </div>
        </div>
    `;
    container.appendChild(card);
    updateRemoveButtons();
    initHsCodeAutocomplete();
}

function removeAttachment(btn) {
    btn.closest('.attachment-card').remove();
    updateRemoveButtons();
}

function updateRemoveButtons() {
    const cards = document.querySelectorAll('.attachment-card');
    cards.forEach((card, i) => {
        const btn = card.querySelector('.btn-remove-attachment');
        btn.style.display = cards.length > 1 ? 'block' : 'none';
    });
}

// Price calculation
async function updatePrice() {
    const country = document.getElementById('countrySelect').value;
    const weight = document.getElementById('weightInput').value;
    const type = document.getElementById('shipmentType').value;
    const priceDisplay = document.getElementById('priceDisplay');
    const priceValue = document.getElementById('priceValue');

    if (!country || !weight || !type) {
        priceDisplay.style.display = 'none';
        return;
    }

    priceValue.textContent = 'Calculating...';
    priceDisplay.style.display = 'block';
    priceDisplay.style.background = '#e8f4f8';

    try {
        const resp = await fetch(`/api/calculate?country=${country}&weight=${weight}&type=${type}`);
        const data = await resp.json();

        if (data.success && data.data) {
            const price = data.data.deliveryPrice || data.data.price || data.data.totalPrice || data.data;
            if (price && typeof price === 'number') {
                priceValue.textContent = price.toFixed(2) + ' UAH';
                priceDisplay.style.background = '#d4edda';
            } else if (typeof price === 'object') {
                const foundPrice = price.deliveryPrice || price.price || price.totalPrice;
                if (foundPrice) {
                    priceValue.textContent = foundPrice.toFixed(2) + ' UAH';
                    priceDisplay.style.background = '#d4edda';
                } else {
                    priceValue.textContent = JSON.stringify(price);
                }
            } else {
                priceValue.textContent = price + ' UAH';
                priceDisplay.style.background = '#d4edda';
            }
        } else {
            priceValue.textContent = 'Error: ' + (data.error || 'Unknown error');
            priceDisplay.style.background = '#f8d7da';
        }
    } catch (e) {
        console.error('Price error:', e);
        priceValue.textContent = 'Connection error';
        priceDisplay.style.background = '#f8d7da';
    }
}

function calculatePrice() {
    updatePrice();
}

function resetForm() {
    document.getElementById('shipmentForm').reset();
    document.getElementById('priceDisplay').style.display = 'none';
    document.getElementById('shipmentResult').innerHTML = '';
}

// Create shipment
async function createShipment(event) {
    event.preventDefault();

    const form = document.getElementById('shipmentForm');
    const submitBtn = document.getElementById('submitBtn');
    const resultDiv = document.getElementById('shipmentResult');

    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving...';

    const formData = new FormData(form);

    // Collect attachments
    const items = [];
    const hsCodesArr = formData.getAll('hsCode[]');
    const descriptions = formData.getAll('description[]');
    const costs = formData.getAll('itemCost[]');
    const currencies = formData.getAll('itemCurrency[]');
    const qtys = formData.getAll('itemQty[]');
    const weights = formData.getAll('itemWeight[]');

    for (let i = 0; i < hsCodesArr.length; i++) {
        items.push({
            hsCode: hsCodesArr[i],
            latinName: descriptions[i],
            price: parseFloat(costs[i]),
            currency: currencies[i],
            quantity: parseInt(qtys[i]),
            weight: parseInt(weights[i]),
            countryOfOrigin: 'UA'
        });
    }

    const shipmentData = {
        type: formData.get('shipmentType'),
        category: formData.get('category'),
        recipient: {
            type: formData.get('recipientType'),
            fullName: formData.get('fullName'),
            phone: formData.get('phoneCode') + formData.get('phone'),
            email: formData.get('email') || null
        },
        address: {
            country: formData.get('country'),
            region: formData.get('region') || null,
            zipCode: formData.get('zipCode') || null,
            city: formData.get('city'),
            address: formData.get('address')
        },
        package: {
            weight: parseInt(formData.get('weight')),
            length: parseInt(formData.get('length')),
            width: parseInt(formData.get('width')),
            height: parseInt(formData.get('height'))
        },
        items: items,
        euInfo: formData.get('euInfo') || null
    };

    try {
        const resp = await fetch('/api/shipment', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(shipmentData)
        });

        const data = await resp.json();

        if (data.success) {
            const s = data.data;
            resultDiv.innerHTML = `
                <div class="success-box">
                    <h3>Shipment Created Successfully!</h3>
                    <p><strong>Barcode:</strong> <span class="barcode">${s.barcode || s.uuid}</span></p>
                    <p><strong>UUID:</strong> ${s.uuid}</p>
                    ${s.deliveryPrice ? `<p><strong>Price:</strong> ${s.deliveryPrice} UAH</p>` : ''}
                    <br>
                    <a href="/api/label/${s.uuid}" class="btn btn-secondary" target="_blank">Download Label (PDF)</a>
                    <button class="btn btn-outline" onclick="showTab('shipments'); loadShipments();" style="margin-left:10px;">View My Shipments</button>
                </div>
            `;

            form.reset();
            document.getElementById('priceDisplay').style.display = 'none';
            loadShipments();
        } else {
            resultDiv.innerHTML = `<div class="error-box"><strong>Error:</strong> ${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-box"><strong>Error:</strong> ${error.message}</div>`;
    }

    submitBtn.disabled = false;
    submitBtn.textContent = 'Save';
}

// Tracking
async function trackShipment() {
    const input = document.getElementById('barcodeInput').value.trim();
    if (!input) return;

    const barcodes = input.split(/[,\s]+/).filter(b => b.length > 0);
    const resultsDiv = document.getElementById('trackResults');

    resultsDiv.innerHTML = '<div class="loading">Loading...</div>';

    try {
        const response = await fetch('/api/track', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({barcodes: barcodes})
        });

        const data = await response.json();

        if (data.success) {
            displayTrackResults(data.data, barcodes);
        } else {
            resultsDiv.innerHTML = `<div class="error-box">${data.error}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error-box">Connection error: ${error.message}</div>`;
    }
}

function displayTrackResults(data, barcodes) {
    const resultsDiv = document.getElementById('trackResults');

    if (!data || (Array.isArray(data) && data.length === 0)) {
        resultsDiv.innerHTML = '<p>Shipment not found</p>';
        return;
    }

    let html = '';
    const shipments = {};
    const items = Array.isArray(data) ? data : [data];

    items.forEach(status => {
        const barcode = status.barcode || 'unknown';
        if (!shipments[barcode]) shipments[barcode] = [];
        shipments[barcode].push(status);
    });

    for (const [barcode, statuses] of Object.entries(shipments)) {
        const lastStatus = statuses[0];
        const statusClass = getTrackStatusClass(lastStatus);
        const statusText = getTrackStatusText(lastStatus);

        html += `
            <div class="shipment-card">
                <div class="shipment-header">
                    <span class="barcode">${barcode}</span>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                <div class="timeline">
        `;

        statuses.forEach(status => {
            html += `
                <div class="timeline-item">
                    <div class="timeline-date">${formatDate(status.date)}</div>
                    <div class="timeline-status">${status.eventName || 'Status'}</div>
                    ${status.country ? `<div class="timeline-location">${status.country}</div>` : ''}
                </div>
            `;
        });

        html += '</div></div>';
    }

    resultsDiv.innerHTML = html;
}

function getTrackStatusClass(status) {
    const name = (status.eventName || '').toLowerCase();
    if (name.includes('deliver')) return 'status-delivered';
    if (name.includes('depart') || name.includes('arriv') || name.includes('transit')) return 'status-transit';
    return 'status-pending';
}

function getTrackStatusText(status) {
    const name = (status.eventName || '').toLowerCase();
    if (name.includes('deliver')) return 'Delivered';
    if (name.includes('depart') || name.includes('transit')) return 'In Transit';
    return 'Processing';
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
        return new Date(dateStr).toLocaleString('en-GB', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    } catch { return dateStr; }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form with data from server
    initializeForm();

    const filterType = document.getElementById('filterType');
    if (filterType) {
        filterType.addEventListener('change', updateShipmentsTable);
    }
});
