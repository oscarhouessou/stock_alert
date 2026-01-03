const API_URL = window.location.origin; // Force absolute URL

// Elements
const productsList = document.getElementById('products-list');
const micBtn = document.getElementById('mic-btn');
const activateBtn = document.getElementById('activate-btn');
const searchInput = document.getElementById('search-input');
const toast = document.getElementById('toast');

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let audioStream = null; // Keep stream reference
let isActivated = false;

// User ID Management
let userId = localStorage.getItem('stockalert_user_id');
if (!userId) {
    userId = 'user_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('stockalert_user_id', userId);
}
console.log("User ID:", userId);

// Helper for authenticated fetch
async function authFetch(url, options = {}) {
    const headers = options.headers || {};
    headers['X-User-ID'] = userId;
    options.headers = headers;

    console.log(`[AuthFetch] ${options.method || 'GET'} ${url}`, headers);

    try {
        const res = await fetch(url, options);
        return res;
    } catch (err) {
        console.error("[AuthFetch] Network Error:", err);
        throw err;
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    console.log("App initialized");
    fetchProducts();
    fetchSalesHistory();
    setupAudio();
    setupFilters();
    setupConfirmModal();
    setupNavigation();
});

// Navigation
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.view');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const target = item.dataset.target;

            // Update nav active state
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // Show target view
            views.forEach(v => {
                if (v.id === target) {
                    v.classList.remove('hidden');
                } else {
                    v.classList.add('hidden');
                }
            });

            if (target === 'view-sales') {
                document.getElementById('page-title').textContent = 'Vente';
                fetchSalesHistory();
            } else if (target === 'view-inventory') {
                document.getElementById('page-title').textContent = 'Inventaire';
                fetchProducts();
            }
        });
    });
}

// Filters
function setupFilters() {
    const chips = document.querySelectorAll('.chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            chips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            const filter = chip.dataset.filter;
            filterProducts(filter);
        });
    });
}

function filterProducts(filter) {
    if (!window.currentProducts) return;
    let filtered = window.currentProducts;
    if (filter === 'low') {
        filtered = window.currentProducts.filter(p => p.quantity < 5);
    }
    renderList(filtered);
}

// Search Filter
searchInput.addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    const cards = document.querySelectorAll('.product-card');
    cards.forEach(card => {
        const name = card.dataset.name.toLowerCase();
        card.style.display = name.includes(term) ? 'flex' : 'none';
    });
});

// Fetch Products
async function fetchProducts() {
    try {
        const res = await authFetch(`${API_URL}/products`);
        const products = await res.json();
        window.currentProducts = products;
        renderList(products);
        updateStats(products);
    } catch (err) {
        console.error("Error fetching products:", err);
        showToast("Erreur de chargement");
    }
}

function renderList(items) {
    productsList.innerHTML = '';
    if (items.length === 0) {
        productsList.innerHTML = '<div style="text-align:center; padding: 20px; color: #8E8E93;">Aucun produit trouvé.</div>';
        return;
    }
    items.forEach((p) => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.dataset.name = p.name;

        // Determine category icon/color
        let catClass = 'cat-other';
        let catIcon = 'fa-box';
        if (p.category === 'alimentation') { catClass = 'cat-alimentation'; catIcon = 'fa-bowl-food'; }
        else if (p.category === 'vêtements') { catClass = 'cat-vêtements'; catIcon = 'fa-shirt'; }
        else if (p.category === 'cosmétiques') { catClass = 'cat-cosmétiques'; catIcon = 'fa-spray-can'; }

        card.innerHTML = `
            <div class="product-info">
                <div class="product-header">
                    <span class="product-name">${p.name}</span>
                    <span class="category-badge ${catClass}">${p.category}</span>
                </div>
                <div class="product-details">
                    <span class="product-price">${p.price.toLocaleString()} FCFA</span>
                    <span class="product-stock">
                        <i class="fa-solid fa-layer-group" style="font-size: 0.8em;"></i>
                        ${p.quantity} ${p.unit}
                    </span>
                </div>
            </div>
            <div class="product-actions">
                <div class="stock-badge">${p.quantity}</div>
            </div>
        `;
        productsList.appendChild(card);
    });

    // Update stock list on sales page too
    const salesStockList = document.getElementById('sales-stock-list');
    if (salesStockList) {
        salesStockList.innerHTML = items
            .filter(p => p.quantity > 0)
            .map(p => `
                <div class="product-card tiny" style="padding: 10px; border-left: 4px solid var(--primary);">
                    <div class="product-info">
                        <div class="product-name" style="font-size: 1rem;">${p.name}</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">${p.quantity} ${p.unit} dispos</div>
                    </div>
                    <div class="product-price" style="font-size: 0.9rem;">${p.price.toLocaleString()} FCFA</div>
                </div>
            `).join('');
    }
}

