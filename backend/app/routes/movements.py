from fastapi import APIRouter
from app.core.pocketbase_auth import authenticated_request, POCKETBASE_URL

router = APIRouter(prefix="/movements", tags=["Movements"])

@router.get("")
def list_movements(sku: str = None, limit: int = 100):
    """Liste les mouvements de stock avec filtre optionnel par SKU"""
    
    params = {
        "expand": "variant,variant.product",
        "perPage": limit,
        "sort": "-created"
    }
    
    if sku:
        product_response = authenticated_request(
            "GET",
            f"{POCKETBASE_URL}/api/collections/products/records",
            params={"filter": f"sku='{sku}'", "perPage": 1}
        )
        product_data = product_response.json()
        
        if not product_data.get("items"):
            return {"movements": []}
        
        product_id = product_data["items"][0]["id"]
        
        variants_response = authenticated_request(
            "GET",
            f"{POCKETBASE_URL}/api/collections/variants/records",
            params={"filter": f"product='{product_id}'", "perPage": 500}
        )
        variants_data = variants_response.json()
        
        variant_ids = [v["id"] for v in variants_data.get("items", [])]
        
        if not variant_ids:
            return {"movements": []}
        
        variant_filter = " || ".join([f"variant='{vid}'" for vid in variant_ids])
        params["filter"] = f"({variant_filter})"
    
    response = authenticated_request(
        "GET",
        f"{POCKETBASE_URL}/api/collections/movements/records",
        params=params
    )
    data = response.json()
    
    movements = []
    for item in data.get("items", []):
        expand = item.get("expand", {})
        variant = expand.get("variant", {})
        variant_expand = variant.get("expand", {})
        product = variant_expand.get("product", {})
        
        movements.append({
            "id": item.get("id"),
            "sku": product.get("sku"),
            "model": product.get("name"),
            "size": variant.get("size"),
            "movement_type": item.get("movement_type"),
            "quantity": item.get("quantity"),
            "reason": item.get("reason"),
            "created": item.get("created"),
            "updated": item.get("updated")
        })
    
    return {"movements": movements}