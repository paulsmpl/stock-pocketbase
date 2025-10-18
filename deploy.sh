# Script de déploiement rapide pour le serveur Elestio
# À exécuter sur le serveur via SSH

#!/bin/bash

echo "🚀 Déploiement de l'API Stock..."

# Naviguer vers le projet
cd ~/stock-pocketbase || exit 1

# Pull les derniers changements
echo "📥 Récupération du code..."
git pull origin main

# Redémarrer l'API
echo "🔄 Redémarrage de l'API..."
docker compose restart api

# Attendre que l'API soit prête
echo "⏳ Attente du démarrage..."
sleep 5

# Vérifier le statut
echo "✅ Vérification du statut..."
docker compose ps api

echo "🎉 Déploiement terminé !"
echo "Test: curl https://juliane-comedic-safely.ngrok-free.dev/inventory?model=sabot"
