import csv
import requests
import os

POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://localhost:8090")
ADMIN_EMAIL = os.getenv("POCKETBASE_ADMIN_EMAIL", "admin@stock.local")
ADMIN_PASSWORD = os.getenv("POCKETBASE_ADMIN_PASSWORD", "VotreSuperMotDePasseSecurisé123!")
CSV_PATH = "stock_initial.csv"
COST_PATH = "cost_mapping.csv"

def authenticate():
    """Authentification admin PocketBase"""
    print(f"🔐 Authentification en tant que {ADMIN_EMAIL}...")
    
    response = requests.post(
        f"{POCKETBASE_URL}/api/admins/auth-with-password",
        json={"identity": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    
    if response.status_code == 200:
        token = response.json()["token"]
        print(f"✅ Authentifié en tant qu'admin")
        return token
    else:
        print(f"❌ Erreur d'authentification: {response.text}")
        exit(1)

def load_cost_mapping():
    """Charge les coûts depuis cost_mapping.csv"""
    cost_map = {}
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
    return cost_map

if __name__ == "__main__":
    print("🚀 Initialisation de PocketBase...")
    
    token = authenticate()
    headers = {"Authorization": token}
    
    # Charger les coûts
    cost_map = load_cost_mapping()
    
    # Importer depuis stock_initial.csv
    print("📊 Import des données depuis stock_initial.csv...")
    
    products_map = {}  # {SKU: product_record_id}
    variants_map = {}  # {SKU|Pointure: variant_record_id}
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            sku = row['ID']
            model = row['Modèle']
            color = row['Couleur']
            gender = row['Sexe']
            size = row['Pointure']
            quantity = int(row['Quantité'])
            
            # Récupérer le coût et prix
            cost_info = cost_map.get(sku, {'cost': 0, 'price': 0, 'source': 'Non défini'})
            
            # Créer ou récupérer le produit
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
            
            # Créer le variant (taille)
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
            
            # Créer l'inventaire
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