async function fetchSalesHistory() {
    try {
        const response = await authFetch(`${API_URL}/sales`);
        if (response.ok) {
            const sales = await response.json();
            renderSales(sales);
            updateSalesStats(sales);
        }
    } catch (err) {
        console.error("Error fetching sales:", err);
    }
}

function renderSales(sales) {
    const salesList = document.getElementById('sales-list');
    if (!salesList) return;

    if (sales.length === 0) {
        salesList.innerHTML = '<div class="empty-state"><p>Aucune vente enregistrée</p></div>';
        return;
    }

    salesList.innerHTML = sales.map(sale => {
        const date = new Date(sale.date).toLocaleString('fr-FR');
        const items = sale.items || [];
        const itemsHtml = items.map(it => `• ${it.product_name} (x${it.quantity})`).join('<br>');

        return `
            <div class="product-card">
                <div class="product-info">
                    <div class="product-name-row">
                        <span class="product-name">${date}</span>
                        <span class="product-category bg-purple">Vente #${sale.id}</span>
                    </div>
                    <div style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 5px;">
                        ${itemsHtml}
                    </div>
                </div>
                <div class="product-details">
                    <div class="product-price">${sale.total_amount.toLocaleString()} FCFA</div>
                </div>
            </div>
        `;
    }).join('');
}

function updateSalesStats(sales) {
    const totalAmount = sales.reduce((sum, s) => sum + s.total_amount, 0);
    const today = new Date().toISOString().split('T')[0];
    const todaySales = sales.filter(s => s.date.startsWith(today)).length;

    const totalEl = document.getElementById('sales-total-amount');
    const todayEl = document.getElementById('sales-today-count');

    if (totalEl) totalEl.textContent = `${totalAmount.toLocaleString()} FCFA`;
    if (todayEl) todayEl.textContent = todaySales;
}

function updateStats(products) {
    document.getElementById('total-count').textContent = products.length;
    const totalVal = products.reduce((sum, p) => sum + (p.price * p.quantity), 0);
    document.getElementById('total-value').textContent = `${totalVal.toLocaleString()} FCFA`;
}

// ========================
// AUDIO HANDLING (TWO-STEP ACTIVATION)
// ========================
let recordingStartTime = null;
let recordingTimer = null;

async function setupAudio() {
    console.log("Setting up audio...");

    // Start Overlay Logic
    const startOverlay = document.getElementById('start-overlay');
    const startBtn = document.getElementById('start-app-btn');

    startBtn.onclick = async function () {
        console.log("Start button clicked");
        await activateAudio();
        startOverlay.classList.add('hidden');
    };

    // Use click instead of mousedown for better compatibility
    micBtn.onclick = async function (e) {
        e.preventDefault();
        console.log("[MIC] Click detected. isActivated:", isActivated, "isRecording:", isRecording);

        if (!isActivated) {
            console.log("[MIC] Trying to activate audio stream...");
            await activateAudio();
            if (!isActivated) {
                console.error("[MIC] Failed to activate audio.");
                showToast("❌ Impossible d'activer le micro.");
                return;
            }
        }

        if (isRecording) {
            console.log("[MIC] Already recording, stopping...");
            stopRecording();
        } else {
            console.log("[MIC] Not recording, starting...");
            await startRecording();
        }
    };
}

