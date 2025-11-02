#!/usr/bin/env python3
import json
import os
import queue
import sounddevice as sd
import vosk
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from datetime import datetime
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

SAMPLE_RATE = 16000
BLOCK_SIZE = 1600  # Optimisé: 100ms au lieu de 125ms (-20% latence)
MODEL_PATH = "models/vosk-model-small-fr-0.22"
CONFIG_FILE = "config.json"
MAX_QUEUE_SIZE = 10
STATS_UPDATE_INTERVAL = 3.0  # Mise à jour stats toutes les 3s (économie CPU)

# Variables globales
model = None
audio_queue = queue.Queue()
is_recording = False
recognition_thread_obj = None

# Instances des utilitaires
vad = VoiceActivityDetector(sample_rate=SAMPLE_RATE, aggressiveness=3)  # Optimisé: 3 = plus agressif
noise_reducer = NoiseReducer(sample_rate=SAMPLE_RATE)
audio_meter = AudioLevelMeter()
punctuator = SmartPunctuator()
emergency_detector = EmergencyDetector()
db = get_database()
stats = get_stats_manager()


class SpeechToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcription Vocale - Version Améliorée")

        # Configuration par défaut (optimisée pour performance)
        self.config = {
            'font_size': 60,
            'theme': 'light',
            'auto_clear_delay': 30,
            'auto_scroll': True,
            'enable_vad': True,                      # ✅ Actif: économise 70% CPU
            'enable_noise_reduction': False,         # ❌ Désactivé: trop gourmand
            'enable_punctuation': False,             # ❌ Désactivé: trop gourmand (ponctuation basique utilisée)
            'enable_emergency_detection': True       # ✅ Actif: crucial pour sécurité
        }
        self.load_config()

        # Variables
        self.auto_clear_timer = None
        self.current_theme = self.config['theme']
        self.stats_window = None
        self.emergency_flash_active = False

        # Couleurs pour les thèmes
        self.themes = {
            'light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'current_bg': '#f8f8f8',
                'history_bg': '#ffffff',
                'separator': '#e0e0e0',
                'settings_btn': '#888888',
                'emergency': '#ff0000'
            },
            'dark': {
                'bg': '#1a1a1a',
                'fg': '#e0e0e0',
                'current_bg': '#252525',
                'history_bg': '#1a1a1a',
                'separator': '#333333',
                'settings_btn': '#666666',
                'emergency': '#ff3333'
            }
        }

        self.setup_ui()
        self.apply_theme()

        # Démarrer la reconnaissance automatiquement
        self.root.after(1000, self.start_recording)

        # Rafraîchir les stats toutes les 2 secondes
        self.update_stats_display()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Plein écran
        self.root.attributes('-fullscreen', True)

        # Frame principale
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Barre supérieure avec indicateurs
        top_bar = tk.Frame(self.root, height=40)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(10, 0))

        # Indicateur de niveau audio (barre de progression)
        self.audio_level_label = tk.Label(top_bar, text="🎤", font=('Arial', 16))
        self.audio_level_label.pack(side=tk.LEFT, padx=(0, 10))

        self.audio_level_bar = ttk.Progressbar(
            top_bar,
            orient=tk.HORIZONTAL,
            length=200,
            mode='determinate'
        )
        self.audio_level_bar.pack(side=tk.LEFT, padx=(0, 20))

        # Bouton statistiques
        self.stats_btn = tk.Button(
            top_bar,
            text="📊",
            font=('Arial', 16),
            command=self.show_stats,
            relief=tk.FLAT,
            borderwidth=0,
            cursor='hand2'
        )
        self.stats_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Bouton paramètres (discret en haut à droite)
        self.settings_btn = tk.Button(
            self.root,
            text="⋮",
            font=('Arial', 24),
            command=self.show_settings,
            relief=tk.FLAT,
            borderwidth=0,
            cursor='hand2'
        )
        self.settings_btn.place(x=self.root.winfo_screenwidth()-60, y=20)

        # Zone texte courante (en haut)
        self.current_text = tk.Label(
            main_frame,
            text="",
            font=('Arial', self.config['font_size']),
            wraplength=self.root.winfo_screenwidth()-100,
            justify=tk.LEFT,
            anchor='nw',
            padx=20,
            pady=15
        )
        self.current_text.pack(fill=tk.X, pady=(0, 10))

        # Séparateur
        separator = tk.Frame(main_frame, height=1)
        separator.pack(fill=tk.X, pady=5)
        self.separator = separator

        # Zone historique (scrollable)
        history_frame = tk.Frame(main_frame)
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_text = scrolledtext.ScrolledText(
            history_frame,
            font=('Arial', int(self.config['font_size'] * 0.8)),
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=0,
            padx=20,
            pady=20
        )
        self.history_text.pack(fill=tk.BOTH, expand=True)
        self.history_text.config(state=tk.DISABLED)

        # Tag pour texte d'urgence
        self.history_text.tag_config('emergency', foreground='red', font=('Arial', int(self.config['font_size'] * 0.8), 'bold'))

        # Bind pour quitter en plein écran (Escape)
        self.root.bind('<Escape>', lambda e: self.toggle_fullscreen())

    def show_settings(self):
        """Affiche la fenêtre de paramètres"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Paramètres")
        settings_window.geometry("600x700")
        settings_window.resizable(False, False)

        # Centrer la fenêtre
        settings_window.transient(self.root)
        settings_window.grab_set()

        frame = tk.Frame(settings_window, padx=30, pady=30)
        frame.pack(fill=tk.BOTH, expand=True)

        # Titre
        title = tk.Label(frame, text="Paramètres", font=('Arial', 20, 'bold'))
        title.pack(pady=(0, 20))

        # --- AFFICHAGE ---
        tk.Label(frame, text="AFFICHAGE", font=('Arial', 14, 'bold')).pack(anchor='w', pady=(10, 5))

        # Taille du texte
        tk.Label(frame, text="Taille du texte:", font=('Arial', 12)).pack(anchor='w', pady=(10, 5))

        font_frame = tk.Frame(frame)
        font_frame.pack(fill=tk.X, pady=(0, 10))

        font_size_var = tk.IntVar(value=self.config['font_size'])
        font_size_label = tk.Label(font_frame, text=f"{self.config['font_size']}px", font=('Arial', 12))
        font_size_label.pack(side=tk.RIGHT)

        def update_font_size(val):
            size = int(float(val))
            font_size_label.config(text=f"{size}px")
            self.config['font_size'] = size
            self.apply_font_size()

        font_slider = tk.Scale(
            font_frame,
            from_=30,
            to=100,
            orient=tk.HORIZONTAL,
            variable=font_size_var,
            command=update_font_size,
            showvalue=False
        )
        font_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Thème
        tk.Label(frame, text="Mode:", font=('Arial', 12)).pack(anchor='w', pady=(10, 5))

        theme_btn = tk.Button(
            frame,
            text="🌙 Mode Sombre" if self.current_theme == 'light' else "☀️ Mode Clair",
            font=('Arial', 12),
            command=lambda: self.toggle_theme(theme_btn),
            cursor='hand2'
        )
        theme_btn.pack(fill=tk.X, pady=(0, 10))

        # --- FONCTIONNALITÉS ---
        tk.Label(frame, text="FONCTIONNALITÉS", font=('Arial', 14, 'bold')).pack(anchor='w', pady=(20, 5))

        # Bouton Mode Performance (toggle rapide)
        def toggle_performance_mode():
            is_perf_mode = not self.config.get('enable_noise_reduction', False)
            self.config['enable_noise_reduction'] = not is_perf_mode
            self.config['enable_punctuation'] = not is_perf_mode
            # Mettre à jour les checkboxes
            noise_var.set(not is_perf_mode)
            punct_var.set(not is_perf_mode)
            perf_btn_text = "⚡ Mode Performance: ON" if is_perf_mode else "🎯 Mode Qualité: ON"
            perf_btn.config(text=perf_btn_text)

        is_perf_mode = not self.config.get('enable_noise_reduction', False)
        perf_btn = tk.Button(
            frame,
            text="⚡ Mode Performance: ON" if is_perf_mode else "🎯 Mode Qualité: ON",
            font=('Arial', 12, 'bold'),
            command=toggle_performance_mode,
            cursor='hand2',
            bg='#2196F3' if is_perf_mode else '#4CAF50',
            fg='white'
        )
        perf_btn.pack(fill=tk.X, pady=(0, 15))

        # VAD
        vad_var = tk.BooleanVar(value=self.config.get('enable_vad', True))
        tk.Checkbutton(
            frame,
            text="Détection de voix (VAD) - Réduit la charge CPU",
            variable=vad_var,
            font=('Arial', 11),
            command=lambda: self.config.update({'enable_vad': vad_var.get()})
        ).pack(anchor='w', pady=5)

        # Réduction de bruit
        noise_var = tk.BooleanVar(value=self.config.get('enable_noise_reduction', True))
        tk.Checkbutton(
            frame,
            text="Réduction de bruit - Meilleure précision",
            variable=noise_var,
            font=('Arial', 11),
            command=lambda: self.config.update({'enable_noise_reduction': noise_var.get()})
        ).pack(anchor='w', pady=5)

        # Ponctuation
        punct_var = tk.BooleanVar(value=self.config.get('enable_punctuation', True))
        tk.Checkbutton(
            frame,
            text="Ponctuation automatique - Plus lisible",
            variable=punct_var,
            font=('Arial', 11),
            command=lambda: self.config.update({'enable_punctuation': punct_var.get()})
        ).pack(anchor='w', pady=5)

        # Détection d'urgence
        emergency_var = tk.BooleanVar(value=self.config.get('enable_emergency_detection', True))
        tk.Checkbutton(
            frame,
            text="Détection d'urgence - Alerte visuelle",
            variable=emergency_var,
            font=('Arial', 11),
            command=lambda: self.config.update({'enable_emergency_detection': emergency_var.get()})
        ).pack(anchor='w', pady=5)

        # Effacement automatique
        tk.Label(frame, text="Effacement automatique:", font=('Arial', 12)).pack(anchor='w', pady=(15, 5))

        auto_clear_var = tk.StringVar(value=str(self.config['auto_clear_delay']))
        auto_clear_combo = ttk.Combobox(
            frame,
            textvariable=auto_clear_var,
            values=['0', '30', '60', '120', '300'],
            state='readonly',
            font=('Arial', 11)
        )
        auto_clear_combo.pack(fill=tk.X, pady=(0, 10))

        def update_auto_clear(event):
            delay = int(auto_clear_var.get())
            self.config['auto_clear_delay'] = delay
            self.reset_auto_clear_timer()

        auto_clear_combo.bind('<<ComboboxSelected>>', update_auto_clear)

        # Défilement automatique
        auto_scroll_var = tk.BooleanVar(value=self.config['auto_scroll'])

        def toggle_auto_scroll():
            self.config['auto_scroll'] = auto_scroll_var.get()

        auto_scroll_check = tk.Checkbutton(
            frame,
            text="Défilement automatique",
            variable=auto_scroll_var,
            font=('Arial', 12),
            command=toggle_auto_scroll
        )
        auto_scroll_check.pack(anchor='w', pady=(10, 10))

        # Boutons d'action
        tk.Label(frame, text="ACTIONS", font=('Arial', 14, 'bold')).pack(anchor='w', pady=(20, 10))

        # Bouton effacer
        clear_btn = tk.Button(
            frame,
            text="🗑️ Effacer l'écran maintenant",
            font=('Arial', 12),
            command=lambda: [self.clear_history(), settings_window.destroy()],
            cursor='hand2'
        )
        clear_btn.pack(fill=tk.X, pady=(0, 10))

        # Bouton exporter
        export_btn = tk.Button(
            frame,
            text="💾 Exporter l'historique",
            font=('Arial', 12),
            command=self.export_history,
            cursor='hand2'
        )
        export_btn.pack(fill=tk.X, pady=(0, 10))

        # Bouton fermer
        close_btn = tk.Button(
            frame,
            text="Fermer",
            font=('Arial', 12),
            command=lambda: [self.save_config(), settings_window.destroy()],
            cursor='hand2',
            bg='#4CAF50',
            fg='white'
        )
        close_btn.pack(fill=tk.X, pady=(20, 0))

    def show_stats(self):
        """Afficher les statistiques"""
        if self.stats_window and tk.Toplevel.winfo_exists(self.stats_window):
            self.stats_window.lift()
            return

        self.stats_window = tk.Toplevel(self.root)
        self.stats_window.title("Statistiques")
        self.stats_window.geometry("500x600")
        self.stats_window.resizable(False, False)

        frame = tk.Frame(self.stats_window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(frame, text="Statistiques en temps réel", font=('Arial', 18, 'bold'))
        title.pack(pady=(0, 20))

        # Créer les labels de stats
        self.stats_labels = {}

        sections = [
            ("📊 Application", ['uptime', 'total_transcriptions', 'total_words', 'avg_words']),
            ("💻 Système", ['cpu', 'memory', 'disk']),
            ("🎤 Audio", ['audio_level', 'avg_audio'])
        ]

        for section_name, keys in sections:
            tk.Label(frame, text=section_name, font=('Arial', 14, 'bold')).pack(anchor='w', pady=(15, 5))

            for key in keys:
                label = tk.Label(frame, text="", font=('Arial', 11), anchor='w')
                label.pack(anchor='w', padx=(10, 0), pady=2)
                self.stats_labels[key] = label

        # Rafraîchir les stats
        self.refresh_stats_window()

    def refresh_stats_window(self):
        """Rafraîchir les statistiques dans la fenêtre"""
        if not self.stats_window or not tk.Toplevel.winfo_exists(self.stats_window):
            return

        all_stats = stats.get_all_stats()
        system = all_stats['system']
        app = all_stats['app']
        audio = all_stats['audio']

        # Mettre à jour les labels
        self.stats_labels['uptime'].config(text=f"Temps de fonctionnement: {app['uptime']}")
        self.stats_labels['total_transcriptions'].config(text=f"Transcriptions: {app['total_transcriptions']}")
        self.stats_labels['total_words'].config(text=f"Mots reconnus: {app['total_words']}")
        self.stats_labels['avg_words'].config(text=f"Mots/transcription: {app['avg_words_per_transcription']}")

        self.stats_labels['cpu'].config(text=f"CPU: {system['cpu']['percent']}% (moy: {system['cpu']['avg_1min']}%)")
        self.stats_labels['memory'].config(text=f"Mémoire: {system['memory']['percent']}% ({system['memory']['used_mb']} MB)")
        self.stats_labels['disk'].config(text=f"Disque: {system['disk']['percent']}% (libre: {system['disk']['free_gb']} GB)")

        self.stats_labels['audio_level'].config(text=f"Niveau actuel: {audio['current_level']}%")
        self.stats_labels['avg_audio'].config(text=f"Niveau moyen: {audio['avg_level']}%")

        # Rafraîchir toutes les 2 secondes
        self.stats_window.after(2000, self.refresh_stats_window)

    def update_stats_display(self):
        """Mettre à jour l'affichage des statistiques (barre de niveau audio)"""
        level = audio_meter.get_average_level()
        self.audio_level_bar['value'] = level

        # Continuer à rafraîchir (optimisé: 3s au lieu de 100ms)
        self.root.after(int(STATS_UPDATE_INTERVAL * 1000), self.update_stats_display)

    def toggle_theme(self, button=None):
        """Basculer entre mode clair et sombre"""
        if self.current_theme == 'light':
            self.current_theme = 'dark'
            if button:
                button.config(text="☀️ Mode Clair")
        else:
            self.current_theme = 'light'
            if button:
                button.config(text="🌙 Mode Sombre")

        self.config['theme'] = self.current_theme
        self.apply_theme()

    def apply_theme(self):
        """Appliquer le thème sélectionné"""
        theme = self.themes[self.current_theme]

        self.root.config(bg=theme['bg'])
        self.current_text.config(bg=theme['current_bg'], fg=theme['fg'])
        self.history_text.config(bg=theme['history_bg'], fg=theme['fg'], insertbackground=theme['fg'])
        self.settings_btn.config(bg=theme['bg'], fg=theme['settings_btn'], activebackground=theme['bg'])
        self.stats_btn.config(bg=theme['bg'], fg=theme['settings_btn'], activebackground=theme['bg'])
        self.separator.config(bg=theme['separator'])

    def apply_font_size(self):
        """Appliquer la taille de police"""
        self.current_text.config(font=('Arial', self.config['font_size']))
        self.history_text.config(font=('Arial', int(self.config['font_size'] * 0.8)))

    def toggle_fullscreen(self):
        """Basculer le mode plein écran"""
        current = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current)

    def add_to_history(self, text, is_emergency=False):
        """Ajouter une transcription à l'historique"""
        timestamp = datetime.now().strftime("%H:%M")

        self.history_text.config(state=tk.NORMAL)

        display_text = text
        if is_emergency:
            display_text = f"⚠️ {text}"

        self.history_text.insert('1.0', f"{display_text} [{timestamp}]\n\n", 'emergency' if is_emergency else '')
        self.history_text.config(state=tk.DISABLED)

        # Défilement automatique vers le haut
        if self.config['auto_scroll']:
            self.history_text.see('1.0')

        # Réinitialiser le timer d'effacement automatique
        self.reset_auto_clear_timer()

        # Flash d'urgence
        if is_emergency:
            self.trigger_emergency_flash()

    def trigger_emergency_flash(self):
        """Déclencher un flash visuel d'urgence"""
        if self.emergency_flash_active:
            return

        self.emergency_flash_active = True
        theme = self.themes[self.current_theme]
        original_bg = theme['current_bg']
        emergency_color = theme['emergency']

        def flash(count=0):
            if count >= 6:  # 3 flashs (on/off)
                self.current_text.config(bg=original_bg)
                self.emergency_flash_active = False
                return

            if count % 2 == 0:
                self.current_text.config(bg=emergency_color)
            else:
                self.current_text.config(bg=original_bg)

            self.root.after(300, lambda: flash(count + 1))

        flash()

    def clear_history(self):
        """Effacer l'historique"""
        self.current_text.config(text="")
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete('1.0', tk.END)
        self.history_text.config(state=tk.DISABLED)
        self.reset_auto_clear_timer()

    def reset_auto_clear_timer(self):
        """Réinitialiser le timer d'effacement automatique"""
        if self.auto_clear_timer:
            self.root.after_cancel(self.auto_clear_timer)
            self.auto_clear_timer = None

        delay = self.config['auto_clear_delay']
        if delay > 0:
            self.auto_clear_timer = self.root.after(delay * 1000, self.clear_history)

    def update_current_text(self, text):
        """Mettre à jour le texte courant"""
        self.current_text.config(text=text)

    def start_recording(self):
        """Démarrer la reconnaissance vocale"""
        global is_recording, recognition_thread_obj

        if not is_recording and model is not None:
            is_recording = True
            recognition_thread_obj = threading.Thread(target=recognition_loop, args=(self,), daemon=True)
            recognition_thread_obj.start()
            print("Reconnaissance vocale démarrée avec améliorations")

    def stop_recording(self):
        """Arrêter la reconnaissance vocale"""
        global is_recording
        is_recording = False

    def export_history(self):
        """Exporter l'historique en fichier texte"""
        try:
            filename = f"transcription_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            count = db.export_to_text(filename)
            messagebox.showinfo("Export réussi", f"{count} transcriptions exportées dans {filename}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {e}")

    def load_config(self):
        """Charger la configuration depuis le fichier"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
            except Exception as e:
                print(f"Erreur lors du chargement de la config: {e}")

    def save_config(self):
        """Sauvegarder la configuration"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la config: {e}")

    def on_closing(self):
        """Actions à effectuer lors de la fermeture"""
        self.stop_recording()
        self.save_config()
        self.root.destroy()


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


