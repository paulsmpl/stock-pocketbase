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

# 3. Vérification des fichiers critiques
echo "📄 VÉRIFICATION DES FICHIERS" | tee -a "$OUTPUT_FILE"
echo "-----------------------------" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "▶ stock_service.py (premières 15 lignes):" | tee -a "$OUTPUT_FILE"
head -15 backend/app/services/stock_service.py | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "▶ fuzzy_matcher.py (complet):" | tee -a "$OUTPUT_FILE"
cat backend/app/services/fuzzy_matcher.py | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "▶ Vérification dans le conteneur Docker:" | tee -a "$OUTPUT_FILE"
docker compose exec -T api cat /app/app/services/stock_service.py | head -15 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 4. Logs avant les tests
echo "📜 LOGS INITIAUX" | tee -a "$OUTPUT_FILE"
echo "----------------" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 50 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 5. Tests API avec monitoring des logs en temps réel
echo "🧪 TESTS API AVEC LOGS" | tee -a "$OUTPUT_FILE"
echo "----------------------" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 1: Health check
echo "▶ Test 1: Health check" | tee -a "$OUTPUT_FILE"
curl -s http://localhost:8000/health 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 1
docker compose logs api --tail 10 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 2: GET /models
echo "▶ Test 2: GET /models" | tee -a "$OUTPUT_FILE"
MODELS_RESPONSE=$(curl -s http://localhost:8000/models 2>&1)
echo "Status code: $?" | tee -a "$OUTPUT_FILE"
echo "Response (premiers 500 chars):" | tee -a "$OUTPUT_FILE"
echo "$MODELS_RESPONSE" | head -c 500 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 1
docker compose logs api --tail 10 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 3: GET /inventory (sans filtre)
echo "▶ Test 3: GET /inventory (sans filtre)" | tee -a "$OUTPUT_FILE"
INVENTORY_FULL=$(curl -s http://localhost:8000/inventory 2>&1)
echo "Status code: $?" | tee -a "$OUTPUT_FILE"
echo "Response structure:" | tee -a "$OUTPUT_FILE"
echo "$INVENTORY_FULL" | jq -r 'if type == "object" then {filters_applied, items_count: (.items | length)} else . end' 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 1
docker compose logs api --tail 10 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 4: GET /inventory?model=sabot (minuscule - DEVRAIT FONCTIONNER)
echo "▶ Test 4: GET /inventory?model=sabot (minuscule)" | tee -a "$OUTPUT_FILE"
echo "Logs AVANT la requête:" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 5 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "Envoi de la requête..." | tee -a "$OUTPUT_FILE"
SABOT_MIN=$(curl -s "http://localhost:8000/inventory?model=sabot" 2>&1)
echo "Status code: $?" | tee -a "$OUTPUT_FILE"
echo "Response complète:" | tee -a "$OUTPUT_FILE"
echo "$SABOT_MIN" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 2
echo "Logs APRÈS la requête:" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 20 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 5: GET /inventory?model=Sabot (majuscule - BUG ICI)
echo "▶ Test 5: GET /inventory?model=Sabot (majuscule - TEST DU BUG)" | tee -a "$OUTPUT_FILE"
echo "Logs AVANT la requête:" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 5 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "Envoi de la requête..." | tee -a "$OUTPUT_FILE"
SABOT_MAJ=$(curl -s "http://localhost:8000/inventory?model=Sabot" 2>&1)
echo "Status code: $?" | tee -a "$OUTPUT_FILE"
echo "Response complète:" | tee -a "$OUTPUT_FILE"
echo "$SABOT_MAJ" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 2
echo "Logs APRÈS la requête (CAPTURE DU BUG):" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 30 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 6: Fuzzy matching "sabbot"
echo "▶ Test 6: GET /inventory?model=sabbot (fuzzy matching)" | tee -a "$OUTPUT_FILE"
SABBOT=$(curl -s "http://localhost:8000/inventory?model=sabbot" 2>&1)
echo "Status code: $?" | tee -a "$OUTPUT_FILE"
echo "Response:" | tee -a "$OUTPUT_FILE"
echo "$SABBOT" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 1
docker compose logs api --tail 10 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 6. Recherche de l'erreur "pop"
echo "🔎 RECHERCHE DE L'ERREUR 'pop'" | tee -a "$OUTPUT_FILE"
echo "-------------------------------" | tee -a "$OUTPUT_FILE"
docker compose logs api 2>&1 | grep -i -A 10 -B 5 "pop expected" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 7. Traceback complet
echo "🐛 TRACEBACKS COMPLETS" | tee -a "$OUTPUT_FILE"
echo "----------------------" | tee -a "$OUTPUT_FILE"
docker compose logs api 2>&1 | grep -i -A 20 "Traceback" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 8. Analyse finale
echo "📊 ANALYSE" | tee -a "$OUTPUT_FILE"
echo "----------" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Vérification syntaxe Python:" | tee -a "$OUTPUT_FILE"
python3 -m py_compile backend/app/services/stock_service.py 2>&1 | tee -a "$OUTPUT_FILE"
[ $? -eq 0 ] && echo "✅ Syntaxe OK" | tee -a "$OUTPUT_FILE" || echo "❌ Erreur syntaxe" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Taille PocketBase:" | tee -a "$OUTPUT_FILE"
du -sh pocketbase/pb_data 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "🎉 Diagnostic terminé ! Fichier: $OUTPUT_FILE" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Résumé des erreurs
echo "🚨 RÉSUMÉ DES ERREURS:"
grep -E "(pop expected|SyntaxError|Exception|Traceback)" "$OUTPUT_FILE" | tail -30