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

        collections = ["products.json", "variants.json", "inventory.json", "movements.json"]
        for file in collections:
            path = os.path.join("/pb", file)
            with open(path, "r") as f:
                collection_data = json.load(f)
                name = collection_data["name"]

            resp = requests.get(f"{POCKETBASE_URL}/api/collections/{name}", headers=headers)
            if resp.status_code == 404:
                print(f"📦 Creating collection: {name}")
                create = requests.post(f"{POCKETBASE_URL}/api/collections", headers=headers, json=collection_data)
                if create.status_code == 200:
                    print(f"✅ Collection '{name}' created.")
                else:
                    print(f"❌ Failed to create {name}: {create.text}")
            else:
                print(f"⚠️ Collection '{name}' already exists.")
    except Exception as e:
        print("Init error:", e)

if __name__ == "__main__":
    main()
