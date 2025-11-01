#!/usr/bin/env python3
"""
Application Desktop pour la reconnaissance vocale locale avec Vosk
Version Tkinter - Plus performante que la version web
"""
import json
import os
import queue
import sounddevice as sd
import vosk
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from datetime import datetime

# Configuration
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
MODEL_PATH = "models/vosk-model-small-fr-0.22"
CONFIG_FILE = "config.json"

# Variables globales
model = None
audio_queue = queue.Queue()
is_recording = False
recognition_thread_obj = None


class SpeechToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcription Vocale")

        # Configuration par défaut
        self.config = {
            'font_size': 60,
            'theme': 'light',
            'auto_clear_delay': 30,
            'auto_scroll': True
        }
        self.load_config()

        # Variables
        self.auto_clear_timer = None
        self.current_theme = self.config['theme']

        # Couleurs pour les thèmes
        self.themes = {
            'light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'current_bg': '#f8f8f8',
                'history_bg': '#ffffff',
                'separator': '#e0e0e0',
                'settings_btn': '#888888'
            },
            'dark': {
                'bg': '#1a1a1a',
                'fg': '#e0e0e0',
                'current_bg': '#252525',
                'history_bg': '#1a1a1a',
                'separator': '#333333',
                'settings_btn': '#666666'
            }
        }

        self.setup_ui()
        self.apply_theme()

        # Démarrer la reconnaissance automatiquement
        self.root.after(1000, self.start_recording)

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Plein écran
        self.root.attributes('-fullscreen', True)

        # Frame principale
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

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

        # Bind pour quitter en plein écran (Escape)
        self.root.bind('<Escape>', lambda e: self.toggle_fullscreen())

    def show_settings(self):
        """Affiche la fenêtre de paramètres"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Paramètres")
        settings_window.geometry("500x500")
        settings_window.resizable(False, False)

        # Centrer la fenêtre
        settings_window.transient(self.root)
        settings_window.grab_set()

        frame = tk.Frame(settings_window, padx=30, pady=30)
        frame.pack(fill=tk.BOTH, expand=True)

        # Titre
        title = tk.Label(frame, text="Paramètres", font=('Arial', 20))
        title.pack(pady=(0, 20))

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

        # Effacement automatique
        tk.Label(frame, text="Effacement automatique:", font=('Arial', 12)).pack(anchor='w', pady=(10, 5))

        auto_clear_var = tk.StringVar(value=str(self.config['auto_clear_delay']))
        auto_clear_combo = ttk.Combobox(
            frame,
            textvariable=auto_clear_var,
            values=['0', '30', '60', '120'],
            state='readonly',
            font=('Arial', 11)
        )
        auto_clear_combo.pack(fill=tk.X, pady=(0, 10))

        # Mapping des valeurs pour affichage
        delay_labels = {'0': 'Désactivé', '30': '30 secondes', '60': '1 minute', '120': '2 minutes'}

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

        # Bouton effacer
        clear_btn = tk.Button(
            frame,
            text="🗑️ Effacer maintenant",
            font=('Arial', 12),
            command=lambda: [self.clear_history(), settings_window.destroy()],
            cursor='hand2'
        )
        clear_btn.pack(fill=tk.X, pady=(20, 10))

        # Bouton fermer
        close_btn = tk.Button(
            frame,
            text="Fermer",
            font=('Arial', 12),
            command=lambda: [self.save_config(), settings_window.destroy()],
            cursor='hand2'
        )
        close_btn.pack(fill=tk.X, pady=(10, 0))

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

    def apply_font_size(self):
        """Appliquer la taille de police"""
        self.current_text.config(font=('Arial', self.config['font_size']))
        self.history_text.config(font=('Arial', int(self.config['font_size'] * 0.8)))

    def toggle_fullscreen(self):
        """Basculer le mode plein écran"""
        current = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current)

    def add_to_history(self, text):
        """Ajouter une transcription à l'historique"""
        timestamp = datetime.now().strftime("%H:%M")

        self.history_text.config(state=tk.NORMAL)
        self.history_text.insert('1.0', f"{text} [{timestamp}]\n\n")
        self.history_text.config(state=tk.DISABLED)

        # Défilement automatique vers le haut
        if self.config['auto_scroll']:
            self.history_text.see('1.0')

        # Réinitialiser le timer d'effacement automatique
        self.reset_auto_clear_timer()

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
            print("Reconnaissance vocale démarrée")

    def stop_recording(self):
        """Arrêter la reconnaissance vocale"""
        global is_recording
        is_recording = False

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
    audio_queue.put(bytes(indata))


def recognition_loop(app):
    """Boucle de reconnaissance vocale"""
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
        print("Écoute en cours...")

        while is_recording:
            try:
                data = audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get('text'):
                    # Texte final
                    app.root.after(0, app.add_to_history, result['text'])
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
    print("Modèle chargé avec succès!")
    return True


def main():
    """Point d'entrée principal"""
    print("=== Application Speech-to-Text Desktop ===")

    if not load_model():
        print("\nImpossible de démarrer sans le modèle Vosk")
        return

    root = tk.Tk()
    app = SpeechToTextApp(root)

    # Gérer la fermeture proprement
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    print("\nApplication démarrée!")
    print("Appuyez sur Échap pour quitter le plein écran")

    root.mainloop()


if __name__ == '__main__':
    main()
