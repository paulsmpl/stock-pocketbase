import requests
import json
import os
import csv
from collections import defaultdict

POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://localhost:8090")
ADMIN_EMAIL = os.getenv("POCKETBASE_EMAIL", "admin@stock.local")
ADMIN_PASSWORD = os.getenv("POCKETBASE_PASSWORD", "VotreSuperMotDePasseSecurisé123!")
CSV_PATH = "/pb/stock_initial.csv"

def create_admin():
    """Crée l'admin PocketBase si n'existe pas"""
    print(f"🔐 Création de l'admin {ADMIN_EMAIL}...")
    try:
        response = requests.post(
            f"{POCKETBASE_URL}/api/admins",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "passwordConfirm": ADMIN_PASSWORD
            }
        )
        if response.status_code == 200:
            print("✅ Admin créé avec succès")
            return True
        elif response.status_code == 400:
            # Admin existe déjà
            print("✅ Admin existe déjà")
            return True
        else:
            print(f"❌ Erreur création admin: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur création admin: {e}")
        return False

def authenticate():
    """Authentifie et retourne le token admin"""
    print(f"🔑 Authentification avec {ADMIN_EMAIL}...")
    response = requests.post(
        f"{POCKETBASE_URL}/api/admins/auth-with-password",
        json={"identity": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    response.raise_for_status()
    token = response.json()["token"]
    print("✅ Authentification réussie")
    return token

# ...existing code pour create_collection, import_csv, etc...

if __name__ == "__main__":
    print("🚀 Initialisation de PocketBase...")
    
    # 1. Créer l'admin
    if not create_admin():
        print("❌ Impossible de créer l'admin, arrêt")
        exit(1)
    
    # 2. S'authentifier
    try:
        token = authenticate()
        headers = {"Authorization": token}
    except Exception as e:
        print(f"❌ Authentification échouée: {e}")
        exit(1)
    
    # 3. Créer les collections
    print("📦 Création des collections...")
    # ...existing code...
    
    # 4. Importer les données CSV
    print("📊 Import des données CSV...")
    # ...existing code...
    
    print("✅ Initialisation terminée !")