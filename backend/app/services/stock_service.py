from typing import Optional
from app.services.fuzzy_matcher import best_match
from app.core.pocketbase_auth import authenticated_request, POCKETBASE_URL

def _extract_single(data):
    """Extrait un objet unique d'une liste ou retourne le dict directement"""
    if isinstance(data, list):
        return data[0] if data else {}
    return data if isinstance(data, dict) else {}

def list_inventory(model=None, color=None, size=None, gender=None):
    """Liste l'inventaire avec filtres optionnels et fuzzy matching"""
    
    # 1. Récupérer tous les records d'inventaire avec expand
    response = authenticated_request(
        "GET",
        f"{POCKETBASE_URL}/api/collections/inventory/records",
        params={"expand": "variant,variant.product", "perPage": 500}
    )
    data = response.json()
    
    # 2. Collecter les choix disponibles pour fuzzy matching
    model_choices = []
    color_choices = []
    
    for item in data.get("items", []):
        expand = item.get("expand", {})
        variant = _extract_single(expand.get("variant", {}))
        variant_expand = variant.get("expand", {})
        product = _extract_single(variant_expand.get("product", {}))
        
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
    
    # 4. Fuzzy matching pour la couleur avec threshold adaptatif
    chosen_color = color
    if color and color_choices and color not in color_choices:
        exact_match = next((c for c in color_choices if c.lower() == color.lower()), None)
        if exact_match:
            chosen_color = exact_match
        else:
            # Threshold plus strict pour mots courts (< 6 caractères)
            threshold = 90 if len(color) < 6 else 80
            c, score = best_match(color, color_choices, threshold=threshold)
            if c and score >= threshold:
                chosen_color = c
            else:
                # Si pas de match, ne pas filtrer par couleur
                chosen_color = None
    
    # 5. Filtrer et construire les résultats
    result = []
    for item in data.get("items", []):
        expand = item.get("expand", {})
        variant = _extract_single(expand.get("variant", {}))
        variant_expand = variant.get("expand", {})
        product = _extract_single(variant_expand.get("product", {}))
        
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


# ...existing code pour _get_product_by_sku, add_stock, sell_stock, etc...