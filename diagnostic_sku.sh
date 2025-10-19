cat > ~/stock-pocketbase/diagnostic_sku.sh << 'EOF'
#!/bin/bash

SKU=${1:-"212-MAR"}

echo "🔍 Test comparatif pour SKU: $SKU"
echo "================================================"
echo ""

# Récupérer le token admin
echo "🔑 Authentification PocketBase..."
TOKEN=$(docker compose exec -T api python3 << 'PYEOF'
from app.core.pocketbase_auth import get_auth_token
print(get_auth_token())
PYEOF
)

if [ -z "$TOKEN" ]; then
    echo "❌ Échec authentification"
    exit 1
fi

echo "✅ Token obtenu"
echo ""

# TEST 1: PocketBase API directe - Recherche du produit
echo "📦 TEST 1: PocketBase API - Recherche produit par SKU"
echo "------------------------------------------------------"
PRODUCT=$(docker compose exec -T pocketbase wget -q -O- \
  --header="Authorization: $TOKEN" \
  "http://localhost:8090/api/collections/products/records?filter=(sku='$SKU')&perPage=1")

echo "$PRODUCT" | jq -r '
if .items | length > 0 then
  "✅ Produit trouvé:",
  "  ID: " + .items[0].id,
  "  SKU: " + .items[0].sku,
  "  Nom: " + .items[0].name,
  "  Couleur: " + (.items[0].color // "N/A"),
  "  Prix: " + (.items[0].price | tostring) + "€"
else
  "❌ Produit introuvable"
end
'

PRODUCT_ID=$(echo "$PRODUCT" | jq -r '.items[0].id // empty')
echo ""

if [ -z "$PRODUCT_ID" ]; then
    echo "❌ Impossible de continuer sans product_id"
    exit 1
fi

# TEST 2: PocketBase API - Récupérer les variants
echo "📐 TEST 2: PocketBase API - Variants du produit"
echo "------------------------------------------------------"
VARIANTS=$(docker compose exec -T pocketbase wget -q -O- \
  --header="Authorization: $TOKEN" \
  "http://localhost:8090/api/collections/variants/records?filter=(product='$PRODUCT_ID')&perPage=100")

echo "$VARIANTS" | jq -r '
if .items | length > 0 then
  "✅ " + (.items | length | tostring) + " variants trouvés:",
  (.items[] | "  - Taille: " + .size + " (ID: " + .id + ")")
else
  "❌ Aucun variant trouvé"
end
'

VARIANT_IDS=$(echo "$VARIANTS" | jq -r '.items[].id')
echo ""

# TEST 3: PocketBase API - Inventaire pour chaque variant
echo "📊 TEST 3: PocketBase API - Inventaire par variant"
echo "------------------------------------------------------"
for VARIANT_ID in $VARIANT_IDS; do
    INV=$(docker compose exec -T pocketbase wget -q -O- \
      --header="Authorization: $TOKEN" \
      "http://localhost:8090/api/collections/inventory/records?filter=(variant='$VARIANT_ID')&perPage=1&expand=variant")
    
    echo "$INV" | jq -r '
    if .items | length > 0 then
      "  Taille " + .items[0].expand.variant.size + ": " + (.items[0].quantity | tostring) + " unités (réservé: " + ((.items[0].reserved // 0) | tostring) + ")"
    else
      "  Variant " + "'$VARIANT_ID'" + ": Pas d'\''inventaire"
    end
    '
done
echo ""

# TEST 4: PocketBase API - Inventaire avec expand complet
echo "🔗 TEST 4: PocketBase API - Inventaire avec expand complet"
echo "------------------------------------------------------"
INV_FULL=$(docker compose exec -T pocketbase wget -q -O- \
  --header="Authorization: $TOKEN" \
  "http://localhost:8090/api/collections/inventory/records?expand=variant,variant.product&perPage=500")

echo "$INV_FULL" | jq -r --arg SKU "$SKU" '
.items[] | 
select(.expand.variant.expand.product.sku == $SKU) |
"  Taille " + .expand.variant.size + ": " + (.quantity | tostring) + " unités (réservé: " + ((.reserved // 0) | tostring) + ")"
'
echo ""

# TEST 5: FastAPI - Liste complète de l'inventaire
echo "🚀 TEST 5: FastAPI - Liste complète de l'inventaire"
echo "------------------------------------------------------"
FASTAPI_ALL=$(docker compose exec -T pocketbase wget -q -O- "http://api:8000/inventory")

echo "$FASTAPI_ALL" | jq -r --arg SKU "$SKU" '
.items[] | 
select(.sku == $SKU) |
"  ✅ Taille " + .size + ": " + (.quantity | tostring) + " unités (réservé: " + ((.reserved // 0) | tostring) + ")"
'

COUNT=$(echo "$FASTAPI_ALL" | jq -r --arg SKU "$SKU" '[.items[] | select(.sku == $SKU)] | length')
if [ "$COUNT" = "0" ]; then
    echo "  ❌ Aucun résultat pour SKU $SKU dans FastAPI"
fi
echo ""

# TEST 6: FastAPI - Test avec fuzzy matching
echo "🎯 TEST 6: FastAPI - Test avec le modèle exact"
echo "------------------------------------------------------"
MODEL_NAME=$(echo "$PRODUCT" | jq -r '.items[0].name')
FASTAPI_MODEL=$(docker compose exec -T pocketbase wget -q -O- "http://api:8000/inventory?model=$MODEL_NAME")

echo "  Recherche avec model=$MODEL_NAME"
COUNT_MODEL=$(echo "$FASTAPI_MODEL" | jq -r --arg SKU "$SKU" '[.items[] | select(.sku == $SKU)] | length')
echo "  Résultats: $COUNT_MODEL items"
echo ""

# TEST 7: Python debug - Analyse des données brutes
echo "🔬 TEST 7: Python debug - Analyse complète"
echo "------------------------------------------------------"
docker compose exec api python3 << PYEOF
from app.services.stock_service import list_inventory
from app.core.pocketbase_auth import authenticated_request, POCKETBASE_URL

# Récupérer les données brutes
response = authenticated_request(
    "GET",
    f"{POCKETBASE_URL}/api/collections/inventory/records",
    params={"expand": "variant,variant.product", "perPage": 500}
)
data = response.json()

print(f"  Total items dans inventory: {len(data.get('items', []))}")

# Chercher le SKU
found = []
for item in data.get("items", []):
    expand = item.get("expand", {})
    variant = expand.get("variant", {})
    if isinstance(variant, list):
        variant = variant[0] if variant else {}
    
    variant_expand = variant.get("expand", {})
    product = variant_expand.get("product", {})
    if isinstance(product, list):
        product = product[0] if product else {}
    
    sku = product.get("sku")
    if sku == "$SKU":
        found.append({
            "model": product.get("name"),
            "color": product.get("color"),
            "size": variant.get("size"),
            "quantity": item.get("quantity", 0)
        })

if found:
    print(f"  ✅ Trouvé {len(found)} items pour SKU $SKU:")
    for f in found:
        print(f"    - {f['model']} {f['color']} taille {f['size']}: {f['quantity']} unités")
else:
    print(f"  ❌ SKU $SKU introuvable dans les données brutes")

# Test avec list_inventory
print(f"\n  Test avec list_inventory():")
result = list_inventory()
items = [i for i in result['items'] if i.get('sku') == '$SKU']
print(f"  Résultat: {len(items)} items")
if items:
    for item in items:
        print(f"    - Taille {item['size']}: {item['quantity']} unités")
PYEOF

echo ""
echo "================================================"
echo "✅ Diagnostic terminé"
EOF

chmod +x ~/stock-pocketbase/diagnostic_sku.sh