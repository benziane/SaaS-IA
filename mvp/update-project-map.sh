#!/bin/bash
# Script one-click pour régénérer project-map.json
# Usage: ./update-project-map.sh

echo ""
echo "========================================"
echo "  Régénération du project-map.json"
echo "========================================"
echo ""

cd backend

# Vérifier si Python est disponible
if command -v python3 &> /dev/null; then
    echo "Utilisation de Python3..."
    python3 scripts/generate_project_map.py
elif command -v python &> /dev/null; then
    echo "Utilisation de Python..."
    python scripts/generate_project_map.py
else
    echo "ERREUR: Python n'est pas installé"
    echo "Installez Python 3.11+ depuis https://www.python.org/"
    exit 1
fi

echo ""
echo "========================================"
echo "  Génération terminée!"
echo "========================================"
echo ""
echo "Fichier généré: project-map.json"
echo ""

