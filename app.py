#!/usr/bin/env python3
import json
import os
import queue
import sounddevice as sd
import vosk
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import numpy as np

from audio_utils import (
    VoiceActivityDetector,
    NoiseReducer,
    AudioLevelMeter,
    SmartPunctuator,
    EmergencyDetector
)
from database import get_database
from stats_manager import get_stats_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete_changez_moi'
socketio = SocketIO(app, cors_allowed_origins="*")

SAMPLE_RATE = 16000
BLOCK_SIZE = 960  # 60ms - Compatible avec VAD (multiple de 480)
MODEL_PATH = "models/vosk-model-small-fr-0.22"
MAX_QUEUE_SIZE = 10

# Variables globales
model = None
audio_queue = queue.Queue()
is_recording = False

# Instances des utilitaires
vad = VoiceActivityDetector(sample_rate=SAMPLE_RATE, aggressiveness=1)  # 1 = peu agressif, meilleure détection
noise_reducer = NoiseReducer(sample_rate=SAMPLE_RATE)
audio_meter = AudioLevelMeter()
punctuator = SmartPunctuator()
emergency_detector = EmergencyDetector()
db = get_database()
stats = get_stats_manager()

# Configuration équilibrée (peut être modifié par l'utilisateur)
config = {
    'enable_vad': True,                      # ✅ VAD activé
    'enable_noise_reduction': True,          # ✅ Actif pour meilleure qualité
    'enable_punctuation': True,              # ✅ Actif pour lisibilité
    'enable_emergency_detection': True       # ✅ Actif pour sécurité
}


def load_model():
    """Charge le modèle Vosk"""
    global model
    if not os.path.exists(MODEL_PATH):
        print(f"ERREUR: Le modèle n'existe pas à {MODEL_PATH}")
        print("Téléchargez-le depuis https://alphacephei.com/vosk/models")
        print("Utilisez le modèle 'vosk-model-small-fr-0.22' pour le français")
        return False

    print(f"Chargement du modèle depuis {MODEL_PATH}...")
    model = vosk.Model(MODEL_PATH)
    print("✅ Modèle chargé avec succès!")
    return True


def audio_callback(indata, frames, time, status):
    """Callback pour capturer l'audio"""
    if status:
        print(f"Statut audio: {status}")

    # Gestion intelligente de la queue (limite la taille)
    if audio_queue.qsize() > MAX_QUEUE_SIZE:
        try:
            audio_queue.get_nowait()  # Supprimer le plus ancien
        except queue.Empty:
            pass

    audio_queue.put(bytes(indata))


def recognition_thread():
    """Thread pour la reconnaissance vocale continue AMÉLIORÉE"""
    global is_recording, model

    rec = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    rec.SetWords(True)

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype='int16',
        channels=1,
        callback=audio_callback
    ):
        print("🎤 Reconnaissance vocale démarrée avec améliorations...")
        print(f"  VAD: {config['enable_vad']}")
        print(f"  Réduction bruit: {config['enable_noise_reduction']}")
        print(f"  Ponctuation: {config['enable_punctuation']}")
        print(f"  Détection urgence: {config['enable_emergency_detection']}")

        while is_recording:
            try:
                data = audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            # Mesurer le niveau audio
            audio_level = audio_meter.get_level(data)

            # Émettre le niveau audio au client
            socketio.emit('audio_level', {'level': audio_level})

            # VAD: Ne traiter que si c'est de la parole
            if config['enable_vad']:
                if not vad.is_speech(data):
                    continue  # Ignorer le silence

            # Réduction de bruit
            if config['enable_noise_reduction']:
                data = noise_reducer.reduce_noise(data)

            # Reconnaissance Vosk
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get('text'):
                    text = result['text']

                    # Ponctuation automatique
                    if config['enable_punctuation']:
                        # Ponctuation ML (avancée mais gourmande)
                        text = punctuator.add_punctuation(text)
                    else:
                        # Ponctuation basique (légère)
                        text = punctuator._basic_punctuation(text)

                    # Détection d'urgence
                    is_emergency = False
                    emergency_words = []
                    if config['enable_emergency_detection']:
                        is_emergency = emergency_detector.check_emergency(text)
                        if is_emergency:
                            emergency_words = emergency_detector.get_emergency_words(text)
                            print(f"⚠️ URGENCE DÉTECTÉE: {emergency_words}")

                    # Sauvegarder dans la base de données
                    db.add_transcription(
                        text,
                        has_emergency=is_emergency,
                        emergency_words=emergency_words,
                        audio_level=audio_level
                    )

                    # Mettre à jour les statistiques
                    stats.increment_transcription(text, audio_level)

                    # Émettre au client
                    socketio.emit('transcription', {
                        'text': text,
                        'final': True,
                        'is_emergency': is_emergency,
                        'emergency_words': emergency_words
                    })
            else:
                partial = json.loads(rec.PartialResult())
                if partial.get('partial'):
                    socketio.emit('transcription', {
                        'text': partial['partial'],
                        'final': False
                    })


