#!/bin/bash
# Script de démarrage rapide

echo "=== Application Speech-to-Text ==="
echo ""

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances si nécessaire
if [ ! -f "venv/.installed" ]; then
    echo "Installation des dépendances Python..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# Vérifier si le modèle existe
if [ ! -d "models/vosk-model-small-fr-0.22" ]; then
    echo ""
    echo "⚠️  Le modèle Vosk n'est pas installé!"
    echo ""
    read -p "Voulez-vous le télécharger maintenant? (o/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        chmod +x download_model.sh
        ./download_model.sh
    else
        echo "Impossible de démarrer sans le modèle."
        echo "Lancez ./download_model.sh pour l'installer."
        exit 1
    fi
fi

# Lancer l'application
echo ""
echo "Démarrage de l'application..."
echo "Ouvrez votre navigateur sur: http://localhost:5000"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter"
echo ""

python3 app.py
