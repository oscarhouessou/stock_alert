const API_URL = ""; // Relative path

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

// Init
document.addEventListener('DOMContentLoaded', () => {
    console.log("App initialized");
    fetchProducts();
    setupAudio();
    setupFilters();
    setupConfirmModal();
});

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
        const res = await fetch(`${API_URL}/products`);
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

    // Mic button logic
    micBtn.onmousedown = function (e) {
        e.preventDefault();
        e.stopPropagation();

        if (!isActivated) {
            // If somehow not activated, try again
            activateAudio().then(() => {
                if (isActivated) startRecording();
            });
            return;
        }

        console.log("MIC BUTTON MOUSEDOWN! isRecording:", isRecording);
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    };
}

async function activateAudio() {
    console.log("Activating audio stream...");
    showToast("⏳ Activation du micro...");

    // Check if mediaDevices is available (requires HTTPS or localhost)
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error("mediaDevices not available");
        showToast("❌ Micro non disponible. Utilisez localhost ou HTTPS.");
        return;
    }

    try {
        audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true
            }
        });

        console.log("Audio stream activated:", audioStream.getAudioTracks().map(t => t.label));

        // IMPORTANT: Keep stream alive with AudioContext (like test page)
        const audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(audioStream);
        // Connect to a gain node to keep it active
        const gainNode = audioContext.createGain();
        gainNode.gain.value = 0; // Silent
        source.connect(gainNode);
        gainNode.connect(audioContext.destination);
        console.log("AudioContext connected to keep stream alive");

        isActivated = true;

        // Show mic button
        micBtn.style.display = 'flex';

        showToast("✅ Micro activé ! Cliquez pour enregistrer");
    } catch (err) {
        console.error("Could not activate audio:", err);
        showToast("❌ Erreur: " + err.message);
    }
}

async function initMediaRecorder() {
    console.log("Initializing media recorder...");
    try {
        // Use pre-initialized stream, or create new one if needed
        let stream = audioStream;
        if (!stream) {
            console.log("No pre-init stream, requesting new one...");
            stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                }
            });
            audioStream = stream;
        }

        console.log("Using stream with tracks:", stream.getAudioTracks().map(t => t.label));

        // Check available MIME types
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
            ? 'audio/webm;codecs=opus'
            : 'audio/webm';
        console.log("Using MIME type:", mimeType);

        mediaRecorder = new MediaRecorder(stream, { mimeType });

        mediaRecorder.ondataavailable = (event) => {
            console.log("Audio data available:", event.data.size, "bytes");
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            console.log("MediaRecorder onstop fired, chunks:", audioChunks.length);
            const audioBlob = new Blob(audioChunks, { type: mimeType });
            console.log("Audio blob created:", audioBlob.size, "bytes");
            audioChunks = [];
            await sendAudioCommand(audioBlob);
        };
        return true;
    } catch (err) {
        console.error("Mic init error:", err);
        showToast("Accès micro refusé");
        return false;
    }
}

async function toggleRecording() {
    console.log("toggleRecording called, isRecording:", isRecording);

    if (isRecording) {
        console.log("Calling stopRecording...");
        stopRecording();
    } else {
        console.log("Calling startRecording...");
        await startRecording();
    }
}

async function startRecording() {
    console.log("startRecording()");

    if (!mediaRecorder) {
        const success = await initMediaRecorder();
        if (!success) return;
    }

    if (mediaRecorder.state === 'recording') {
        console.log("Already recording, ignoring");
        return;
    }

    isRecording = true;
    audioChunks = [];
    recordingStartTime = Date.now();

    // Use timeslice to get data chunks during recording (every 250ms)
    mediaRecorder.start(250);
    console.log("MediaRecorder started with timeslice, state:", mediaRecorder.state);

    micBtn.classList.add('recording');
    micBtn.style.backgroundColor = '#f44336'; // Red while recording

    // Start timer
    recordingTimer = setInterval(() => {
        const elapsed = ((Date.now() - recordingStartTime) / 1000).toFixed(1);
        micBtn.innerHTML = `<span style="font-size: 14px; font-weight: bold;">${elapsed}s</span>`;
    }, 100);

    showToast("🎤 Parlez maintenant...");
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
        const res = await fetch(`${API_URL}/command/audio`, {
            method: 'POST',
            body: formData
        });

        console.log("Server response status:", res.status);
        const data = await res.json();
        console.log("Server response data:", data);

        micBtn.classList.remove('processing');

        if (res.ok && data.action !== 'unknown') {
            // Show confirmation modal (it will hide loading)
            pendingCommand = data;
            showConfirmModal(data);
        } else {
            hideLoadingModal();
            showToast("❌ Commande non comprise. Réessayez.");
        }
    } catch (err) {
        console.error("Error sending audio:", err);
        hideLoadingModal();
        micBtn.classList.remove('processing');
        showToast("❌ Erreur de connexion");
    }
}

