#!/bin/bash
# Script pour télécharger le modèle Vosk français

MODEL_NAME="vosk-model-small-fr-0.22"
MODEL_URL="https://alphacephei.com/vosk/models/${MODEL_NAME}.zip"
MODELS_DIR="models"

echo "=== Téléchargement du modèle Vosk français ==="
echo "Modèle: ${MODEL_NAME}"
echo ""

# Créer le dossier models s'il n'existe pas
mkdir -p "${MODELS_DIR}"

# Vérifier si le modèle existe déjà
if [ -d "${MODELS_DIR}/${MODEL_NAME}" ]; then
    echo "Le modèle existe déjà dans ${MODELS_DIR}/${MODEL_NAME}"
    read -p "Voulez-vous le retélécharger? (o/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Oo]$ ]]; then
        echo "Installation annulée."
        exit 0
    fi
    rm -rf "${MODELS_DIR}/${MODEL_NAME}"
fi

# Télécharger le modèle
echo "Téléchargement du modèle (environ 40 MB)..."
if command -v wget &> /dev/null; then
    wget -O "${MODELS_DIR}/${MODEL_NAME}.zip" "${MODEL_URL}"
elif command -v curl &> /dev/null; then
    curl -L -o "${MODELS_DIR}/${MODEL_NAME}.zip" "${MODEL_URL}"
else
    echo "ERREUR: wget ou curl est requis pour télécharger le modèle"
    echo "Veuillez télécharger manuellement depuis: ${MODEL_URL}"
    exit 1
fi

# Vérifier si le téléchargement a réussi
if [ ! -f "${MODELS_DIR}/${MODEL_NAME}.zip" ]; then
    echo "ERREUR: Le téléchargement a échoué"
    exit 1
fi

# Décompresser le modèle
echo "Décompression du modèle..."
if command -v unzip &> /dev/null; then
    unzip -q "${MODELS_DIR}/${MODEL_NAME}.zip" -d "${MODELS_DIR}/"
else
    echo "ERREUR: unzip est requis"
    echo "Sur Raspberry Pi: sudo apt-get install unzip"
    exit 1
fi

# Nettoyer le fichier zip
rm "${MODELS_DIR}/${MODEL_NAME}.zip"

echo ""
echo "✅ Installation terminée!"
echo "Le modèle est installé dans: ${MODELS_DIR}/${MODEL_NAME}"
echo ""
echo "Vous pouvez maintenant lancer l'application avec: python3 app.py"
