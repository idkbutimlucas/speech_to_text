// Configuration
let socket;
let isRecording = false;
let autoScroll = true;
let currentTheme = 'light';
let autoClearDelay = 30; // en secondes
let autoClearTimer = null;
let lastActivityTime = Date.now();

// Éléments DOM
const currentText = document.getElementById('currentText');
const historyDiv = document.getElementById('transcriptionHistory');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeModal = document.querySelector('.close');
const fontSizeSlider = document.getElementById('fontSize');
const fontSizeValue = document.getElementById('fontSizeValue');
const themeToggle = document.getElementById('themeToggle');
const autoScrollCheckbox = document.getElementById('autoScroll');
const autoClearDelaySelect = document.getElementById('autoClearDelay');
const manualClearBtn = document.getElementById('manualClearBtn');

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    initSocket();
    loadSettings();
    setupEventListeners();
    checkStatus();
});

// Configuration de Socket.IO
function initSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connecté au serveur');
        updateStatus('Connecté', false);
        // Démarrer automatiquement la reconnaissance après connexion
        setTimeout(() => {
            startRecording();
        }, 1000);
    });

    socket.on('disconnect', () => {
        console.log('Déconnecté du serveur');
        updateStatus('Déconnecté', false);
        isRecording = false;
    });

    socket.on('transcription', (data) => {
        // Réinitialiser le timer d'auto-effacement à chaque transcription
        resetAutoClearTimer();

        if (data.final) {
            // Texte final
            if (data.text.trim()) {
                addToHistory(data.text);
                currentText.textContent = '';
            }
        } else {
            // Texte en cours (partiel)
            currentText.textContent = data.text;
        }
    });

    socket.on('recording_started', () => {
        isRecording = true;
        updateStatus('Écoute en cours...', true);
        console.log('Reconnaissance vocale démarrée');
    });

    socket.on('recording_stopped', () => {
        isRecording = false;
        updateStatus('Connecté', false);
        currentText.textContent = '';
        // Redémarrer automatiquement
        setTimeout(() => {
            startRecording();
        }, 2000);
    });

    socket.on('error', (data) => {
        console.error('Erreur:', data.message);
        updateStatus('Erreur', false);
        // Tenter de redémarrer après une erreur
        setTimeout(() => {
            if (!isRecording) {
                startRecording();
            }
        }, 5000);
    });
}

// Événements des boutons
function setupEventListeners() {
    settingsBtn.addEventListener('click', () => settingsModal.style.display = 'block');
    closeModal.addEventListener('click', () => settingsModal.style.display = 'none');

    // Fermer le modal en cliquant en dehors
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });

    // Paramètres
    fontSizeSlider.addEventListener('input', (e) => {
        const size = e.target.value;
        fontSizeValue.textContent = size + 'px';
        currentText.style.fontSize = size + 'px';
        historyDiv.style.fontSize = (size * 0.8) + 'px';
        localStorage.setItem('fontSize', size);
    });

    themeToggle.addEventListener('click', toggleTheme);

    autoScrollCheckbox.addEventListener('change', (e) => {
        autoScroll = e.target.checked;
        localStorage.setItem('autoScroll', autoScroll);
    });

    autoClearDelaySelect.addEventListener('change', (e) => {
        autoClearDelay = parseInt(e.target.value);
        localStorage.setItem('autoClearDelay', autoClearDelay);
        console.log(`Auto-effacement configuré à ${autoClearDelay} secondes`);
        resetAutoClearTimer();
    });

    manualClearBtn.addEventListener('click', () => {
        clearHistory();
        settingsModal.style.display = 'none';
    });
}

// Auto-effacement
function resetAutoClearTimer() {
    // Effacer le timer existant
    if (autoClearTimer) {
        clearTimeout(autoClearTimer);
        autoClearTimer = null;
    }

    // Si l'auto-effacement est désactivé (0), ne pas créer de nouveau timer
    if (autoClearDelay === 0) {
        return;
    }

    // Créer un nouveau timer
    autoClearTimer = setTimeout(() => {
        console.log(`Pas d'activité depuis ${autoClearDelay} secondes, effacement de l'historique`);
        clearHistory(true); // true = effacement silencieux (pas de confirmation)
    }, autoClearDelay * 1000);
}

