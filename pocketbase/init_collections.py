import os, json, requests, csv
from collections import defaultdict

POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://localhost:8090")
ADMIN_EMAIL = os.getenv("POCKETBASE_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("POCKETBASE_PASSWORD", "admin123")
CSV_PATH = "/pb/stock_initial.csv"
COST_CSV_PATH = "/pb/cost_mapping.csv"

def load_cost_mapping():
    """Charge le mapping des coûts depuis cost_mapping.csv"""
    cost_map = {}  # key: (model, color, gender) -> cost
    if not os.path.exists(COST_CSV_PATH):
        print(f"⚠️ Cost mapping CSV not found: {COST_CSV_PATH}, costs will be null.")
        return cost_map
    
    with open(COST_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model = row['Modèle']
            color = row['Couleur']
            gender = row['Sexe'].lower() if row['Sexe'].lower() != 'unisex' else 'mixte'
            cost = float(row['Cout']) if row['Cout'] and row['Cout'] != '0' else None
            cost_map[(model, color, gender)] = cost
    
    print(f"💰 Loaded {len(cost_map)} cost mappings")
    return cost_map

def import_stock_from_csv(headers):
    """Import stock initial depuis CSV avec batch inserts optimisés"""
    if not os.path.exists(CSV_PATH):
        print(f"⚠️ CSV file not found: {CSV_PATH}, skipping import.")
        return
    
    # Charger le mapping des coûts
    cost_map = load_cost_mapping()
    
    # Grouper par (ID, Modèle, Couleur, Sexe) pour créer les produits
    products_map = {}  # key: (id, model, color, gender) -> {model, color, gender, cost, sizes: [(size, qty)]}
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['ID'], row['Modèle'], row['Couleur'], row['Sexe'])
            if key not in products_map:
                gender_normalized = row['Sexe'].lower() if row['Sexe'].lower() != 'unisex' else 'mixte'
                # Chercher le coût dans le mapping
                cost_key = (row['Modèle'], row['Couleur'], gender_normalized)
                cost = cost_map.get(cost_key)
                
                products_map[key] = {
                    'id': row['ID'],
                    'model': row['Modèle'],
                    'color': row['Couleur'],
                    'gender': gender_normalized,
                    'cost': cost,
                    'sizes': []
                }
            products_map[key]['sizes'].append((row['Pointure'], int(row['Quantité'])))
    
    print(f"📦 Found {len(products_map)} unique products in CSV")
    
    # Vérifier si déjà importé (check si products contient des SKU commençant par les IDs du CSV)
    try:
        existing = requests.get(f"{POCKETBASE_URL}/api/collections/products/records", 
                               headers=headers,
                               params={'perPage': 1}).json()
        if existing.get('totalItems', 0) > 0:
            print("⚠️ Products already exist, skipping CSV import to avoid duplicates.")
            return
    except:
        pass  # OK, collection vide ou inexistante
    
    # Créer les products
    product_ids = {}  # SKU -> product_record_id
    for key, data in products_map.items():
        sku = f"{data['id']}-{data['color'][:3].upper()}"  # Ex: 1-MUL
        
        # Créer le product
        payload = {
            'sku': sku,
            'name': data['model'],
            'color': data['color'],
            'gender': data['gender'],
            'cost': data['cost']
            # 'price' reste null pour l'instant (pas encore d'info)
        }
        try:
            resp = requests.post(f"{POCKETBASE_URL}/api/collections/products/records",
                                headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                product_id = resp.json()['id']
                product_ids[sku] = product_id
                
                # Créer variants + inventory pour chaque taille
                for size, qty in data['sizes']:
                    # Créer variant
                    variant_payload = {'product': product_id, 'size': str(size)}
                    variant_resp = requests.post(f"{POCKETBASE_URL}/api/collections/variants/records",
                                                headers=headers, json=variant_payload)
                    if variant_resp.status_code in [200, 201]:
                        variant_id = variant_resp.json()['id']
                        
                        # Créer inventory
                        inv_payload = {'variant': variant_id, 'quantity': qty, 'reserved': 0}
                        requests.post(f"{POCKETBASE_URL}/api/collections/inventory/records",
                                     headers=headers, json=inv_payload)
            else:
                print(f"⚠️ Failed to create product {sku}: {resp.text}")
        except Exception as e:
            print(f"❌ Error creating product {sku}: {e}")
    
    print(f"✅ Imported {len(product_ids)} products with their variants and inventory")

def main():
    try:
        # Tenter l'authentification admin
        auth = requests.post(f"{POCKETBASE_URL}/api/admins/auth-with-password",
                             json={"identity": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        
        # Si l'admin n'existe pas (400), le créer
        if auth.status_code == 400:
            print("📝 Admin not found, creating initial admin...")
            create_admin = requests.post(f"{POCKETBASE_URL}/api/admins",
                                        json={
                                            "email": ADMIN_EMAIL,
                                            "password": ADMIN_PASSWORD,
                                            "passwordConfirm": ADMIN_PASSWORD
                                        })
            if create_admin.status_code in [200, 201]:
                print(f"✅ Admin created: {ADMIN_EMAIL}")
                # Ré-authentifier après création
                auth = requests.post(f"{POCKETBASE_URL}/api/admins/auth-with-password",
                                   json={"identity": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
                auth.raise_for_status()
            else:
                print(f"❌ Failed to create admin: {create_admin.text}")
                return
        else:
            auth.raise_for_status()
        
        token = auth.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Créer products en premier et récupérer son ID
        products_data = json.load(open("/pb/products.json"))
        resp = requests.get(f"{POCKETBASE_URL}/api/collections/products", headers=headers)
        if resp.status_code == 404:
            print("📦 Creating collection: products")
            create = requests.post(f"{POCKETBASE_URL}/api/collections", headers=headers, json=products_data)
            if create.status_code == 200:
                products_id = create.json()["id"]
                print(f"✅ Collection 'products' created (ID: {products_id})")
            else:
                print(f"❌ Failed to create products: {create.text}")
                return
        else:
            products_id = resp.json()["id"]
            print(f"⚠️ Collection 'products' already exists (ID: {products_id})")

        # Créer variants avec l'ID de products
        variants_data = json.load(open("/pb/variants.json"))
        variants_data["schema"][0]["options"]["collectionId"] = products_id
        resp = requests.get(f"{POCKETBASE_URL}/api/collections/variants", headers=headers)
        if resp.status_code == 404:
            print("📦 Creating collection: variants")
            create = requests.post(f"{POCKETBASE_URL}/api/collections", headers=headers, json=variants_data)
            if create.status_code == 200:
                variants_id = create.json()["id"]
                print(f"✅ Collection 'variants' created (ID: {variants_id})")
            else:
                print(f"❌ Failed to create variants: {create.text}")
                return
        else:
            variants_id = resp.json()["id"]
            print(f"⚠️ Collection 'variants' already exists (ID: {variants_id})")

        # Créer inventory avec l'ID de variants
        inventory_data = json.load(open("/pb/inventory.json"))
        inventory_data["schema"][0]["options"]["collectionId"] = variants_id
        resp = requests.get(f"{POCKETBASE_URL}/api/collections/inventory", headers=headers)
        if resp.status_code == 404:
            print("📦 Creating collection: inventory")
            create = requests.post(f"{POCKETBASE_URL}/api/collections", headers=headers, json=inventory_data)
            if create.status_code == 200:
                print(f"✅ Collection 'inventory' created.")
            else:
                print(f"❌ Failed to create inventory: {create.text}")
        else:
            print(f"⚠️ Collection 'inventory' already exists.")

        # Créer movements avec l'ID de variants
        movements_data = json.load(open("/pb/movements.json"))
        movements_data["schema"][0]["options"]["collectionId"] = variants_id
        resp = requests.get(f"{POCKETBASE_URL}/api/collections/movements", headers=headers)
        if resp.status_code == 404:
            print("📦 Creating collection: movements")
            create = requests.post(f"{POCKETBASE_URL}/api/collections", headers=headers, json=movements_data)
            if create.status_code == 200:
                print(f"✅ Collection 'movements' created.")
            else:
                print(f"❌ Failed to create movements: {create.text}")
        else:
            print(f"⚠️ Collection 'movements' already exists.")
        
        # Importer le stock initial depuis CSV
        print("\n📊 Importing initial stock from CSV...")
        import_stock_from_csv(headers)
        
    except Exception as e:
        print("Init error:", e)

if __name__ == "__main__":
    main()