@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')


@app.route('/status')
def status():
    """Vérifier le statut de l'application"""
    return jsonify({
        'model_loaded': model is not None,
        'is_recording': is_recording,
        'config': config
    })


@app.route('/stats')
def get_stats():
    """Obtenir les statistiques"""
    return jsonify(stats.get_all_stats())


@app.route('/config', methods=['GET', 'POST'])
def handle_config():
    """Gérer la configuration"""
    global config
    if request.method == 'POST':
        data = request.get_json()
        config.update(data)
        return jsonify({'status': 'ok', 'config': config})
    return jsonify(config)


@app.route('/history')
def get_history():
    """Récupérer l'historique des transcriptions"""
    limit = request.args.get('limit', 50, type=int)
    transcriptions = db.get_recent_transcriptions(limit)
    return jsonify(transcriptions)


@app.route('/export')
def export_history():
    """Exporter l'historique"""
    from datetime import datetime
    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    count = db.export_to_text(filename)
    return jsonify({'status': 'ok', 'filename': filename, 'count': count})


@socketio.on('start_recording')
def handle_start_recording():
    """Démarre l'enregistrement"""
    global is_recording

    if model is None:
        emit('error', {'message': 'Modèle non chargé'})
        return

    if not is_recording:
        is_recording = True
        thread = threading.Thread(target=recognition_thread)
        thread.daemon = True
        thread.start()
        emit('recording_started', {'status': 'ok'})


@socketio.on('stop_recording')
def handle_stop_recording():
    """Arrête l'enregistrement"""
    global is_recording
    is_recording = False
    emit('recording_stopped', {'status': 'ok'})


@socketio.on('update_config')
def handle_update_config(data):
    """Mettre à jour la configuration"""
    global config
    config.update(data)
    emit('config_updated', {'status': 'ok', 'config': config})


if __name__ == '__main__':
    print("=" * 70)
    print("🎤 Application Speech-to-Text Web - VERSION AMÉLIORÉE")
    print("=" * 70)
    print("\n📦 Fonctionnalités:")
    print("  ✅ VAD (Voice Activity Detection)")
    print("  ✅ Réduction de bruit")
    print("  ✅ Ponctuation automatique")
    print("  ✅ Détection d'urgence")
    print("  ✅ Sauvegarde persistante (SQLite)")
    print("  ✅ Statistiques en temps réel")
    print("  ✅ Optimisations performances\n")

    if load_model():
        print("\nDémarrage du serveur sur http://localhost:5001")
        print("Appuyez sur Ctrl+C pour arrêter")
        print(f"💾 Base de données: {db.get_total_count()} transcriptions sauvegardées\n")
        socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
    else:
        print("\n❌ Impossible de démarrer sans le modèle Vosk")
        print("Voir le README.md pour les instructions d'installation")
