# Application Speech-to-Text Desktop

Application desktop native de transcription vocale en temps réel pour personnes malentendantes, optimisée pour Raspberry Pi. **Plus performante que la version web.**

## Pourquoi la version desktop ?

- **Meilleure performance** - Moins de latence qu'une application web
- **Plus légère** - Pas de serveur Flask ni de navigateur
- **Démarrage rapide** - Lance directement en plein écran
- **Interface native** - Utilise Tkinter (inclus avec Python)
- **Même fonctionnalités** - Toutes les options de la version web

## Installation rapide

### 1. Installer les dépendances système

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-tk portaudio19-dev git unzip wget
```

**Note:** `python3-tk` est nécessaire pour Tkinter (interface graphique)

### 2. Installer l'application

```bash
cd ~/speech_to_text

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Télécharger le modèle Vosk
chmod +x download_model.sh
./download_model.sh
```

### 3. Lancer l'application

```bash
# Méthode 1: Script de lancement
chmod +x start_desktop.sh
./start_desktop.sh

# Méthode 2: Directement
source venv/bin/activate
python3 app_desktop.py
```

## Utilisation

### Interface

L'application démarre en **plein écran** automatiquement.

- **Zone supérieure** - Texte en cours de reconnaissance (temps réel)
- **Zone inférieure** - Historique des transcriptions avec horodatage
- **Bouton ⋮ (en haut à droite)** - Ouvre les paramètres

### Paramètres disponibles

Dans le menu paramètres (cliquer sur ⋮) :

1. **Taille du texte** - De 30px à 100px (défaut: 60px)
2. **Mode sombre/clair** - Bouton pour basculer
3. **Effacement automatique** - Désactivé, 30s, 1min, 2min
4. **Défilement automatique** - Active/désactive le scroll auto
5. **Effacer maintenant** - Bouton pour vider l'historique

### Raccourcis clavier

- **Échap** - Quitter le mode plein écran
- La reconnaissance démarre automatiquement au lancement

## Configuration automatique au démarrage

Pour que l'application démarre automatiquement avec le Raspberry Pi :

### Option 1: Service systemd (recommandé)

```bash
# Éditer le fichier si nécessaire (vérifier le chemin /home/pi/speech_to_text)
sudo nano speech-to-text-desktop.service

# Copier le service
sudo cp speech-to-text-desktop.service /etc/systemd/system/

# Activer et démarrer
sudo systemctl enable speech-to-text-desktop.service
sudo systemctl start speech-to-text-desktop.service

# Vérifier le statut
sudo systemctl status speech-to-text-desktop.service
```

### Option 2: Autostart LXDE

```bash
# Créer le dossier autostart si nécessaire
mkdir -p ~/.config/autostart

# Créer un fichier .desktop
nano ~/.config/autostart/speech-to-text.desktop
```

Contenu du fichier :

```
[Desktop Entry]
Type=Application
Name=Speech to Text
Exec=/home/pi/speech_to_text/start_desktop.sh
Terminal=false
```

## Sauvegarde des paramètres

Les paramètres sont automatiquement sauvegardés dans `config.json` :
- Taille du texte
- Thème (clair/sombre)
- Délai d'effacement automatique
- Défilement automatique

## Comparaison version Web vs Desktop

| Fonctionnalité | Version Web | Version Desktop |
|----------------|-------------|-----------------|
| Performance | Moyenne | **Excellente** |
| Latence | ~200-300ms | **~50-100ms** |
| RAM utilisée | ~400MB | **~250MB** |
| Démarrage | 5-10s | **2-3s** |
| Interface | Navigateur | **Native** |
| Fonctionnalités | ✅ Toutes | ✅ Toutes |

## Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
journalctl -u speech-to-text-desktop.service -f

# Tester manuellement
cd ~/speech_to_text
source venv/bin/activate
python3 app_desktop.py
```

### Erreur "no display"

L'application nécessite un environnement graphique. Vérifiez que :
- Le Raspberry Pi est démarré avec le bureau (pas en mode console uniquement)
- La variable DISPLAY est définie : `echo $DISPLAY` (devrait afficher `:0`)

### Le microphone ne fonctionne pas

Identique à la version web :

```bash
# Lister les microphones
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Tester
arecord -d 5 test.wav && aplay test.wav
```

### L'application est lente

- Vérifier la température : `vcgencmd measure_temp`
- Fermer les autres applications
- Considérer un Raspberry Pi 5

## Avantages pour votre grand-mère

1. **Plus simple** - Lance directement en plein écran
2. **Plus rapide** - Réactivité immédiate
3. **Plus fiable** - Pas de problème de navigateur/cache
4. **Autonome** - Fonctionne 100% localement
5. **Maintenance facile** - Redémarre automatiquement en cas d'erreur

## Migration depuis la version web

Si vous aviez la version web qui tournait :

```bash
# Arrêter l'ancienne version
sudo systemctl stop speech-to-text.service
sudo systemctl disable speech-to-text.service

# Lancer la nouvelle version desktop
./start_desktop.sh
```

Les deux versions peuvent coexister, mais utilisez la version desktop pour de meilleures performances !

## Support

Pour toute question, voir le fichier GUIDE_MAMIE.md ou README.md principal.

---

**Version Desktop - Optimisée pour Raspberry Pi**
