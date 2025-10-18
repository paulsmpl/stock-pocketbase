from typing import Optional
from app.services.fuzzy_matcher import best_match
from app.core.pocketbase_auth import authenticated_request, POCKETBASE_URL

def list_inventory(model=None, color=None, size=None, gender=None):
    """Liste l'inventaire avec filtres optionnels et fuzzy matching"""
    
    # 1. Récupérer tous les records d'inventaire avec expand
    response = authenticated_request(
        "GET",
        f"{POCKETBASE_URL}/api/collections/inventory/records",
        params={"expand": "variant,variant.product", "perPage": 500}
    )
    data = response.json()
    
    # ...existing code... (reste identique)
    
    # 2. Collecter les choix disponibles pour fuzzy matching
    model_choices = []
    color_choices = []
    
    for item in data.get("items", []):
        expand = item.get("expand", {})
        variant = expand.get("variant", {})
        variant_expand = variant.get("expand", {})
        product = variant_expand.get("product", {})
        
        p_name = product.get("name")
        p_color = product.get("color")
        
        if p_name and p_name not in model_choices:
            model_choices.append(p_name)
        if p_color and p_color not in color_choices:
            color_choices.append(p_color)
    
    # 3. Fuzzy matching pour le modèle
    chosen_model = model
    if model and model_choices and model not in model_choices:
        exact_match = next((m for m in model_choices if m.lower() == model.lower()), None)
        if exact_match:
            chosen_model = exact_match
        else:
            m, score = best_match(model, model_choices)
            if m:
                chosen_model = m
    
    # 4. Fuzzy matching pour la couleur
    chosen_color = color
    if color and color_choices and color not in color_choices:
        exact_match = next((c for c in color_choices if c.lower() == color.lower()), None)
        if exact_match:
            chosen_color = exact_match
        else:
            c, score = best_match(color, color_choices)
            if c:
                chosen_color = c
    
    # 5. Filtrer et construire les résultats
    result = []
    for item in data.get("items", []):
        expand = item.get("expand", {})
        variant = expand.get("variant", {})
        variant_expand = variant.get("expand", {})
        product = variant_expand.get("product", {})
        
        v_size = variant.get("size")
        p_name = product.get("name")
        p_color = product.get("color")
        p_gender = product.get("gender")
        p_cost = product.get("cost")
        p_price = product.get("price")
        p_sku = product.get("sku")
        p_photo = product.get("photo")
        p_id = product.get("id")
        rec_qty = item.get("quantity", 0)
        rec_reserved = item.get("reserved", 0)
        
        # Appliquer les filtres
        if size and v_size != size:
            continue
        if chosen_model and p_name != chosen_model:
            continue
        if chosen_color and p_color and p_color.lower() != chosen_color.lower():
            continue
        if gender and p_gender and p_gender.lower() != gender.lower():
            continue
        
        # Construire l'URL de l'image
        image_url = None
        if p_photo and p_id:
            image_url = f"{POCKETBASE_URL}/api/files/products/{p_id}/{p_photo}"
        
        result.append({
            "sku": p_sku,
            "model": p_name,
            "color": p_color,
            "gender": p_gender,
            "cost": p_cost,
            "price": p_price,
            "size": v_size,
            "quantity": rec_qty,
            "reserved": rec_reserved,
            "image": image_url
        })
    
    return {
        "filters_applied": {
            "model": chosen_model,
            "color": chosen_color,
            "size": size,
            "gender": gender
        },
        "items": result
    }


def _get_product_by_sku(sku):
    """Récupère un produit par SKU"""
    response = authenticated_request(
        "GET",
        f"{POCKETBASE_URL}/api/collections/products/records",
        params={"filter": f"sku='{sku}'", "perPage": 1}
    )
    data = response.json()
    items = data.get("items", [])
    return items[0] if items else None


def _get_variant(product_id, size):
    """Récupère un variant par product_id et size"""
    response = authenticated_request(
        "GET",
        f"{POCKETBASE_URL}/api/collections/variants/records",
        params={"filter": f"(product='{product_id}' && size='{size}')", "perPage": 1}
    )
    data = response.json()
    items = data.get("items", [])
    return items[0] if items else None


def _create_variant(product_id, size):
    """Crée un nouveau variant"""
    response = authenticated_request(
        "POST",
        f"{POCKETBASE_URL}/api/collections/variants/records",
        json={"product": product_id, "size": size}
    )
    return response.json()


def _get_or_create_inventory(variant_id):
    """Récupère ou crée un record d'inventaire"""
    response = authenticated_request(
        "GET",
        f"{POCKETBASE_URL}/api/collections/inventory/records",
        params={"filter": f"variant='{variant_id}'", "perPage": 1}
    )
    data = response.json()
    items = data.get("items", [])
    
    if items:
        return items[0]
    
    # Créer si n'existe pas
    response = authenticated_request(
        "POST",
        f"{POCKETBASE_URL}/api/collections/inventory/records",
        json={"variant": variant_id, "quantity": 0, "reserved": 0}
    )
    return response.json()


def _update_inventory(inventory_id, quantity):
    """Met à jour la quantité d'inventaire"""
    response = authenticated_request(
        "PATCH",
        f"{POCKETBASE_URL}/api/collections/inventory/records/{inventory_id}",
        json={"quantity": quantity}
    )
    return response.json()


def _create_movement(variant_id, movement_type, quantity, reason):
    """Crée un mouvement de stock"""
    response = authenticated_request(
        "POST",
        f"{POCKETBASE_URL}/api/collections/movements/records",
        json={
            "variant": variant_id,
            "movement_type": movement_type,
            "quantity": quantity,
            "reason": reason
        }
    )
    return response.json()


def add_stock(sku, size, quantity):
    """Ajoute du stock pour un SKU/taille"""
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    
    product = _get_product_by_sku(sku)
    if not product:
        raise ValueError("Product not found")
    
    variant = _get_variant(product["id"], size)
    if not variant:
        variant = _create_variant(product["id"], size)
    
    inv = _get_or_create_inventory(variant["id"])
    
    current = inv.get("quantity", 0)
    new_qty = current + quantity
    _update_inventory(inv["id"], new_qty)
    
    _create_movement(variant["id"], "ADD_STOCK", quantity, "API add_stock")
    
    return {
        "sku": sku,
        "size": size,
        "quantity_added": quantity,
        "new_quantity": new_qty
    }


def sell_stock(sku, size, quantity):
    """Vend du stock (réduit l'inventaire)"""
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    
    product = _get_product_by_sku(sku)
    if not product:
        raise ValueError("Product not found")
    
    variant = _get_variant(product["id"], size)
    if not variant:
        raise ValueError("Variant not found")
    
    inv = _get_or_create_inventory(variant["id"])
    
    current = inv.get("quantity", 0)
    if current < quantity:
        raise ValueError(f"Insufficient stock. Available: {current}, requested: {quantity}")
    
    new_qty = current - quantity
    _update_inventory(inv["id"], new_qty)
    
    _create_movement(variant["id"], "SALE", quantity, "API sale")
    
    return {
        "sku": sku,
        "size": size,
        "quantity_sold": quantity,
        "new_quantity": new_qty
    }