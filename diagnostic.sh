#!/bin/bash
# Script de diagnostic complet de l'API Stock
# Génère un rapport détaillé avec logs, tests API, et état du système

OUTPUT_FILE="diagnostic_$(date +%Y%m%d_%H%M%S).txt"

echo "🔍 Diagnostic de l'API Stock - $(date)" | tee "$OUTPUT_FILE"
echo "================================================" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 1. Informations système
echo "📋 INFORMATIONS SYSTÈME" | tee -a "$OUTPUT_FILE"
echo "------------------------" | tee -a "$OUTPUT_FILE"
echo "Hostname: $(hostname)" | tee -a "$OUTPUT_FILE"
echo "Date: $(date)" | tee -a "$OUTPUT_FILE"
echo "Git branch: $(git branch --show-current)" | tee -a "$OUTPUT_FILE"
echo "Git commit: $(git log --oneline -1)" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 2. État des conteneurs
echo "🐳 ÉTAT DES CONTENEURS DOCKER" | tee -a "$OUTPUT_FILE"
echo "-------------------------------" | tee -a "$OUTPUT_FILE"
docker compose ps | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 3. Vérification du fichier stock_service.py
echo "📄 VÉRIFICATION DU FICHIER stock_service.py" | tee -a "$OUTPUT_FILE"
echo "--------------------------------------------" | tee -a "$OUTPUT_FILE"
echo "Premières lignes du fichier:" | tee -a "$OUTPUT_FILE"
head -10 backend/app/services/stock_service.py | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "Recherche de doublons dans les imports:" | tee -a "$OUTPUT_FILE"
grep "^from typing" backend/app/services/stock_service.py | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 4. Logs des conteneurs (dernières 100 lignes)
echo "📜 LOGS DES CONTENEURS (100 dernières lignes)" | tee -a "$OUTPUT_FILE"
echo "----------------------------------------------" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "=== LOGS API ===" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 100 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "=== LOGS POCKETBASE ===" | tee -a "$OUTPUT_FILE"
docker compose logs pocketbase --tail 50 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 5. Tests API
echo "🧪 TESTS API" | tee -a "$OUTPUT_FILE"
echo "-------------" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 1: Health check
echo "▶ Test 1: Health check" | tee -a "$OUTPUT_FILE"
curl -s http://localhost:8000/health 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 2: Liste des modèles
echo "▶ Test 2: Liste des modèles (GET /models)" | tee -a "$OUTPUT_FILE"
curl -s http://localhost:8000/models 2>&1 | head -50 | tee -a "$OUTPUT_FILE"
echo "... (tronqué)" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 3: Inventaire complet (limité)
echo "▶ Test 3: Inventaire complet (GET /inventory - premières entrées)" | tee -a "$OUTPUT_FILE"
INVENTORY_RESPONSE=$(curl -s http://localhost:8000/inventory 2>&1)
echo "Status: $?" | tee -a "$OUTPUT_FILE"
echo "Response (premiers 500 caractères):" | tee -a "$OUTPUT_FILE"
echo "$INVENTORY_RESPONSE" | head -c 500 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "Filters applied:" | tee -a "$OUTPUT_FILE"
echo "$INVENTORY_RESPONSE" | jq -r '.filters_applied' 2>&1 | tee -a "$OUTPUT_FILE"
echo "Items count:" | tee -a "$OUTPUT_FILE"
echo "$INVENTORY_RESPONSE" | jq -r '.items | length' 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 4: Recherche "sabot" (minuscule)
echo "▶ Test 4: Recherche 'sabot' (GET /inventory?model=sabot)" | tee -a "$OUTPUT_FILE"
SABOT_RESPONSE=$(curl -s "http://localhost:8000/inventory?model=sabot" 2>&1)
echo "Status: $?" | tee -a "$OUTPUT_FILE"
echo "Response:" | tee -a "$OUTPUT_FILE"
echo "$SABOT_RESPONSE" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 5: Recherche "Sabot" (majuscule)
echo "▶ Test 5: Recherche 'Sabot' (GET /inventory?model=Sabot)" | tee -a "$OUTPUT_FILE"
SABOT_MAJ_RESPONSE=$(curl -s "http://localhost:8000/inventory?model=Sabot" 2>&1)
echo "Status: $?" | tee -a "$OUTPUT_FILE"
echo "Response:" | tee -a "$OUTPUT_FILE"
echo "$SABOT_MAJ_RESPONSE" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 6: Recherche avec faute "sabbot"
echo "▶ Test 6: Recherche avec faute 'sabbot' (fuzzy matching)" | tee -a "$OUTPUT_FILE"
FUZZY_RESPONSE=$(curl -s "http://localhost:8000/inventory?model=sabbot" 2>&1)
echo "Status: $?" | tee -a "$OUTPUT_FILE"
echo "Response:" | tee -a "$OUTPUT_FILE"
echo "$FUZZY_RESPONSE" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 7: Recherche par couleur
echo "▶ Test 7: Recherche par couleur 'marron' (GET /inventory?color=marron)" | tee -a "$OUTPUT_FILE"
COLOR_RESPONSE=$(curl -s "http://localhost:8000/inventory?color=marron" 2>&1)
echo "Status: $?" | tee -a "$OUTPUT_FILE"
echo "Filters applied:" | tee -a "$OUTPUT_FILE"
echo "$COLOR_RESPONSE" | jq -r '.filters_applied' 2>&1 | tee -a "$OUTPUT_FILE"
echo "Items count:" | tee -a "$OUTPUT_FILE"
echo "$COLOR_RESPONSE" | jq -r '.items | length' 2>&1 | tee -a "$OUTPUT_FILE"
echo "First 3 items:" | tee -a "$OUTPUT_FILE"
echo "$COLOR_RESPONSE" | jq -r '.items[:3]' 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 6. Logs en temps réel après les tests (30 dernières lignes)
echo "📜 LOGS APRÈS TESTS (30 dernières lignes)" | tee -a "$OUTPUT_FILE"
echo "------------------------------------------" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 30 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 7. Analyse du code Python
echo "🐍 ANALYSE DU CODE PYTHON" | tee -a "$OUTPUT_FILE"
echo "--------------------------" | tee -a "$OUTPUT_FILE"
echo "Vérification syntaxe Python:" | tee -a "$OUTPUT_FILE"
python3 -m py_compile backend/app/services/stock_service.py 2>&1 | tee -a "$OUTPUT_FILE"
if [ $? -eq 0 ]; then
    echo "✅ Syntaxe Python OK" | tee -a "$OUTPUT_FILE"
else
    echo "❌ Erreur de syntaxe Python" | tee -a "$OUTPUT_FILE"
fi
echo "" | tee -a "$OUTPUT_FILE"

# 8. Statistiques PocketBase
echo "💾 STATISTIQUES POCKETBASE" | tee -a "$OUTPUT_FILE"
echo "---------------------------" | tee -a "$OUTPUT_FILE"
echo "Taille des données:" | tee -a "$OUTPUT_FILE"
du -sh pocketbase/pb_data 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "Collections:" | tee -a "$OUTPUT_FILE"
ls -lh pocketbase/pb_data/data.db 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 9. Résumé
echo "📊 RÉSUMÉ" | tee -a "$OUTPUT_FILE"
echo "---------" | tee -a "$OUTPUT_FILE"
echo "✅ Tests API terminés" | tee -a "$OUTPUT_FILE"
echo "📄 Rapport sauvegardé dans: $OUTPUT_FILE" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "🎉 Diagnostic terminé ! Fichier généré: $OUTPUT_FILE"

# Afficher les dernières lignes importantes
echo ""
echo "🔍 Résumé rapide:"
echo "----------------"
grep -E "(Error|error|ERROR|Exception|Traceback|SyntaxError)" "$OUTPUT_FILE" | tail -20 || echo "Aucune erreur détectée"
