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

# 5. Tests API via réseau Docker interne
echo "🧪 TESTS API (réseau Docker interne)" | tee -a "$OUTPUT_FILE"
echo "-------------------------------------" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 1: Health check
echo "▶ Test 1: GET / (health check)" | tee -a "$OUTPUT_FILE"
docker compose exec -T caddy wget -qO- http://api:8000/ 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 1
docker compose logs api --tail 10 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 2: GET /models
echo "▶ Test 2: GET /models" | tee -a "$OUTPUT_FILE"
docker compose exec -T caddy wget -qO- http://api:8000/models 2>&1 | head -c 1000 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 1
docker compose logs api --tail 10 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 3: GET /inventory (sans filtre)
echo "▶ Test 3: GET /inventory (sans filtre)" | tee -a "$OUTPUT_FILE"
docker compose exec -T caddy wget -qO- http://api:8000/inventory 2>&1 | head -c 1000 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 1
docker compose logs api --tail 10 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 4: GET /inventory?model=sabot (minuscule - fuzzy matching)
echo "▶ Test 4: GET /inventory?model=sabot (minuscule - fuzzy matching)" | tee -a "$OUTPUT_FILE"
echo "Logs AVANT:" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 5 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
docker compose exec -T caddy wget -qO- 'http://api:8000/inventory?model=sabot' 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 2
echo "Logs APRÈS:" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 20 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 5: GET /inventory?model=Sabot (majuscule - TEST DU BUG)
echo "▶ Test 5: GET /inventory?model=Sabot (majuscule - BUG ATTENDU)" | tee -a "$OUTPUT_FILE"
echo "Logs AVANT:" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 5 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "📡 Envoi de la requête avec model=Sabot..." | tee -a "$OUTPUT_FILE"
docker compose exec -T caddy wget -qO- 'http://api:8000/inventory?model=Sabot' 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 2
echo "🔥 Logs APRÈS (CAPTURE DU BUG 'pop'):" | tee -a "$OUTPUT_FILE"
docker compose logs api --tail 30 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 6: Fuzzy matching "sabbot" (faute de frappe)
echo "▶ Test 6: GET /inventory?model=sabbot (fuzzy matching typo)" | tee -a "$OUTPUT_FILE"
docker compose exec -T caddy wget -qO- 'http://api:8000/inventory?model=sabbot' 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 1
docker compose logs api --tail 10 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 7: Filtre par couleur
echo "▶ Test 7: GET /inventory?color=Marron" | tee -a "$OUTPUT_FILE"
docker compose exec -T caddy wget -qO- 'http://api:8000/inventory?color=Marron' 2>&1 | head -c 500 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 1
docker compose logs api --tail 10 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Test 8: Filtres combinés
echo "▶ Test 8: GET /inventory?model=Sabot&color=Noir (filtres combinés)" | tee -a "$OUTPUT_FILE"
docker compose exec -T caddy wget -qO- 'http://api:8000/inventory?model=Sabot&color=Noir' 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
sleep 1
docker compose logs api --tail 10 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 6. Recherche de l'erreur "pop"
echo "🔎 RECHERCHE DE L'ERREUR 'pop'" | tee -a "$OUTPUT_FILE"
echo "-------------------------------" | tee -a "$OUTPUT_FILE"
docker compose logs api 2>&1 | grep -i -A 10 -B 5 "pop expected" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 7. Recherche de tous les Tracebacks
echo "🐛 TOUS LES TRACEBACKS" | tee -a "$OUTPUT_FILE"
echo "----------------------" | tee -a "$OUTPUT_FILE"
docker compose logs api 2>&1 | grep -i -A 20 "Traceback" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 8. Analyse finale
echo "📊 ANALYSE FINALE" | tee -a "$OUTPUT_FILE"
echo "-----------------" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Vérification syntaxe Python (hôte):" | tee -a "$OUTPUT_FILE"
python3 -m py_compile backend/app/services/stock_service.py 2>&1 | tee -a "$OUTPUT_FILE"
[ $? -eq 0 ] && echo "✅ Syntaxe OK sur l'hôte" | tee -a "$OUTPUT_FILE" || echo "❌ Erreur syntaxe sur l'hôte" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Vérification syntaxe Python (conteneur):" | tee -a "$OUTPUT_FILE"
docker compose exec -T api python3 -m py_compile /app/app/services/stock_service.py 2>&1 | tee -a "$OUTPUT_FILE"
[ $? -eq 0 ] && echo "✅ Syntaxe OK dans le conteneur" | tee -a "$OUTPUT_FILE" || echo "❌ Erreur syntaxe dans le conteneur" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Taille PocketBase:" | tee -a "$OUTPUT_FILE"
du -sh pocketbase/pb_data 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Nombre de produits dans PocketBase:" | tee -a "$OUTPUT_FILE"
docker compose exec -T pocketbase /pb/pocketbase admin list-records products --count 2>&1 | tee -a "$OUTPUT_FILE" || echo "Commande non disponible" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "🎉 Diagnostic terminé ! Fichier: $OUTPUT_FILE" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Résumé des erreurs critiques
echo "🚨 RÉSUMÉ DES ERREURS CRITIQUES:" | tee -a "$OUTPUT_FILE"
echo "---------------------------------" | tee -a "$OUTPUT_FILE"
grep -E "(pop expected|SyntaxError|Exception|Traceback|ERROR|CRITICAL)" "$OUTPUT_FILE" | tail -50 | tee -a "$OUTPUT_FILE"