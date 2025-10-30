# Guide de démarrage rapide

## Installation ultra-rapide (5 minutes)

### 1. Installer les prérequis système

**Sur Raspberry Pi / Debian / Ubuntu :**
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv portaudio19-dev git unzip wget
```

**Sur macOS :**
```bash
brew install portaudio
```

### 2. Installer l'application

```bash
# Cloner ou copier le projet
cd ~/speech_to_text

# Lancer le script de démarrage
./start.sh
```

Le script va :
- Créer l'environnement virtuel
- Installer les dépendances
- Télécharger le modèle Vosk (si nécessaire)
- Lancer l'application

### 3. Ouvrir dans le navigateur

Ouvrez : **http://localhost:5000**

### 4. Utiliser l'application

1. Cliquez sur **"▶️ Démarrer"**
2. Parlez dans votre microphone
3. Le texte apparaît en temps réel !

## Test rapide sans Raspberry Pi

Vous pouvez tester l'application sur votre ordinateur (Mac/Linux/Windows) avant de l'installer sur le Raspberry Pi.

## Premiers réglages recommandés

1. Cliquez sur **⚙️** (paramètres)
2. Ajustez la taille du texte pour votre grand-mère
3. Testez le mode sombre si elle préfère
4. Vérifiez que le défilement automatique est activé

## Problèmes courants

### "Modèle non chargé"
```bash
./download_model.sh
```

### "Microphone non trouvé"
```bash
# Vérifier les micros disponibles
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

### Permissions refusées
```bash
chmod +x start.sh download_model.sh
```

## Pour aller plus loin

Consultez le fichier **README.md** pour :
- Configuration du démarrage automatique
- Mode kiosque pour le navigateur
- Optimisations avancées
- Dépannage détaillé

## Besoin d'aide ?

Ouvrez une issue sur GitHub ou consultez la documentation complète.
