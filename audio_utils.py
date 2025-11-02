#!/usr/bin/env python3
import numpy as np
import webrtcvad
import noisereduce as nr
from collections import deque


class VoiceActivityDetector:
    def __init__(self, sample_rate=16000, aggressiveness=2):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate
        self.frame_duration_ms = 30
        self.frame_size = int(sample_rate * self.frame_duration_ms / 1000)

    def is_speech(self, audio_data):
        try:
            if len(audio_data) != self.frame_size * 2:
                return True
            return self.vad.is_speech(audio_data, self.sample_rate)
        except Exception:
            return True


class NoiseReducer:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.noise_profile = None
        self.calibration_frames = deque(maxlen=10)
        self.is_calibrated = False

    def calibrate(self, audio_data):
        audio_float = self._bytes_to_float(audio_data)
        self.calibration_frames.append(audio_float)
        if len(self.calibration_frames) == 10 and not self.is_calibrated:
            self.noise_profile = np.concatenate(list(self.calibration_frames))
            self.is_calibrated = True

    def reduce_noise(self, audio_data):
        try:
            if not self.is_calibrated:
                self.calibrate(audio_data)
                return audio_data
            audio_float = self._bytes_to_float(audio_data)
            reduced = nr.reduce_noise(y=audio_float, sr=self.sample_rate, stationary=True, prop_decrease=0.8)
            return self._float_to_bytes(reduced)
        except Exception:
            return audio_data

    def _bytes_to_float(self, audio_bytes):
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        return audio_int16.astype(np.float32) / 32768.0

    def _float_to_bytes(self, audio_float):
        audio_int16 = (audio_float * 32768.0).astype(np.int16)
        return audio_int16.tobytes()


class AudioLevelMeter:
    def __init__(self):
        self.history = deque(maxlen=20)

    def get_level(self, audio_data):
        try:
            audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_int16.astype(np.float32) / 32768.0
            rms = np.sqrt(np.mean(audio_float ** 2))
            level = min(int(rms * 300), 100)
            self.history.append(level)
            return level
        except Exception:
            return 0

    def get_average_level(self):
        return int(np.mean(self.history)) if self.history else 0


class SmartPunctuator:
    def __init__(self):
        self.model = None
        self._model_loaded = False

    def _load_model(self):
        """Lazy loading du modèle ML (uniquement si nécessaire)"""
        if self._model_loaded:
            return
        try:
            from deepmultilingualpunctuation import PunctuationModel
            print("📥 Chargement du modèle de ponctuation ML...")
            self.model = PunctuationModel()
            print("✅ Modèle de ponctuation chargé")
        except Exception as e:
            print(f"⚠️  Modèle de ponctuation ML non disponible: {e}")
            self.model = None
        self._model_loaded = True

    def add_punctuation(self, text):
        """Ponctuation ML avancée (gourmande en CPU)"""
        if not text or not text.strip():
            return text

        # Charger le modèle seulement si nécessaire
        if not self._model_loaded:
            self._load_model()

        if self.model is None:
            return self._basic_punctuation(text)
        try:
            result = self.model.restore_punctuation(text)
            if result:
                result = result[0].upper() + result[1:]
            return result
        except Exception:
            return self._basic_punctuation(text)

    def _basic_punctuation(self, text):
        """Ponctuation basique améliorée (sans ML)"""
        text = text.strip()
        if not text:
            return text

        # Mots interrogatifs français
        question_words = ['comment', 'quoi', 'qui', 'où', 'quand', 'pourquoi',
                         'quel', 'quelle', 'quels', 'quelles', 'combien', 'est-ce']

        # Mots de liaison qui méritent une virgule
        liaison_words = ['mais', 'donc', 'alors', 'ensuite', 'puis', 'enfin',
                        'cependant', 'toutefois', 'néanmoins', 'pourtant']

        # Mettre la première lettre en majuscule
        text = text[0].upper() + text[1:]

        # Ajouter des virgules après les mots de liaison en début de phrase
        words = text.split()
        if len(words) > 1 and words[0].lower() in liaison_words:
            text = words[0] + ',' + ' '.join(words[1:])

        # Déterminer la ponctuation finale
        if text[-1] not in '.!?':
            # Si c'est une question
            first_word = words[0].lower().rstrip(',')
            if first_word in question_words:
                text += ' ?'
            else:
                text += '.'

        return text


class EmergencyDetector:
    EMERGENCY_KEYWORDS = {
        'aide', 'aidez', 'urgence', 'urgent', 'mal', 'douleur',
        'secours', 'appel', 'ambulance', 'docteur', 'médecin',
        'pompiers', 'police', 'danger', 'feu', 'incendie',
        'tombé', 'tombée', 'chute', 'tombe'
    }

    def check_emergency(self, text):
        if not text:
            return False
        words = set(text.lower().split())
        return bool(words & self.EMERGENCY_KEYWORDS)

    def get_emergency_words(self, text):
        if not text:
            return []
        words = set(text.lower().split())
        return list(words & self.EMERGENCY_KEYWORDS)


def calculate_audio_stats(audio_data):
    try:
        audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32) / 32768.0
        return {
            'rms': float(np.sqrt(np.mean(audio_float ** 2))),
            'peak': float(np.max(np.abs(audio_float))),
            'mean': float(np.mean(audio_float)),
            'std': float(np.std(audio_float))
        }
    except Exception:
        return {'rms': 0, 'peak': 0, 'mean': 0, 'std': 0}
