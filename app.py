#!/usr/bin/env python3
"""
Application Flask pour la reconnaissance vocale locale avec Vosk
"""
import json
import os
import queue
import sounddevice as sd
import vosk
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete_changez_moi'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
MODEL_PATH = "models/vosk-model-small-fr-0.22"  # Modèle français

# Variables globales
model = None
audio_queue = queue.Queue()
is_recording = False


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
    print("Modèle chargé avec succès!")
    return True


def audio_callback(indata, frames, time, status):
    """Callback pour capturer l'audio"""
    if status:
        print(f"Statut audio: {status}")
    audio_queue.put(bytes(indata))


def recognition_thread():
    """Thread pour la reconnaissance vocale continue"""
    global is_recording, model

    rec = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    rec.SetWords(True)

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
                          dtype='int16', channels=1, callback=audio_callback):
        print("Reconnaissance vocale démarrée...")

        while is_recording:
            try:
                data = audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get('text'):
                    socketio.emit('transcription', {
                        'text': result['text'],
                        'final': True
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
        'is_recording': is_recording
    })


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


if __name__ == '__main__':
    print("=== Application Speech-to-Text pour Grand-Mère ===")

    if load_model():
        print("\nDémarrage du serveur sur http://localhost:5001")
        print("Appuyez sur Ctrl+C pour arrêter")
        socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
    else:
        print("\nImpossible de démarrer sans le modèle Vosk")
        print("Voir le README.md pour les instructions d'installation")
