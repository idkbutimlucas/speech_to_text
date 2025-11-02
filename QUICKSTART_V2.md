# ⚡ Démarrage Rapide

Guide ultra-rapide pour tester l'application.

## 🚀 Mac / PC (Test)

```bash
cd ~/Documents/Perso/speech_to_text
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Ouvrir : **http://localhost:5001**

## 🥧 Raspberry Pi 4

```bash
# Installation (une seule fois)
sudo apt install -y python3-pip python3-venv portaudio19-dev
cd ~/speech_to_text
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./download_model.sh

# Lancer
python3 app.py
```

Ouvrir : **http://IP_DU_PI:5001**

## 🎯 Tester les Fonctionnalités

### 1. VAD (CPU réduit)
- Laissez tourner sans parler
- CPU devrait être ~15-20%
- Parlez → CPU monte à ~60%

### 2. Ponctuation
- Dites : "bonjour comment allez vous"
- Résultat : "Bonjour, comment allez-vous ?"

### 3. Urgence
- Dites : "j'ai besoin d'aide"
- Flash rouge + ⚠️ devant le texte

### 4. Barre Audio
- Regardez la barre 🎤 en haut
- Bouge quand vous parlez

### 5. Stats
- Cliquez sur 📊
- Voir CPU, RAM, etc.

### 6. Export
- Paramètres (⋮) → 💾 Exporter
- Fichier .txt créé

## 📊 Performance Attendue (RPi4)

| Métrique | Valeur |
|----------|--------|
| CPU silence | 15-20% |
| CPU parole | 60% |
| Latence | 150ms |
| Précision | 90% |

## 🛠️ Problèmes Courants

### Pas de dépendances
```bash
pip install -r requirements.txt
```

### Modèle manquant
```bash
./download_model.sh
```

### Micro ne fonctionne pas
```bash
# Mac: Autoriser dans Préférences Système > Microphone
# RPi: arecord -d 5 test.wav && aplay test.wav
```

### App lente
Désactiver ponctuation et bruit dans paramètres (⋮)

## ✅ Checklist

- [ ] App démarre
- [ ] Texte s'affiche quand je parle
- [ ] Ponctuation ajoutée
- [ ] Barre audio bouge
- [ ] Stats disponibles (📊)
- [ ] Export fonctionne (💾)

## 📚 Docs Complètes

- **Installation RPi** : [INSTALL.md](INSTALL.md)
- **Documentation** : [README.md](README.md)
- **Améliorations** : [README_IMPROVEMENTS.md](README_IMPROVEMENTS.md)

---

**C'est parti !** 🎊
