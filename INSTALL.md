# 📦 Installation - Raspberry Pi 4

Guide d'installation complet pour Raspberry Pi 4.

## 🎯 Prérequis

### Matériel
- Raspberry Pi 4 (4GB RAM minimum)
- Carte SD 32GB classe 10
- Microphone USB
- Alimentation officielle 5V/3A

### Logiciel
- Raspberry Pi OS (32-bit ou 64-bit)
- Connexion internet (pour l'installation)

## 🚀 Installation Rapide (5 minutes)

```bash
# 1. Mise à jour système
sudo apt update && sudo apt upgrade -y

# 2. Installation dépendances
sudo apt install -y python3-pip python3-venv python3-dev \
    portaudio19-dev python3-pyaudio libportaudio2 \
    alsa-utils pulseaudio python3-tk git wget unzip

# 3. Copier le projet (adapter selon votre cas)
cd ~
# Option A: Git
git clone <VOTRE_REPO> speech_to_text
# Option B: USB
cp -r /mnt/usb/speech_to_text ~/
# Option C: SCP depuis PC
# scp -r /chemin/local/speech_to_text pi@IP_DU_PI:~/

cd ~/speech_to_text

# 4. Environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 5. Dépendances Python (5-10 min)
pip install --upgrade pip
pip install -r requirements.txt

# 6. Modèle Vosk (si pas déjà inclus)
./download_model.sh

# 7. Test
python3 app.py
# Ouvrir http://IP_DU_PI:5001 dans navigateur
```

## 🎤 Configuration Microphone

```bash
# Lister les micros disponibles
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Tester le micro
arecord -d 5 test.wav
aplay test.wav
```

Si le micro ne fonctionne pas :

```bash
sudo nano /etc/asound.conf
```

Ajouter (remplacer `X` par numéro de votre micro) :
```
pcm.!default {
    type hw
    card X
}
ctl.!default {
    type hw
    card X
}
```

## ⚙️ Démarrage Automatique

### Service systemd

```bash
# Copier le fichier service
sudo cp speech-to-text.service /etc/systemd/system/

# Vérifier les chemins
sudo nano /etc/systemd/system/speech-to-text.service

# Activer
sudo systemctl daemon-reload
sudo systemctl enable speech-to-text.service
sudo systemctl start speech-to-text.service

# Vérifier
sudo systemctl status speech-to-text.service
```

### Commandes utiles

```bash
# Voir logs en temps réel
journalctl -u speech-to-text.service -f

# Redémarrer
sudo systemctl restart speech-to-text.service

# Arrêter
sudo systemctl stop speech-to-text.service

# Désactiver auto-start
sudo systemctl disable speech-to-text.service
```

## 🔧 Optimisations (Optionnel)

### Réduire mémoire GPU
```bash
sudo raspi-config
# Performance Options > GPU Memory > 16 MB
# Redémarrer
```

### Overclock léger
```bash
sudo nano /boot/config.txt
# Ajouter :
over_voltage=2
arm_freq=1750
# Redémarrer
```

### Version Desktop au boot

Pour lancer app_desktop.py au démarrage :

```bash
# Modifier le service
sudo nano /etc/systemd/system/speech-to-text.service

# Changer ExecStart :
ExecStart=/home/pi/speech_to_text/venv/bin/python3 /home/pi/speech_to_text/app_desktop.py

# Ajouter si manquant :
Environment="DISPLAY=:0"

# Recharger
sudo systemctl daemon-reload
sudo systemctl restart speech-to-text.service
```

## 🐛 Dépannage

### Problème : App ne démarre pas
```bash
# Vérifier logs
journalctl -u speech-to-text.service -n 50

# Test manuel
cd ~/speech_to_text
source venv/bin/activate
python3 app.py
```

### Problème : ModuleNotFoundError
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Problème : Micro ne fonctionne pas
```bash
# Permissions
sudo usermod -a -G audio pi

# Redémarrer
sudo reboot
```

### Problème : App lente
```bash
# Vérifier température
vcgencmd measure_temp

# Si > 70°C, ajouter refroidissement

# Désactiver ponctuation et bruit
# Dans paramètres de l'interface
```

### Problème : Modèle manquant
```bash
cd ~/speech_to_text
./download_model.sh
# Ou télécharger manuellement
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip
unzip vosk-model-small-fr-0.22.zip
```

## 📊 Vérification Installation

### Checklist

- [ ] Python 3.7+ installé (`python3 --version`)
- [ ] Dépendances système installées
- [ ] Environnement virtuel créé et actif
- [ ] Dépendances Python installées
- [ ] Modèle Vosk téléchargé (40MB)
- [ ] Microphone détecté
- [ ] App démarre sans erreur
- [ ] Reconnaissance fonctionne
- [ ] Service systemd configuré (optionnel)

### Tests

```bash
# Test 1: Imports Python
python3 -c "import vosk, sounddevice, flask; print('OK')"

# Test 2: Modèle existe
ls models/vosk-model-small-fr-0.22/

# Test 3: Micro fonctionne
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Test 4: Lancer app
python3 app.py
# Vérifier http://IP_DU_PI:5001
```

## 🔄 Mise à Jour

Pour mettre à jour le code :

```bash
cd ~/speech_to_text

# Sauvegarder config
cp config.json config.json.backup
cp transcriptions.db transcriptions.db.backup

# Update code (si Git)
git pull

# Ou copier nouveaux fichiers
# scp -r ... pi@IP:~/speech_to_text/

# Update dépendances
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Redémarrer
sudo systemctl restart speech-to-text.service
```

## 💾 Sauvegarde

Fichiers à sauvegarder régulièrement :
- `config.json` - Configuration
- `transcriptions.db` - Historique

```bash
# Backup automatique quotidien
crontab -e
# Ajouter :
0 2 * * * cp ~/speech_to_text/transcriptions.db ~/speech_to_text/backup_$(date +\%Y\%m\%d).db
```

## 📡 Accès Réseau

Pour accéder depuis autres appareils :

1. Trouver IP du RPi : `hostname -I`
2. Ouvrir navigateur : `http://IP_DU_PI:5001`
3. **Autoriser dans pare-feu si nécessaire**

## ✅ Installation Terminée

Votre système est prêt ! L'application démarre automatiquement au boot et affiche les transcriptions en temps réel.

**Pour tester :** Parlez français → le texte apparaît !

---

**Questions ?** Voir [README.md](README.md) ou [QUICKSTART_V2.md](QUICKSTART_V2.md)