// ========================
// LOADING & CONFIRMATION MODALS
// ========================
function setupConfirmModal() {
    // Create loading modal
    const loadingHTML = `
        <div id="loading-modal" class="modal hidden">
            <div class="modal-backdrop"></div>
            <div class="modal-content loading-content">
                <div class="spinner"></div>
                <h2>⏳ Analyse en cours...</h2>
                <p>Transcription et compréhension de votre commande</p>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loadingHTML);

    // Create confirm modal
    const modalHTML = `
        <div id="confirm-modal" class="modal hidden">
            <div class="modal-backdrop"></div>
            <div class="modal-content">
                <h2>📋 Récapitulatif</h2>
                <p class="transcription-text" id="transcription-display"></p>
                <div id="products-list-modal"></div>
                <div class="modal-actions">
                    <button id="modal-cancel" class="btn btn-cancel">❌ Annuler</button>
                    <button id="modal-confirm" class="btn btn-confirm">✅ Valider</button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Event listeners
    document.getElementById('modal-cancel').addEventListener('click', hideConfirmModal);
    document.getElementById('modal-confirm').addEventListener('click', confirmCommand);
}

function showLoadingModal() {
    document.getElementById('loading-modal').classList.remove('hidden');
}

function hideLoadingModal() {
    document.getElementById('loading-modal').classList.add('hidden');
}

function showConfirmModal(data) {
    hideLoadingModal();

    const modal = document.getElementById('confirm-modal');
    const transcriptionDisplay = document.getElementById('transcription-display');
    const productsList = document.getElementById('products-list-modal');

    // Show original transcription
    transcriptionDisplay.textContent = `"${data.original_text || ''}"`;

    // Get products array (new format)
    const products = data.products || [];
    const action = data.action;

    let actionText = '';
    let actionIcon = '';
    switch (action) {
        case 'add': actionText = 'Ajouter au stock'; actionIcon = '➕'; break;
        case 'remove': actionText = 'Retirer du stock'; actionIcon = '➖'; break;
        case 'check_stock': actionText = 'Vérifier stock'; actionIcon = '🔍'; break;
        case 'check_value': actionText = 'Vérifier valeur'; actionIcon = '💰'; break;
        default: actionText = action; actionIcon = '❓';
    }

    // Build form for each product
    let productsHTML = '';

    if (products.length === 0) {
        // Add empty product form
        products.push({ name: '', category: 'autres', unit: 'Unité', quantity: '', price: '' });
    }

    products.forEach((p, index) => {
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
                    <div class="edit-row half">
                        <label>Prix unitaire (FCFA) *</label>
                        <input type="number" class="edit-input" id="edit-price-${index}" value="${p.price || ''}" min="0" placeholder="0" />
                    </div>
                    <div class="edit-row half">
                        <label>Quantité *</label>
                        <input type="number" class="edit-input" id="edit-qty-${index}" value="${p.quantity || ''}" min="1" placeholder="0" />
                    </div>
                </div>
                
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

    hideConfirmModal();
    showLoadingModal();

    try {
        // Send multiple products
        const res = await fetch(`${API_URL}/products/add-multiple`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ products })
        });

        hideLoadingModal();

        if (res.ok) {
            const results = await res.json();
            const totalAdded = products.reduce((sum, p) => sum + p.quantity, 0);
            showToast(`✅ ${products.length} produit(s) ajouté(s) !`);
            fetchProducts();
        } else {
            showToast("❌ Erreur lors de l'ajout");
        }
    } catch (err) {
        hideLoadingModal();
        console.error(err);
        showToast("❌ Erreur de connexion");
    }

    pendingCommand = null;
}

// ========================
// UI HELPERS
// ========================
function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('visible');
    setTimeout(() => {
        toast.classList.remove('visible');
    }, 3000);
}
