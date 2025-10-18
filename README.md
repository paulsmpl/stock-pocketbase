# 🧱 Stock Assistant (FastAPI + PocketBase)

**Stock Assistant** es### 2. Créer les fichiers d'environnement

```bash
# Backend config
cp backend/.env.example backend/.env

# Ngrok config (à la racine)
cp .env.example .env
```

**Important** : Ajoute ton authtoken ngrok dans `.env` :

1. Récupère ton authtoken sur [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)
2. Édite `.env` et remplace `your_ngrok_authtoken_here` par ton token

> ⚠️ **Important** : Le mot de passe admin PocketBase (`POCKETBASE_PASSWORD`) doit contenir **entre 10 et 72 caractères**.

### 3. Lancer avec Dockerpplication légère de gestion de stock connectée à **ChatGPT**.  
Elle combine **PocketBase** comme base de données et back-office, avec **FastAPI** comme API métier et interface pour un connecteur OpenAPI utilisable dans ChatGPT.

---

## ⚙️ Architecture

```
ChatGPT ⇄ FastAPI (backend intelligent)
             ↕
          PocketBase
             ↕
       SQLite + fichiers (images)
```

### Composants :
| Composant | Rôle |
|------------|------|
| **PocketBase** | Base de données, stockage des images et interface d’administration |
| **FastAPI** | Fournit une API simplifiée, logique métier et correction de texte (fuzzy matching) |
| **ChatGPT Connecteur** | Interface conversationnelle qui consomme cette API |
| **Docker Compose** | Orchestre les deux services ensemble |

---

## 🗂 Structure du projet

```
stock-pocketbase/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entrée principale FastAPI
│   │   ├── core/                # Configuration et client PocketBase
│   │   ├── routes/              # Endpoints REST
│   │   ├── services/            # Logique métier
│   │   ├── schemas/             # (optionnel) Modèles Pydantic
│   │   └── utils/               # Fonctions utilitaires
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── pocketbase/
│   ├── Dockerfile
│   ├── init_collections.py      # Script de création automatique des collections
│   ├── products.json
│   ├── variants.json
│   ├── inventory.json
│   └── movements.json
│
├── openapi/openapi.yaml         # Spécification pour le connecteur ChatGPT
├── Caddyfile                    # Configuration reverse proxy HTTPS
├── docker-compose.yml           # Orchestration Caddy + PocketBase + FastAPI
└── README.md
```

---

## 🚀 Démarrage rapide

### 1. Cloner le projet

```bash
git clone https://github.com/ton-org/stock-assistant.git
cd stock-assistant
```

### 2. Créer le fichier d’environnement

```bash
cp backend/.env.example backend/.env
```

### 3. Lancer avec Docker

```bash
docker compose up --build
```

➡️ Accès :

**Après le démarrage, récupère ton URL ngrok publique :**

```bash
# Via l'interface web ngrok
http://localhost:4040

# Ou via API
curl http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'
```

Tu obtiendras une URL type : `https://abc123.ngrok.io`

**Endpoints disponibles :**
- **FastAPI Docs** → `https://YOUR-NGROK-URL/docs`
- **PocketBase Admin** → `https://YOUR-NGROK-URL/_/`
- **PocketBase API** → `https://YOUR-NGROK-URL/api/`

> 🔒 **HTTPS automatique** : ngrok gère automatiquement les certificats SSL.

> 🌐 **URL publique** : Accessible depuis n'importe où sur internet via ngrok.

⚙️ Les collections `products`, `variants`, `inventory` et `movements` sont créées automatiquement par `init_collections.py`.

🎯 **Import automatique du stock initial** : Le fichier `pocketbase/stock_initial.csv` est automatiquement importé au premier démarrage (133 produits, 757 variants). Voir [IMPORT.md](pocketbase/IMPORT.md) pour les détails.

---

## 🧩 Schéma des collections PocketBase

| Collection | Description | Relation |
|-------------|--------------|-----------|
| `products` | Modèles (nom, couleur, image, SKU) | — |
| `variants` | Variantes de produits (par taille, couleur) | → `product` |
| `inventory` | Quantité disponible et réservée | → `variant` |
| `movements` | Journal des ajouts/ventes | → `variant` |

---

## 🧠 Endpoints principaux FastAPI

| Endpoint | Méthode | Description |
|-----------|----------|--------------|
| `/inventory` | `GET` | Liste le stock (filtres : `model`, `color`, `size`) |
| `/inventory/add_stock` | `POST` | Ajoute du stock pour un modèle et une taille |
| `/inventory/sale` | `POST` | Enregistre une vente (décrémente la quantité) |
| `/models` | `GET` | Liste les modèles disponibles |
| `/movements` | `GET` | Liste les mouvements (filtres : `sku`, `size`, `type`) |

💡 Le backend applique un **fuzzy matching** pour corriger les erreurs sur les noms de modèles et couleurs (ex. “Air Fauce” → “Air Force”).

---

## 🧩 Exemple d’utilisation

### Ajouter du stock :
```bash
curl -X POST "http://localhost:8000/inventory/add_stock?sku=ADIDAS-SS&size=42&quantity=5"
```

### Enregistrer une vente :
```bash
curl -X POST "http://localhost:8000/inventory/sale?sku=ADIDAS-SS&size=42&quantity=2"
```

### Lister le stock filtré :
```bash
curl "http://localhost:8000/inventory?model=Stan%20Smith&color=white"
```

---

## 🧩 OpenAPI (pour ChatGPT)

Le fichier `openapi/openapi.yaml` définit les endpoints que ChatGPT peut appeler via un **connecteur “Actions”**.  
Tu peux l’importer directement dans le builder ChatGPT pour créer un assistant personnalisé.

> Exemple d’usage dans ChatGPT :  
> “Ajoute 5 paires de Air Force 1 taille 43 au stock.”  
> → Appel automatique : `POST /inventory/add_stock?sku=NIKE-AF1&size=43&quantity=5`

---

## 🧱 Technologies

| Composant | Version | Rôle |
|------------|----------|------|
| FastAPI | 0.115.5 | Framework API |
| PocketBase | 0.22.14 | Backend + UI |
| Caddy | 2 | Reverse proxy interne |
| Ngrok | latest | Tunnel HTTPS public |
| Python | 3.11 | Langage principal |
| RapidFuzz | 3.9.3 | Correction floue |
| Docker Compose | — | Orchestration |

---

## 🔒 Améliorations futures

- 🔑 Authentification API (`X-API-Key`)
- 📊 Tableau de bord (React/Vue.js)
- 📦 Import/export CSV
- 🧾 Script de génération de produits démo
- 🩺 Endpoint `/health` et `/version`

---

## 🧰 Contribution

1. Fork le repo  
2. Crée ta branche :  
   ```bash
   git checkout -b feature/nom-fonction
   ```
3. Push tes changements  
   ```bash
   git push origin feature/nom-fonction
   ```
4. Crée une Pull Request 🚀
