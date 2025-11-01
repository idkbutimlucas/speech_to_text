#!/bin/bash
# Script de lancement de l'application desktop

cd "$(dirname "$0")"

# Activer l'environnement virtuel
source venv/bin/activate

# Lancer l'application
python3 app_desktop.py