async function activateAudio() {
    console.log("Activating audio stream...");

    // Check for Secure Context (required for getUserMedia)
    const isLocal = ['localhost', '127.0.0.1', '0.0.0.0'].includes(window.location.hostname);
    if (window.location.protocol !== 'https:' && !isLocal) {
        showToast("⚠️ Contexte non sécurisé. Le micro ne fonctionnera que via HTTPS ou localhost.");
    }

    // Check if mediaDevices is available
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error("mediaDevices not available");
        showToast("❌ Micro non disponible ou accès refusé.");
        return;
    }

    try {
        audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true
            }
        });

        console.log("Audio stream activated");

        // Keep stream alive
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(audioStream);
        const gainNode = audioContext.createGain();
        gainNode.gain.value = 0;
        source.connect(gainNode);
        gainNode.connect(audioContext.destination);

        isActivated = true;
        micBtn.style.display = 'flex';
        showToast("✅ Micro prêt !");
    } catch (err) {
        console.error("Could not activate audio:", err);
        showToast("❌ Accès micro refusé : " + err.message);
    }
}

async function initMediaRecorder() {
    console.log("Initializing media recorder...");
    try {
        if (!audioStream) {
            await activateAudio();
            if (!audioStream) return false;
        }

        // Expanded MIME type support for Safari/Chrome/Firefox
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4',
            'audio/aac',
            'audio/wav'
        ];

        let preferredType = '';
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                preferredType = type;
                console.log("Selected MIME type:", preferredType);
                break;
            }
        }

        if (!preferredType) {
            console.error("No supported MIME type found for MediaRecorder");
            showToast("❌ Format audio non supporté par ce navigateur");
            return false;
        }

        mediaRecorder = new MediaRecorder(audioStream, { mimeType: preferredType });
        window.currentMimeType = preferredType; // Save for blob creation

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            console.log("MediaRecorder stopped. Chunks:", audioChunks.length);
            const audioBlob = new Blob(audioChunks, { type: window.currentMimeType });
            audioChunks = [];
            if (audioBlob.size > 1000) { // Avoid sending tiny/empty recordings
                await sendAudioCommand(audioBlob);
            } else {
                micBtn.classList.remove('processing');
                showToast("🎤 Enregistrement trop court");
            }
        };
        return true;
    } catch (err) {
        console.error("MediaRecorder init error:", err);
        showToast("❌ Erreur d'initialisation du micro");
        return false;
    }
}

async function startRecording() {
    console.log("startRecording()");

    if (!mediaRecorder) {
        const success = await initMediaRecorder();
        if (!success) return;
    }

    if (mediaRecorder.state === 'recording') return;

    isRecording = true;
    audioChunks = [];
    recordingStartTime = Date.now();

    mediaRecorder.start(250);
    micBtn.classList.add('recording');

    recordingTimer = setInterval(() => {
        // Just keeping the timer for logic, but not updating UI with it
    }, 100);

    showToast("🎤 Je vous écoute...");
}

function stopRecording() {
    console.log("stopRecording(), isRecording:", isRecording, "mediaRecorder.state:", mediaRecorder?.state);

    if (!isRecording) {
        console.log("Not recording, ignoring stop");
        return;
    }

    clearInterval(recordingTimer);
    isRecording = false;

    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        console.log("MediaRecorder.stop() called");
    }

    micBtn.classList.remove('recording');
    micBtn.style.backgroundColor = ''; // Reset
    micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
    micBtn.classList.add('processing');
    showToast("⏳ Analyse en cours...");
}

// ========================
// SEND AUDIO & CONFIRMATION
// ========================
let pendingCommand = null;

async function sendAudioCommand(blob) {
    console.log("Sending audio to server...");

    // Show loading modal
    showLoadingModal();

    const formData = new FormData();
    formData.append("file", blob, "command.webm");

    try {
        const response = await authFetch(`${API_URL}/command/audio`, {
            method: 'POST',
            body: formData
        });

        console.log("Server response status:", response.status);
        const data = await response.json();
        console.log("Server response data:", data);

        micBtn.classList.remove('processing');

        if (response.ok && data.action !== 'unknown') {
            // Show confirmation modal (it will hide loading)
            pendingCommand = data;
            showConfirmModal(data);
        } else {
            hideLoadingModal();
            if (isActivated) micBtn.style.display = 'flex'; // Restore mic
            showToast(data.message || "❌ Commande non comprise. Réessayez.");
        }
    } catch (err) {
        console.error("Error sending audio:", err);
        hideLoadingModal();
        if (isActivated) micBtn.style.display = 'flex'; // Restore mic
        micBtn.classList.remove('processing');
        showToast("❌ Erreur de connexion");
    }
}

