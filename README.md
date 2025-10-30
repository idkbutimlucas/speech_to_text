# Application Speech-to-Text Locale

Application de transcription vocale en temps réel pour personnes malentendantes, optimisée pour Raspberry Pi. Tout fonctionne en local, sans nécessiter de connexion internet ou de services cloud.

## Caractéristiques

- ✅ **100% Local** - Aucune donnée envoyée sur internet
- ✅ **Temps réel** - Affichage instantané de la transcription
- ✅ **Interface accessible** - Grandes polices, mode sombre/clair
- ✅ **Reconnaissance en français** - Utilise Vosk avec modèle français
- ✅ **Léger** - Fonctionne sur Raspberry Pi 4
- ✅ **Gratuit** - Aucun frais d'abonnement

## Prérequis matériels

### Pour Raspberry Pi (recommandé)

- **Raspberry Pi 4** avec 4GB RAM minimum (ou Raspberry Pi 5)
- Carte SD de 16GB minimum
- Microphone USB de bonne qualité (omnidirectionnel recommandé)
- Écran tactile 7-10 pouces ou moniteur HDMI
- Alimentation officielle Raspberry Pi

### Microphones recommandés (20-50€)

- Blue Yeti Nano
- Rode NT-USB Mini
- Samson Meteor Mic
- Tout microphone USB avec bonne captation omnidirectionnelle

## Installation sur Raspberry Pi

### 1. Préparer le Raspberry Pi

```bash
# Mettre à jour le système
sudo apt-get update
sudo apt-get upgrade -y

# Installer les dépendances système
sudo apt-get install -y python3-pip python3-venv portaudio19-dev git unzip wget
```

### 2. Cloner et installer l'application

```bash
# Aller dans le dossier personnel
cd ~

# Cloner le projet (ou le copier)
git clone <URL_DU_REPO> speech_to_text
cd speech_to_text

# Créer un environnement virtuel Python
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances Python
pip install -r requirements.txt
```

### 3. Télécharger le modèle Vosk français

```bash
# Rendre le script exécutable
chmod +x download_model.sh

# Télécharger le modèle (environ 40 MB)
./download_model.sh
```

Le script va télécharger et décompresser automatiquement le modèle Vosk français.

### 4. Configurer le microphone

```bash
# Lister les microphones disponibles
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

Si votre microphone USB n'est pas reconnu par défaut, vous pouvez le définir dans le fichier `app.py` en modifiant la ligne avec `sd.RawInputStream`.

### 5. Test de l'application

```bash
# Activer l'environnement virtuel si ce n'est pas déjà fait
source venv/bin/activate

# Lancer l'application
python3 app.py
```

L'application devrait démarrer sur `http://localhost:5000`. Ouvrez cette adresse dans Chromium (le navigateur du Raspberry Pi).

### 6. Configuration du démarrage automatique

Pour que l'application démarre automatiquement au boot :

```bash
# Copier le fichier de service
sudo cp speech-to-text.service /etc/systemd/system/

# Éditer le fichier si nécessaire (vérifier les chemins)
sudo nano /etc/systemd/system/speech-to-text.service

# Activer le service
sudo systemctl enable speech-to-text.service
sudo systemctl start speech-to-text.service

# Vérifier le statut
sudo systemctl status speech-to-text.service
```

### 7. Configuration du navigateur en mode kiosque

Pour que le navigateur s'ouvre en plein écran au démarrage :

```bash
# Éditer le fichier d'autostart
nano ~/.config/lxsession/LXDE-pi/autostart
```

Ajouter ces lignes :

```
@chromium-browser --kiosk --app=http://localhost:5000
@xset s off
@xset -dpms
@xset s noblank
```

## Utilisation

### Interface

1. **Bouton Démarrer (▶️)** - Commence la reconnaissance vocale
2. **Bouton Arrêter (⏹️)** - Arrête la reconnaissance
3. **Bouton Effacer (🗑️)** - Efface l'historique
4. **Bouton Paramètres (⚙️)** - Ouvre les options

### Paramètres disponibles

