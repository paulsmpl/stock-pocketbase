# 🤖 Créer un GPT Custom sur OpenAI Platform

Ce guide explique comment créer un assistant ChatGPT personnalisé qui utilise ton API de gestion de stock.

---

## 📋 Prérequis

✅ Compte **ChatGPT Plus** ou **ChatGPT Team/Enterprise**  
✅ API déployée et accessible via ngrok : `https://juliane-comedic-safely.ngrok-free.dev`  
✅ Fichier `openapi/openapi.yaml` à jour

---

## 🚀 Étape 1 : Créer un nouveau GPT

1. **Aller sur ChatGPT** : https://chat.openai.com/
2. **Cliquer sur ton profil** (en haut à droite) → **Mes GPTs**
3. **Cliquer sur "Créer un GPT"** (ou "Create a GPT")
4. **Choisir "Configurer"** (Configure) pour le mode manuel

---

## ⚙️ Étape 2 : Configuration de base

### 📝 Section "Détails" (Details)

**Nom** :
```
Stock Assistant - Chaussures
```

**Description** :
```
Assistant de gestion de stock de chaussures avec support des genres (homme/femme/mixte), 
coûts et prix. Permet de consulter l'inventaire, ajouter du stock et enregistrer des ventes.
```

**Instructions** (System Prompt) :
```markdown
Tu es un assistant spécialisé dans la gestion de stock de chaussures.

# Capacités
- Consulter l'inventaire en temps réel avec filtres (modèle, couleur, taille, genre)
- Ajouter du stock pour un modèle et une taille
- Enregistrer des ventes (décrémenter le stock)
- Consulter l'historique des mouvements de stock
- Afficher les informations de coût et prix

# Règles importantes
1. **Toujours utiliser le fuzzy matching** : Si l'utilisateur dit "hermè" au lieu de "Hermès", 
   l'API corrigera automatiquement.
2. **Genre** : Les produits ont 3 genres possibles : homme, femme, mixte
3. **SKU** : Format {ID}-{3_LETTRES_COULEUR} (ex: 1-MUL, 22-BLA)
4. **Coût vs Prix** : 
   - `cost` = coût d'achat
   - `price` = prix de vente (peut être null)
5. **Pointures** : Afficher toutes les tailles disponibles pour un modèle

# Comportement
- Présenter les résultats de manière claire et structurée (tableaux Markdown)
- Calculer automatiquement les marges si coût ET prix sont disponibles
- Alerter si le stock est bas (< 3 unités)
- Confirmer les actions d'ajout/vente avec un résumé

# Exemples de requêtes
- "Combien de Hermès blanches taille 38 ?"
- "Ajoute 5 paires de SKU 1-MUL taille 37"
- "Vends 2 paires de Tropézienne rouge taille 40"
- "Montre-moi tous les modèles femme en stock"
- "Quel est le coût moyen des produits homme ?"
```

**Photo de profil** (optionnel) :
- Upload une icône de chaussure ou logo de boutique

---

## 🔗 Étape 3 : Ajouter l'Action API

### Dans la section "Actions"

1. **Cliquer sur "Créer une nouvelle action"** (Create new action)

2. **Méthode d'authentification** : Sélectionner **"None"** (pas d'auth pour l'instant)

3. **Schéma OpenAPI** : Coller le contenu du fichier `openapi/openapi.yaml`

```yaml
openapi: 3.1.0
info:
  title: Stock Assistant API
  description: API de gestion de stock de chaussures avec support du genre (homme/femme/mixte), des coûts et des prix
  version: 1.0.0
servers:
  - url: https://juliane-comedic-safely.ngrok-free.dev
    description: Serveur de production via ngrok
# ... (coller tout le contenu)
```

4. **Politique de confidentialité** (Privacy Policy) : Laisser vide ou ajouter :
```
https://votre-site.com/privacy
```

5. **Cliquer sur "Tester"** pour vérifier que l'API répond correctement

---

## 🧪 Étape 4 : Tester le GPT

### Tests recommandés

1. **Test inventaire basique** :
```
Montre-moi tous les modèles disponibles
```

2. **Test avec filtre** :
```
Combien de modèles femme en multicolore ?
```

3. **Test fuzzy matching** :
```
Donne-moi le stock de "hermes" (sans accent)
```

4. **Test ajout de stock** :
```
Ajoute 3 paires de SKU 1-MUL taille 38
```

5. **Test vente** :
```
Enregistre une vente de 2 paires de Arabique multicolore taille 37
```