// ========================
// LOADING & CONFIRMATION MODALS
// ========================
function setupConfirmModal() {
    // Event listeners for existing modal elements
    const cancelBtn = document.getElementById('modal-cancel');
    const confirmBtn = document.getElementById('modal-confirm');

    if (cancelBtn) cancelBtn.addEventListener('click', hideConfirmModal);
    if (confirmBtn) confirmBtn.addEventListener('click', confirmCommand);
}

function showLoadingModal() {
    document.getElementById('loading-modal').classList.remove('hidden');
    micBtn.style.display = 'none';
}

function hideLoadingModal() {
    document.getElementById('loading-modal').classList.add('hidden');
    // Note: micBtn visibility will be handled by showConfirmModal or hideConfirmModal
}

function showConfirmModal(data) {
    hideLoadingModal();

    // Hide mic button during confirmation
    micBtn.style.display = 'none';

    const modal = document.getElementById('confirm-modal');
    const transcriptionDisplay = document.getElementById('transcription-display');
    const productsList = document.getElementById('products-list-modal');
    const confirmBtn = document.getElementById('modal-confirm');

    // Show original transcription
    transcriptionDisplay.textContent = `"${data.original_text || ''}"`;

    // Get products array (new format)
    const products = data.products || [];
    const action = data.action;

    let actionText = '';
    let actionIcon = '';
    let btnText = 'Valider';

    switch (action) {
        case 'add':
            actionText = 'Ajouter au stock';
            actionIcon = '➕';
            btnText = products.length > 1 ? `Ajouter ${products.length} produits` : 'Ajouter au stock';
            break;
        case 'remove':
            actionText = 'Retirer du stock';
            actionIcon = '➖';
            btnText = products.length > 1 ? `Retirer ${products.length} produits` : 'Retirer du stock';
            break;
        case 'check_stock':
            actionText = 'Vérifier stock';
            actionIcon = '🔍';
            btnText = 'Compris';
            break;
        case 'check_value':
            actionText = 'Vérifier valeur';
            actionIcon = '💰';
            btnText = 'Fermer';
            break;
        default:
            actionText = action;
            actionIcon = '❓';
            btnText = 'Valider';
    }

    if (confirmBtn) confirmBtn.textContent = btnText;

    // Build form for each product
    let productsHTML = '';

    if (products.length === 0) {
        // Add empty product form
        products.push({ name: '', category: 'autres', unit: 'Unité', quantity: '', price: '' });
    }

    products.forEach((p, index) => {
        // Auto-lookup price if it's a sale and price is missing/0
        if ((action === 'sell' || action === 'remove') && (!p.price || p.price === 0)) {
            const existing = window.currentProducts ? window.currentProducts.find(item => item.name.toLowerCase() === p.name.toLowerCase()) : null;
            if (existing) {
                p.price = existing.price;
            }
        }

        const subtotal = (p.price || 0) * (p.quantity || 0);

        productsHTML += `
            <div class="product-edit-card" data-index="${index}">
                <div class="card-header">
                    <div class="action-badge">${actionIcon} ${actionText}</div>
                    ${products.length > 1 ? `<span class="product-number">Produit ${index + 1}</span>` : ''}
                </div>
                
                <div class="edit-row">
                    <label>Nom du produit *</label>
                    <input type="text" class="edit-input" id="edit-name-${index}" value="${p.name || ''}" placeholder="Ex: Riz blanc" />
                </div>
                
                <div class="edit-row-group">
                    <div class="edit-row half">
                        <label>Catégorie *</label>
                        <select class="edit-input" id="edit-category-${index}">
                            <option value="alimentation" ${p.category === 'alimentation' ? 'selected' : ''}>🍚 Alimentation</option>
                            <option value="vêtements" ${p.category === 'vêtements' ? 'selected' : ''}>👕 Vêtements</option>
                            <option value="cosmétiques" ${p.category === 'cosmétiques' ? 'selected' : ''}>💄 Cosmétiques</option>
                            <option value="autres" ${p.category === 'autres' ? 'selected' : ''}>📦 Autres</option>
                        </select>
                    </div>
                    <div class="edit-row half">
                        <label>Unité *</label>
                        <select class="edit-input" id="edit-unit-${index}">
                            <option value="Unité" ${p.unit === 'Unité' ? 'selected' : ''}>Unité</option>
                            <option value="Kg" ${p.unit === 'Kg' ? 'selected' : ''}>Kg</option>
                            <option value="Litre" ${p.unit === 'Litre' ? 'selected' : ''}>Litre</option>
                            <option value="Carton" ${p.unit === 'Carton' ? 'selected' : ''}>Carton</option>
                            <option value="Sac" ${p.unit === 'Sac' ? 'selected' : ''}>Sac</option>
                            <option value="Paquet" ${p.unit === 'Paquet' ? 'selected' : ''}>Paquet</option>
                        </select>
                    </div>
                </div>
                
                <div class="edit-row-group">
                    <div class="edit-row half" style="${(action === 'sell' || action === 'remove') ? 'display: none;' : ''}">
                        <label>Prix unitaire (FCFA) *</label>
                        <input type="number" class="edit-input" id="edit-price-${index}" value="${p.price || ''}" min="0" placeholder="0" />
                    </div>
                    <div class="edit-row ${(action === 'sell' || action === 'remove') ? '' : 'half'}">
                        <label>Quantité *</label>
                        <input type="number" class="edit-input" id="edit-qty-${index}" value="${p.quantity || ''}" min="1" placeholder="0" />
                    </div>
                </div>

                ${(action === 'sell' || action === 'remove') ? `
                    <div class="subtotal-info" style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.85rem; color: #666;">Unit: ${p.price || 0} FCFA</span>
                        <span style="font-weight: 700; color: #1c1c1e;">Total: ${subtotal.toLocaleString()} FCFA</span>
                    </div>
                ` : ''}
                
                <div class="edit-row">
                    <label>Description (optionnel)</label>
                    <input type="text" class="edit-input" id="edit-desc-${index}" value="${p.description || ''}" placeholder="Ex: Qualité premium" />
                </div>
            </div>
        `;
    });

    productsList.innerHTML = productsHTML;
    productsList.dataset.productCount = products.length;

    modal.classList.remove('hidden');
}

