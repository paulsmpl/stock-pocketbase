import os, json, requests

POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://localhost:8090")
ADMIN_EMAIL = os.getenv("POCKETBASE_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("POCKETBASE_PASSWORD", "admin123")

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
    except Exception as e:
        print("Init error:", e)

if __name__ == "__main__":
    main()