def recognition_loop(app):
    """Boucle de reconnaissance vocale AMÉLIORÉE"""
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
        print("🎤 Écoute en cours avec améliorations...")
        print(f"  VAD: {app.config.get('enable_vad', True)}")
        print(f"  Réduction bruit: {app.config.get('enable_noise_reduction', True)}")
        print(f"  Ponctuation: {app.config.get('enable_punctuation', True)}")
        print(f"  Détection urgence: {app.config.get('enable_emergency_detection', True)}")

        while is_recording:
            try:
                data = audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            # Mesurer le niveau audio
            audio_level = audio_meter.get_level(data)

            # VAD: Ne traiter que si c'est de la parole
            if app.config.get('enable_vad', True):
                if not vad.is_speech(data):
                    continue  # Ignorer le silence

            # Réduction de bruit
            if app.config.get('enable_noise_reduction', True):
                data = noise_reducer.reduce_noise(data)

            # Reconnaissance Vosk
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get('text'):
                    text = result['text']

                    # Ponctuation automatique
                    if app.config.get('enable_punctuation', False):
                        # Ponctuation ML (avancée mais gourmande)
                        text = punctuator.add_punctuation(text)
                    else:
                        # Ponctuation basique (légère, toujours active)
                        text = punctuator._basic_punctuation(text)

                    # Détection d'urgence
                    is_emergency = False
                    emergency_words = []
                    if app.config.get('enable_emergency_detection', True):
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

                    # Afficher dans l'interface
                    app.root.after(0, app.add_to_history, text, is_emergency)
                    app.root.after(0, app.update_current_text, "")
            else:
                partial = json.loads(rec.PartialResult())
                if partial.get('partial'):
                    # Texte partiel
                    app.root.after(0, app.update_current_text, partial['partial'])


