from typing import Optional
import requests
from app.core.pb_client import get_pb

POCKETBASE_URL = "http://pocketbase:8090"

def list_inventory(model=None, color=None, size=None, gender=None):
    # Récupère directement via HTTP au lieu du SDK bugué
    response = requests.get(
        f"{POCKETBASE_URL}/api/collections/inventory/records",
        params={"expand": "variant,variant.product", "perPage": 500}
    )
    data = response.json()
    
    result = []
    model_choices = set()
    color_choices = set()
    
    for item in data.get("items", []):
        expand = item.get("expand", {})
        variant = expand.get("variant", {})
        variant_expand = variant.get("expand", {})
        product = variant_expand.get("product", {})
        
        p_name = product.get("name")
        p_color = product.get("color")
        
        if p_name:
            model_choices.add(p_name)
        if p_color:
            color_choices.add(p_color)
    
    # ... reste du code de filtrage
    
    for item in data.get("items", []):
        expand = item.get("expand", {})
        variant = expand.get("variant", {})
        variant_expand = variant.get("expand", {})
        product = variant_expand.get("product", {})
        
        result.append({
            "sku": product.get("sku"),
            "model": product.get("name"),
            "color": product.get("color"),
            "gender": product.get("gender"),
            "cost": product.get("cost"),
            "price": product.get("price"),
            "size": variant.get("size"),
            "quantity": item.get("quantity", 0),
            "reserved": item.get("reserved", 0),
            "image": None  # À implémenter
        })
    
    return {"filters_applied": {}, "items": result}