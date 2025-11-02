#!/usr/bin/env python3
"""
Module de gestion de la base de données SQLite
Sauvegarde et récupération de l'historique des transcriptions
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager


class TranscriptionDatabase:
    """Gestionnaire de base de données pour les transcriptions"""

    def __init__(self, db_path="transcriptions.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialiser la base de données"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Table des transcriptions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    has_emergency BOOLEAN DEFAULT 0,
                    emergency_words TEXT,
                    audio_level INTEGER DEFAULT 0,
                    word_count INTEGER DEFAULT 0
                )
            """)

            # Table des statistiques de session
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    total_words INTEGER DEFAULT 0,
                    total_transcriptions INTEGER DEFAULT 0,
                    avg_audio_level REAL DEFAULT 0
                )
            """)

            # Index pour performances
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON transcriptions(timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_emergency
                ON transcriptions(has_emergency)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager pour connexion DB"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Accès par nom de colonne
        try:
            yield conn
        finally:
            conn.close()

    def add_transcription(self, text, has_emergency=False, emergency_words=None,
                          audio_level=0):
        """Ajouter une transcription"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            word_count = len(text.split()) if text else 0
            emergency_words_json = json.dumps(emergency_words) if emergency_words else None

            cursor.execute("""
                INSERT INTO transcriptions
                (text, has_emergency, emergency_words, audio_level, word_count)
                VALUES (?, ?, ?, ?, ?)
            """, (text, has_emergency, emergency_words_json, audio_level, word_count))

            conn.commit()
            return cursor.lastrowid

    def get_recent_transcriptions(self, limit=50):
        """Récupérer les transcriptions récentes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, text, timestamp, has_emergency, emergency_words, audio_level
                FROM transcriptions
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'text': row['text'],
                    'timestamp': row['timestamp'],
                    'has_emergency': bool(row['has_emergency']),
                    'emergency_words': json.loads(row['emergency_words']) if row['emergency_words'] else [],
                    'audio_level': row['audio_level']
                })

            return results

    def get_transcriptions_by_date(self, date=None):
        """Récupérer les transcriptions d'une date spécifique"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, text, timestamp, has_emergency, audio_level
                FROM transcriptions
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            """, (date,))

            return [dict(row) for row in cursor.fetchall()]

    def get_emergency_transcriptions(self, limit=20):
        """Récupérer les transcriptions marquées comme urgence"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, text, timestamp, emergency_words
                FROM transcriptions
                WHERE has_emergency = 1
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'text': row['text'],
                    'timestamp': row['timestamp'],
                    'emergency_words': json.loads(row['emergency_words']) if row['emergency_words'] else []
                })

            return results

    def get_statistics(self, days=7):
        """Obtenir des statistiques sur les derniers jours"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Stats globales
            cursor.execute("""
                SELECT
                    COUNT(*) as total_transcriptions,
                    SUM(word_count) as total_words,
                    AVG(audio_level) as avg_audio_level,
                    COUNT(CASE WHEN has_emergency = 1 THEN 1 END) as emergency_count
                FROM transcriptions
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
            """, (days,))

            row = cursor.fetchone()

            return {
                'total_transcriptions': row['total_transcriptions'] or 0,
                'total_words': row['total_words'] or 0,
                'avg_audio_level': round(row['avg_audio_level'] or 0, 2),
                'emergency_count': row['emergency_count'] or 0
            }

    def search_transcriptions(self, query, limit=50):
        """Rechercher dans les transcriptions"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, text, timestamp, has_emergency
                FROM transcriptions
                WHERE text LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f'%{query}%', limit))

            return [dict(row) for row in cursor.fetchall()]

    def delete_old_transcriptions(self, days=30):
        """Supprimer les transcriptions de plus de X jours"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM transcriptions
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            """, (days,))

            deleted_count = cursor.rowcount
            conn.commit()

            return deleted_count

    def export_to_text(self, output_file, date=None):
        """Exporter les transcriptions en fichier texte"""
        transcriptions = self.get_transcriptions_by_date(date) if date else self.get_recent_transcriptions(1000)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"Historique des transcriptions - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 80 + "\n\n")

            for trans in reversed(transcriptions):
                timestamp = trans.get('timestamp', '')
                text = trans.get('text', '')
                emergency = trans.get('has_emergency', False)

                f.write(f"[{timestamp}]")
                if emergency:
                    f.write(" ⚠️ URGENCE")
                f.write(f"\n{text}\n\n")

        return len(transcriptions)

    def get_total_count(self):
        """Obtenir le nombre total de transcriptions"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM transcriptions")
            row = cursor.fetchone()
            return row['count'] if row else 0


# Instance globale (singleton)
_db_instance = None


def get_database(db_path="transcriptions.db"):
    """Obtenir l'instance de la base de données"""
    global _db_instance
    if _db_instance is None:
        _db_instance = TranscriptionDatabase(db_path)
    return _db_instance
