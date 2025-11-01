# Installation sur Raspberry Pi - Guide Rapide

Guide ultra-simplifié pour installer l'application Speech-to-Text Desktop sur votre Raspberry Pi.

## Prérequis

- Raspberry Pi 4 (4GB) ou Raspberry Pi 5
- Carte SD avec Raspberry Pi OS installé
- Microphone USB (ex: Logitech C920)
- Connexion internet (pour l'installation uniquement)

## Installation en 5 étapes

### 1️⃣ Installer les dépendances

Ouvrez un terminal et copiez-collez ces commandes :

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-tk portaudio19-dev git unzip wget
```

⏱️ Temps estimé : 3-5 minutes

### 2️⃣ Télécharger l'application

```bash
cd ~
git clone <URL_DU_REPO> speech_to_text
cd speech_to_text
```

Si vous avez copié les fichiers manuellement (clé USB), remplacez par :

```bash
cd ~/speech_to_text
```

### 3️⃣ Installer l'environnement Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

⏱️ Temps estimé : 5-10 minutes

### 4️⃣ Télécharger le modèle de reconnaissance vocale

```bash
chmod +x download_model.sh
./download_model.sh
```

⏱️ Temps estimé : 1-2 minutes (télécharge ~40 MB)

### 5️⃣ Lancer l'application

```bash
chmod +x start_desktop.sh
./start_desktop.sh
```

**L'application devrait s'ouvrir en plein écran !** 🎉

## Configuration du microphone

Si le micro ne fonctionne pas :

```bash
# Lister les micros disponibles
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Tester l'enregistrement
arecord -d 3 test.wav && aplay test.wav
```

Si votre Logitech C920 n'est pas détectée, débranchez-la et rebranchez-la.

## Démarrage automatique

Pour que l'application démarre au boot du Raspberry Pi :

```bash
# Copier le service
sudo cp speech-to-text-desktop.service /etc/systemd/system/

# Activer
sudo systemctl enable speech-to-text-desktop.service
sudo systemctl start speech-to-text-desktop.service
```

Redémarrez le Raspberry Pi pour tester :

```bash
sudo reboot
```

## Utilisation

Une fois lancée :

- L'application écoute automatiquement
- Le texte apparaît en temps réel
- Cliquez sur **⋮** (en haut à droite) pour les paramètres
- Appuyez sur **Échap** pour quitter le plein écran

## Résolution de problèmes

### L'application ne démarre pas

```bash
cd ~/speech_to_text
source venv/bin/activate
python3 app_desktop.py
```

Regardez les messages d'erreur affichés.

### Erreur "Model not found"

Le modèle Vosk n'a pas été téléchargé :

```bash
cd ~/speech_to_text
./download_model.sh
```

### Le micro ne capte rien

Vérifiez le niveau du micro :

```bash
alsamixer
```

Utilisez les flèches pour naviguer et augmenter le volume du micro USB.

### L'application est trop lente

- Vérifiez la température : `vcgencmd measure_temp`
- Fermez les autres applications
- Si > 70°C, ajoutez un ventilateur

## Aide complète

Pour plus de détails, consultez :

- **README_DESKTOP.md** - Documentation complète de l'application desktop
- **GUIDE_MAMIE.md** - Guide pour expliquer à votre grand-mère
- **README.md** - Documentation générale du projet

## Récapitulatif des commandes

```bash
# Installation complète
sudo apt-get update && sudo apt-get install -y python3-pip python3-venv python3-tk portaudio19-dev git unzip wget
cd ~/speech_to_text
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./download_model.sh

# Lancement
./start_desktop.sh

# Démarrage automatique
sudo cp speech-to-text-desktop.service /etc/systemd/system/
sudo systemctl enable speech-to-text-desktop.service
sudo systemctl start speech-to-text-desktop.service
```

---

**Installation terminée ! Votre grand-mère peut maintenant suivre les conversations. ❤️**