6. **Test statistiques** :
```
Quel est le coût moyen des chaussures femme ?
```

---

## 🎨 Étape 5 : Personnalisation avancée

### Ajouter des capacités supplémentaires

Dans les **Capacités** (Capabilities) :
- ✅ **Web Browsing** : Désactiver (pas nécessaire)
- ✅ **DALL·E Image Generation** : Activer si tu veux générer des visuels de stock
- ✅ **Code Interpreter** : Activer pour faire des analyses statistiques

### Exemples de conversation (Conversation Starters)

Ajouter des suggestions de requêtes :
```
💼 "Montre-moi l'inventaire complet"
👠 "Quels modèles femme sont disponibles ?"
📊 "Donne-moi les statistiques de stock"
🛒 "Enregistre une vente"
```

---

## 🔒 Étape 6 : Sécurité (Optionnel mais recommandé)

### Option 1 : Ajouter une API Key

1. **Générer une clé API** dans `.env` :
```bash
API_KEY=votre_cle_secrete_ici
```

2. **Modifier le code FastAPI** pour vérifier la clé :
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(401, "Invalid API Key")
```

3. **Dans OpenAI Platform** → Actions → Authentication :
   - Type : **Custom**
   - Header Name : `X-API-Key`
   - Value : `votre_cle_secrete_ici`

### Option 2 : Utiliser OAuth2 (avancé)

Voir la documentation PocketBase pour configurer OAuth2.

---

## 📊 Étape 7 : Publier le GPT

1. **Visibilité** :
   - **Privé** (Only me) : Toi seul peut l'utiliser
   - **Lien partagé** (Anyone with a link) : Partage avec des collaborateurs
   - **Public** : Visible sur le GPT Store (nécessite vérification)

2. **Cliquer sur "Créer"** ou "Update"

3. **Tester dans une nouvelle conversation** :
```
@Stock Assistant - Chaussures montre-moi l'inventaire
```

---

## 🎯 Cas d'usage avancés

### 1. Alertes de stock bas
```
Quels produits ont moins de 3 unités en stock ?
```

### 2. Analyse de rentabilité
```
Calcule la marge pour les produits où le prix est défini
```

### 3. Recommandations de réassort
```
Quels sont les modèles les plus vendus ce mois ?
```

### 4. Export de données
```
Génère un CSV de l'inventaire complet
```

---

## 🐛 Résolution de problèmes

### Erreur "Failed to fetch"
- ✅ Vérifier que ngrok est actif : `docker compose logs ngrok`
- ✅ Tester l'URL manuellement : `https://juliane-comedic-safely.ngrok-free.dev/docs`

### Erreur "Invalid schema"
- ✅ Valider le YAML sur https://editor.swagger.io/
- ✅ Vérifier que tous les `operationId` sont uniques

### Le GPT ne trouve pas les données
- ✅ Vérifier que l'import CSV a bien fonctionné : `GET /models`
- ✅ Tester les endpoints manuellement avec Postman/curl

### Ngrok URL change
- ✅ Mettre à jour le `servers.url` dans `openapi.yaml`
- ✅ Re-importer le schema dans OpenAI Platform

---

## 📱 Utilisation mobile

Le GPT sera accessible sur :
- **Application mobile ChatGPT** (iOS/Android)
- **Web** : https://chat.openai.com/

---

## 🚀 Améliorations futures

1. **Ajouter des photos de produits** :
   - Upload les images dans PocketBase
   - Le GPT peut afficher les visuels

2. **Notifications** :
   - Webhooks pour alerter quand stock < seuil

3. **Multi-langue** :
   - Support FR/EN dans les prompts

4. **Analytics** :
   - Intégrer un endpoint `/stats` pour les KPIs

---

## 📚 Ressources

- **Documentation OpenAI GPTs** : https://platform.openai.com/docs/actions
- **Swagger Editor** : https://editor.swagger.io/
- **Ngrok Dashboard** : http://localhost:4040
- **PocketBase Admin** : https://juliane-comedic-safely.ngrok-free.dev/_/

---

## ✅ Checklist finale

- [ ] GPT créé avec le bon nom et description
- [ ] System prompt configuré avec les instructions
- [ ] Action API ajoutée avec le schema OpenAPI complet
- [ ] Tests réalisés sur au moins 5 requêtes différentes
- [ ] Conversation starters ajoutés
- [ ] Visibilité définie (privé/partagé/public)
- [ ] URL ngrok à jour dans le schema

🎉 **Ton GPT est prêt à gérer ton stock de chaussures !**