- **Taille du texte** - Ajustable de 20px à 80px
- **Mode sombre/clair** - Pour différents éclairages
- **Défilement automatique** - Active/désactive le scroll automatique

### Raccourcis clavier

- `Ctrl + Espace` - Démarrer/arrêter l'écoute
- `Ctrl + Shift + C` - Effacer l'historique

## Optimisations pour grand-mère

### Conseils d'utilisation

1. **Positionnement du microphone**
   - Placer le micro à 30-50 cm de la zone de conversation
   - Éviter les sources de bruit (TV, ventilateur)
   - Position centrale dans la pièce

2. **Configuration de l'écran**
   - Luminosité adaptée à l'éclairage ambiant
   - Distance de lecture confortable (50-80 cm)
   - Angle d'écran ajustable

3. **Simplification maximale**
   - Laisser tourner en permanence (pas besoin d'éteindre)
   - Un seul bouton visible pour démarrer/arrêter
   - Taille de texte pré-configurée

4. **Maintenance**
   - L'application redémarre automatiquement en cas d'erreur
   - Aucune maintenance régulière nécessaire
   - Mise à jour possible à distance (SSH)

## Améliorations possibles

### Court terme

- [ ] Historique sauvegardé entre les sessions
- [ ] Bouton d'urgence plus visible
- [ ] Mode "toujours écouter" avec détection de voix

### Moyen terme

- [ ] Reconnaissance de plusieurs locuteurs
- [ ] Filtrage du bruit amélioré
- [ ] Export de l'historique en PDF
- [ ] Application mobile pour consulter à distance

### Long terme

- [ ] Intégration avec système domotique
- [ ] Sous-titres pour la TV
- [ ] Alertes visuelles pour sonnette/téléphone

## Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u speech-to-text.service -f

# Tester manuellement
cd ~/speech_to_text
source venv/bin/activate
python3 app.py
```

### Le microphone ne fonctionne pas

```bash
# Lister les périphériques audio
arecord -l

# Tester l'enregistrement
arecord -d 5 test.wav
aplay test.wav
```

### La reconnaissance est de mauvaise qualité

- Vérifier le niveau du microphone dans les paramètres audio
- Réduire le bruit ambiant
- Se rapprocher du microphone
- Essayer un microphone de meilleure qualité

### L'application est lente

- Vérifier la température du Raspberry Pi : `vcgencmd measure_temp`
- S'assurer qu'aucun autre programme lourd ne tourne
- Envisager un Raspberry Pi 5 pour de meilleures performances

## Structure du projet

```
speech_to_text/
├── app.py                    # Serveur Flask principal
├── requirements.txt          # Dépendances Python
├── download_model.sh         # Script de téléchargement du modèle
├── speech-to-text.service    # Service systemd
├── templates/
│   └── index.html           # Interface HTML
├── static/
│   ├── css/
│   │   └── style.css        # Styles CSS
│   └── js/
│       └── app.js           # Logique JavaScript
└── models/
    └── vosk-model-small-fr-0.22/  # Modèle Vosk (téléchargé)
```

## Technologies utilisées

- **Backend** : Python 3, Flask, Flask-SocketIO
- **Reconnaissance vocale** : Vosk (bibliothèque open-source)
- **Frontend** : HTML5, CSS3, JavaScript (Vanilla)
- **Communication temps réel** : WebSocket (Socket.IO)

## Coûts estimés

- Raspberry Pi 4 (4GB) : ~60€
- Carte SD 32GB : ~10€
- Microphone USB : 20-50€
- Écran tactile 7" : ~60€
- Alimentation : ~10€
- Boîtier : ~10€

**Total : ~170-220€** (achat unique, pas d'abonnement)

## Licence

Ce projet est libre d'utilisation pour un usage personnel.

## Support et questions

Pour toute question ou amélioration, n'hésitez pas à ouvrir une issue sur le dépôt GitHub.

## Remerciements

- [Vosk](https://alphacephei.com/vosk/) pour la reconnaissance vocale open-source
- Communauté Raspberry Pi
- Tous ceux qui contribuent à rendre la technologie accessible

---

Fait avec ❤️ pour mamie
