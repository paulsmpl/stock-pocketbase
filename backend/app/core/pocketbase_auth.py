import requests
import os
from functools import lru_cache
from datetime import datetime, timedelta

POCKETBASE_URL = "http://pocketbase:8090"
ADMIN_EMAIL = os.getenv("POCKETBASE_ADMIN_EMAIL", "admin@stock.local")
ADMIN_PASSWORD = os.getenv("POCKETBASE_ADMIN_PASSWORD", "VotreSuperMotDePasseSecurisé123!")

# Cache du token avec expiration
_token_cache = {"token": None, "expires_at": None}

def get_auth_token():
    """Récupère et cache le token d'authentification PocketBase"""
    now = datetime.now()
    
    # Si token en cache et valide, le retourner
    if _token_cache["token"] and _token_cache["expires_at"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]
    
    # Sinon, se reconnecter
    try:
        response = requests.post(
            f"{POCKETBASE_URL}/api/admins/auth-with-password",
            json={"identity": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        response.raise_for_status()
        data = response.json()
        
        # Cacher le token (expire dans 2 heures par défaut)
        _token_cache["token"] = data["token"]
        _token_cache["expires_at"] = now + timedelta(hours=1, minutes=50)  # 10 min de marge
        
        return data["token"]
    except Exception as e:
        raise Exception(f"Échec d'authentification PocketBase: {str(e)}")

def get_auth_headers():
    """Retourne les headers HTTP avec le token d'authentification"""
    token = get_auth_token()
    return {"Authorization": token}

def authenticated_request(method, url, **kwargs):
    """Fait une requête HTTP authentifiée vers PocketBase"""
    headers = kwargs.pop("headers", {})
    headers.update(get_auth_headers())
    
    response = requests.request(method, url, headers=headers, **kwargs)
    
    # Si 401/403, rafraîchir le token et réessayer
    if response.status_code in [401, 403]:
        _token_cache["token"] = None  # Invalider le cache
        headers.update(get_auth_headers())
        response = requests.request(method, url, headers=headers, **kwargs)
    
    response.raise_for_status()
    return response