// Fonctions principales
function startRecording() {
    if (!isRecording) {
        socket.emit('start_recording');
        console.log('Demande de démarrage de la reconnaissance');
    }
}

function stopRecording() {
    socket.emit('stop_recording');
}

function clearHistory(silent = false) {
    if (silent || confirm('Voulez-vous effacer tout l\'historique ?')) {
        historyDiv.innerHTML = '';
        currentText.textContent = '';
        resetAutoClearTimer();
    }
}

function addToHistory(text) {
    const p = document.createElement('p');
    p.textContent = text;

    // Ajouter l'heure
    const timestamp = new Date().toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit'
    });
    const timeSpan = document.createElement('span');
    timeSpan.style.fontSize = '0.7em';
    timeSpan.style.opacity = '0.6';
    timeSpan.style.marginLeft = '10px';
    timeSpan.textContent = `[${timestamp}]`;
    p.appendChild(timeSpan);

    // Ajouter en HAUT de l'historique (texte le plus récent en premier)
    historyDiv.insertBefore(p, historyDiv.firstChild);

    // Défilement automatique vers le haut
    if (autoScroll) {
        historyDiv.scrollTop = 0;
    }

    // Réinitialiser le timer d'auto-effacement
    resetAutoClearTimer();
}

function updateStatus(text, active) {
    statusText.textContent = text;
    if (active) {
        statusIndicator.classList.add('active');
    } else {
        statusIndicator.classList.remove('active');
    }
}

// Paramètres
function loadSettings() {
    // Taille de police
    const savedFontSize = localStorage.getItem('fontSize') || 60;
    fontSizeSlider.value = savedFontSize;
    fontSizeValue.textContent = savedFontSize + 'px';
    currentText.style.fontSize = savedFontSize + 'px';
    historyDiv.style.fontSize = (savedFontSize * 0.8) + 'px';

    // Thème
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        themeToggle.textContent = '☀️ Mode Clair';
        currentTheme = 'dark';
    }

    // Auto-scroll
    const savedAutoScroll = localStorage.getItem('autoScroll');
    if (savedAutoScroll !== null) {
        autoScroll = savedAutoScroll === 'true';
        autoScrollCheckbox.checked = autoScroll;
    }

    // Auto-clear delay
    const savedAutoClearDelay = localStorage.getItem('autoClearDelay');
    if (savedAutoClearDelay !== null) {
        autoClearDelay = parseInt(savedAutoClearDelay);
        autoClearDelaySelect.value = autoClearDelay;
    }

    // Démarrer le timer d'auto-effacement
    resetAutoClearTimer();
}

function toggleTheme() {
    if (currentTheme === 'light') {
        document.body.setAttribute('data-theme', 'dark');
        themeToggle.textContent = '☀️ Mode Clair';
        currentTheme = 'dark';
    } else {
        document.body.removeAttribute('data-theme');
        themeToggle.textContent = '🌙 Mode Sombre';
        currentTheme = 'light';
    }
    localStorage.setItem('theme', currentTheme);
}

// Vérifier le statut du serveur
async function checkStatus() {
    try {
        const response = await fetch('/status');
        const data = await response.json();
        if (data.model_loaded) {
            updateStatus('Prêt', false);
        } else {
            updateStatus('Modèle non chargé', false);
        }
    } catch (error) {
        console.error('Erreur de vérification du statut:', error);
        updateStatus('Erreur de connexion', false);
    }
}

// Détection d'inactivité de la page (optionnel)
// Redémarrer la reconnaissance si la page reprend le focus
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && !isRecording) {
        console.log('Page redevenue visible, redémarrage de la reconnaissance');
        setTimeout(() => {
            startRecording();
        }, 1000);
    }
});
