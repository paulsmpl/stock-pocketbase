import csv
import requests
import os
import time

POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://localhost:8090")
ADMIN_EMAIL = os.getenv("POCKETBASE_ADMIN_EMAIL", "admin@stock.local")
ADMIN_PASSWORD = os.getenv("POCKETBASE_ADMIN_PASSWORD", "VotreSuperMotDePasseSecurisé123!")
CSV_PATH = "stock_initial.csv"
COST_PATH = "cost_mapping.csv"

def authenticate():
    """Authentification admin PocketBase"""
    print(f"🔐 Authentification en tant que {ADMIN_EMAIL}...")
    
    for i in range(10):
        try:
            response = requests.post(
                f"{POCKETBASE_URL}/api/admins/auth-with-password",
                json={"identity": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=5
            )
            if response.status_code == 200:
                token = response.json()["token"]
                print(f"✅ Authentifié en tant qu'admin")
                return token
        except:
            print(f"⏳ Attente PocketBase... ({i+1}/10)")
            time.sleep(2)
    
    print(f"❌ Erreur d'authentification après 10 tentatives")
    exit(1)

def get_collection_id(headers, collection_name):
    """Récupérer l'ID d'une collection"""
    try:
        response = requests.get(
            f"{POCKETBASE_URL}/api/collections/{collection_name}",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()["id"]
    except:
        pass
    return None

def create_collections(headers):
    """Créer les collections si elles n'existent pas"""
    print("📦 Création des collections...")
    
    # Étape 1: Créer products sans dépendances
    products_schema = {
        "name": "products",
        "type": "base",
        "schema": [
            {"name": "sku", "type": "text", "required": True, "options": {"min": 1, "max": 50}},
            {"name": "name", "type": "text", "required": True, "options": {"min": 1, "max": 200}},
            {"name": "color", "type": "text", "required": False, "options": {"max": 100}},
            {"name": "gender", "type": "text", "required": False, "options": {"max": 50}},
            {"name": "cost", "type": "number", "required": False},
            {"name": "price", "type": "number", "required": False}
        ],
        "indexes": ["CREATE UNIQUE INDEX idx_products_sku ON products (sku)"]
    }
    
    products_id = get_collection_id(headers, "products")
    if not products_id:
        response = requests.post(
            f"{POCKETBASE_URL}/api/collections",
            headers=headers,
            json=products_schema
        )
        if response.status_code == 200:
            products_id = response.json()["id"]
            print(f"  ✅ Collection 'products' créée (ID: {products_id})")
        else:
            print(f"  ❌ Erreur création 'products': {response.text}")
            return
    else:
        print(f"  ✅ Collection 'products' existe déjà (ID: {products_id})")
    
    # Étape 2: Créer variants avec la relation vers products
    variants_schema = {
        "name": "variants",
        "type": "base",
        "schema": [
            {"name": "product", "type": "relation", "required": True, "options": {
                "collectionId": products_id,  # ✅ ID de products
                "cascadeDelete": True,
                "maxSelect": 1
            }},
            {"name": "size", "type": "text", "required": True, "options": {"max": 10}}
        ],
        "indexes": ["CREATE UNIQUE INDEX idx_variants_product_size ON variants (product, size)"]
    }
    
    variants_id = get_collection_id(headers, "variants")
    if not variants_id:
        response = requests.post(
            f"{POCKETBASE_URL}/api/collections",
            headers=headers,
            json=variants_schema
        )
        if response.status_code == 200:
            variants_id = response.json()["id"]
            print(f"  ✅ Collection 'variants' créée (ID: {variants_id})")
        else:
            print(f"  ❌ Erreur création 'variants': {response.text}")
            return
    else:
        print(f"  ✅ Collection 'variants' existe déjà (ID: {variants_id})")
    
    # Étape 3: Créer inventory avec la relation vers variants
    inventory_schema = {
        "name": "inventory",
        "type": "base",
        "schema": [
            {"name": "variant", "type": "relation", "required": True, "options": {
                "collectionId": variants_id,  # ✅ ID de variants
                "cascadeDelete": True,
                "maxSelect": 1
            }},
            {"name": "quantity", "type": "number", "required": True},
            {"name": "reserved", "type": "number", "required": False}
        ],
        "indexes": ["CREATE UNIQUE INDEX idx_inventory_variant ON inventory (variant)"]
    }
    
    inventory_id = get_collection_id(headers, "inventory")
    if not inventory_id:
        response = requests.post(
            f"{POCKETBASE_URL}/api/collections",
            headers=headers,
            json=inventory_schema
        )
        if response.status_code == 200:
            print(f"  ✅ Collection 'inventory' créée")
        else:
            print(f"  ❌ Erreur création 'inventory': {response.text}")
            return
    else:
        print(f"  ✅ Collection 'inventory' existe déjà")
    
    # Étape 4: Créer movements
    movements_schema = {
        "name": "movements",
        "type": "base",
        "schema": [
            {"name": "variant", "type": "relation", "required": True, "options": {
                "collectionId": variants_id,  # ✅ ID de variants
                "cascadeDelete": False,
                "maxSelect": 1
            }},
            {"name": "type", "type": "select", "required": True, "options": {
                "values": ["entry", "exit", "reservation", "unreservation", "adjustment"]
            }},
            {"name": "quantity", "type": "number", "required": True},
            {"name": "reason", "type": "text", "required": False, "options": {"max": 500}},
            {"name": "reference", "type": "text", "required": False, "options": {"max": 100}}
        ]
    }
    
    movements_id = get_collection_id(headers, "movements")
    if not movements_id:
        response = requests.post(
            f"{POCKETBASE_URL}/api/collections",
            headers=headers,
            json=movements_schema
        )
        if response.status_code == 200:
            print(f"  ✅ Collection 'movements' créée")
        else:
            print(f"  ❌ Erreur création 'movements': {response.text}")
    else:
        print(f"  ✅ Collection 'movements' existe déjà")

def load_cost_mapping():
    """Charge les coûts depuis cost_mapping.csv"""
    cost_map = {}
    try:
        with open(COST_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku = row['SKU']
                cost_map[sku] = {
                    'cost': float(row['Cost']) if row['Cost'] else 0,
                    'price': float(row['Price']) if row['Price'] else 0,
                    'source': row['Source']
                }
        print(f"✅ {len(cost_map)} coûts chargés depuis cost_mapping.csv")
    except Exception as e:
        print(f"⚠️  Erreur chargement cost_mapping.csv: {e}")
    return cost_map

if __name__ == "__main__":
    print("🚀 Initialisation de PocketBase...")
    
    token = authenticate()
    headers = {"Authorization": token}
    
    # Créer les collections
    create_collections(headers)
    
    # Charger les coûts
    cost_map = load_cost_mapping()
    
    # Importer depuis stock_initial.csv
    print("📊 Import des données depuis stock_initial.csv...")
    
    products_map = {}
    variants_map = {}
    
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                sku = row['ID']
                model = row['Modèle']
                color = row['Couleur']
                gender = row['Sexe']
                size = row['Pointure']
                quantity = int(row['Quantité'])
                
                cost_info = cost_map.get(sku, {'cost': 0, 'price': 0, 'source': 'Non défini'})
                
                if sku not in products_map:
                    product_data = {
                        "sku": sku,
                        "name": model,
                        "color": color,
                        "gender": gender,
                        "cost": cost_info['cost'],
                        "price": cost_info['price']
                    }
                    
                    response = requests.post(
                        f"{POCKETBASE_URL}/api/collections/products/records",
                        headers=headers,
                        json=product_data
                    )
                    
                    if response.status_code == 200:
                        products_map[sku] = response.json()["id"]
                        print(f"  ✅ Produit créé: SKU {sku} - {model} ({cost_info['cost']}€ / {cost_info['price']}€)")
                    else:
                        print(f"  ❌ Erreur produit SKU {sku}: {response.text}")
                        continue
                
                product_id = products_map[sku]
                variant_key = f"{sku}|{size}"
                
                if variant_key not in variants_map:
                    variant_data = {
                        "product": product_id,
                        "size": size
                    }
                    
                    response = requests.post(
                        f"{POCKETBASE_URL}/api/collections/variants/records",
                        headers=headers,
                        json=variant_data
                    )
                    
                    if response.status_code == 200:
                        variants_map[variant_key] = response.json()["id"]
                    else:
                        print(f"  ❌ Erreur variant SKU {sku} taille {size}: {response.text}")
                        continue
                
                variant_id = variants_map[variant_key]
                
                inventory_data = {
                    "variant": variant_id,
                    "quantity": quantity,
                    "reserved": 0
                }
                
                response = requests.post(
                    f"{POCKETBASE_URL}/api/collections/inventory/records",
                    headers=headers,
                    json=inventory_data
                )
                
                if response.status_code != 200:
                    print(f"  ❌ Erreur inventaire SKU {sku} taille {size}: {response.text}")
    
        print(f"\n✅ Import terminé !")
        print(f"  - {len(products_map)} produits créés")
        print(f"  - {len(variants_map)} variants créés")
        
    except Exception as e:
        print(f"❌ Erreur import: {e}")