function hideConfirmModal() {
    document.getElementById('confirm-modal').classList.add('hidden');
    pendingCommand = null;

    // Show mic button again if activated
    if (isActivated) {
        micBtn.style.display = 'flex';
    }
}

async function confirmCommand() {
    const productCount = parseInt(document.getElementById('products-list-modal').dataset.productCount) || 1;
    const products = [];

    for (let i = 0; i < productCount; i++) {
        const name = document.getElementById(`edit-name-${i}`).value.trim();
        const category = document.getElementById(`edit-category-${i}`).value;
        const unit = document.getElementById(`edit-unit-${i}`).value;
        const price = parseFloat(document.getElementById(`edit-price-${i}`).value) || 0;
        const quantity = parseInt(document.getElementById(`edit-qty-${i}`).value) || 0;
        const description = document.getElementById(`edit-desc-${i}`).value.trim();

        if (!name || quantity <= 0) {
            showToast(`⚠️ Produit ${i + 1}: Nom et quantité requis`);
            return;
        }

        products.push({ name, category, unit, price, quantity, description });
    }

    const action = pendingCommand ? pendingCommand.action : 'add';
    const isSale = (action === 'sell' || action === 'remove');

    hideConfirmModal();
    showLoadingModal();

    try {
        const endpoint = isSale ? `${API_URL}/sales/confirm` : `${API_URL}/products/add-multiple`;

        const response = await authFetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(products)
        });

        hideLoadingModal();

        if (response.ok) {
            const data = await response.json();
            if (isSale) {
                showToast(`✅ Vente enregistrée (${data.total_amount.toLocaleString()} FCFA)`);
            } else {
                showToast(`✅ ${products.length} produit(s) traité(s) !`);
            }

            // Refresh everything
            fetchProducts();
            fetchSalesHistory();
        } else {
            const error = await response.json();
            showToast(`❌ Erreur: ${error.detail || "Action impossible"}`);
        }
    } catch (err) {
        hideLoadingModal();
        console.error(err);
        showToast("❌ Erreur de connexion");
    }

    if (isActivated) micBtn.style.display = 'flex';
    pendingCommand = null;
}

// ========================
// UI HELPERS
// ========================
function showToast(msg) {
    console.log("[TOAST]", msg);
    toast.textContent = msg;
    toast.classList.add('visible');
    setTimeout(() => {
        toast.classList.remove('visible');
    }, 3000);
}