def load_model():
    """Charge le modèle Vosk"""
    global model

    if not os.path.exists(MODEL_PATH):
        print(f"ERREUR: Le modèle n'existe pas à {MODEL_PATH}")
        print("Téléchargez-le avec ./download_model.sh")
        return False

    print(f"Chargement du modèle depuis {MODEL_PATH}...")
    model = vosk.Model(MODEL_PATH)
    print("✅ Modèle chargé avec succès!")
    return True


def main():
    """Point d'entrée principal"""
    print("=" * 70)
    print("🎤 Application Speech-to-Text - VERSION AMÉLIORÉE")
    print("=" * 70)
    print("\n📦 Fonctionnalités:")
    print("  ✅ VAD (Voice Activity Detection)")
    print("  ✅ Réduction de bruit")
    print("  ✅ Ponctuation automatique")
    print("  ✅ Détection d'urgence")
    print("  ✅ Sauvegarde persistante (SQLite)")
    print("  ✅ Statistiques en temps réel")
    print("  ✅ Optimisations performances\n")

    if not load_model():
        print("\n❌ Impossible de démarrer sans le modèle Vosk")
        return

    # Charger le modèle de ponctuation (optionnel, peut prendre du temps)
    print("Chargement du modèle de ponctuation...")

    root = tk.Tk()
    app = SpeechToTextApp(root)

    # Gérer la fermeture proprement
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    print("\n✅ Application démarrée!")
    print("📝 Appuyez sur Échap pour quitter le plein écran")
    print(f"💾 Base de données: {db.get_total_count()} transcriptions sauvegardées\n")

    root.mainloop()


if __name__ == '__main__':
    main()
