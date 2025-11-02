#!/usr/bin/env python3
"""
Module de gestion des statistiques en temps réel
CPU, mémoire, performances, etc.
"""

import psutil
import time
from collections import deque
from datetime import datetime


class StatsManager:
    """Gestionnaire de statistiques système et application"""

    def __init__(self):
        self.start_time = time.time()
        self.word_count = 0
        self.transcription_count = 0
        self.error_count = 0

        # Historique des statistiques
        self.cpu_history = deque(maxlen=60)  # 60 dernières secondes
        self.memory_history = deque(maxlen=60)
        self.audio_level_history = deque(maxlen=60)

        # Compteurs
        self.session_words = 0
        self.session_transcriptions = 0

    def get_system_stats(self):
        """Obtenir les statistiques système"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # Ajouter à l'historique
            self.cpu_history.append(cpu_percent)
            self.memory_history.append(memory.percent)

            stats = {
                'cpu': {
                    'percent': round(cpu_percent, 1),
                    'count': psutil.cpu_count(),
                    'avg_1min': round(sum(self.cpu_history) / len(self.cpu_history), 1) if self.cpu_history else 0
                },
                'memory': {
                    'percent': round(memory.percent, 1),
                    'used_mb': round(memory.used / 1024 / 1024, 1),
                    'total_mb': round(memory.total / 1024 / 1024, 1),
                    'available_mb': round(memory.available / 1024 / 1024, 1)
                },
                'disk': {
                    'percent': round(psutil.disk_usage('/').percent, 1),
                    'free_gb': round(psutil.disk_usage('/').free / 1024 / 1024 / 1024, 1)
                }
            }

            # Température (si disponible sur Raspberry Pi)
            try:
                temps = psutil.sensors_temperatures()
                if 'cpu_thermal' in temps:
                    stats['temperature'] = {
                        'cpu': round(temps['cpu_thermal'][0].current, 1)
                    }
            except (AttributeError, KeyError):
                pass

            return stats

        except Exception as e:
            print(f"Erreur stats système: {e}")
            return {
                'cpu': {'percent': 0, 'count': 1, 'avg_1min': 0},
                'memory': {'percent': 0, 'used_mb': 0, 'total_mb': 0, 'available_mb': 0},
                'disk': {'percent': 0, 'free_gb': 0}
            }

    def get_app_stats(self):
        """Obtenir les statistiques de l'application"""
        uptime_seconds = int(time.time() - self.start_time)
        uptime_str = self._format_uptime(uptime_seconds)

        return {
            'uptime': uptime_str,
            'uptime_seconds': uptime_seconds,
            'total_transcriptions': self.transcription_count,
            'total_words': self.word_count,
            'error_count': self.error_count,
            'avg_words_per_transcription': round(self.word_count / self.transcription_count, 1) if self.transcription_count > 0 else 0,
            'transcriptions_per_minute': round(self.transcription_count / (uptime_seconds / 60), 2) if uptime_seconds > 0 else 0
        }

    def get_audio_stats(self):
        """Obtenir les statistiques audio"""
        if not self.audio_level_history:
            return {
                'current_level': 0,
                'avg_level': 0,
                'max_level': 0
            }

        return {
            'current_level': self.audio_level_history[-1] if self.audio_level_history else 0,
            'avg_level': round(sum(self.audio_level_history) / len(self.audio_level_history), 1),
            'max_level': max(self.audio_level_history)
        }

    def get_all_stats(self):
        """Obtenir toutes les statistiques"""
        return {
            'system': self.get_system_stats(),
            'app': self.get_app_stats(),
            'audio': self.get_audio_stats(),
            'timestamp': datetime.now().isoformat()
        }

    def increment_transcription(self, text, audio_level=0):
        """Incrémenter les compteurs de transcription"""
        self.transcription_count += 1
        word_count = len(text.split()) if text else 0
        self.word_count += word_count

        if audio_level > 0:
            self.audio_level_history.append(audio_level)

    def increment_error(self):
        """Incrémenter le compteur d'erreurs"""
        self.error_count += 1

    def reset_session_stats(self):
        """Réinitialiser les statistiques de session"""
        self.session_words = 0
        self.session_transcriptions = 0

    def _format_uptime(self, seconds):
        """Formater le temps de fonctionnement"""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if days > 0:
            return f"{days}j {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def get_performance_summary(self):
        """Résumé des performances"""
        system_stats = self.get_system_stats()
        app_stats = self.get_app_stats()

        # Évaluation de la performance
        cpu = system_stats['cpu']['percent']
        memory = system_stats['memory']['percent']

        if cpu > 90 or memory > 90:
            status = "critique"
            color = "red"
        elif cpu > 70 or memory > 70:
            status = "élevé"
            color = "orange"
        elif cpu > 50 or memory > 50:
            status = "modéré"
            color = "yellow"
        else:
            status = "optimal"
            color = "green"

        return {
            'status': status,
            'color': color,
            'cpu_percent': cpu,
            'memory_percent': memory,
            'uptime': app_stats['uptime'],
            'transcription_count': app_stats['total_transcriptions']
        }


# Instance globale
_stats_instance = None


def get_stats_manager():
    """Obtenir l'instance du gestionnaire de statistiques"""
    global _stats_instance
    if _stats_instance is None:
        _stats_instance = StatsManager()
    return _stats_instance
