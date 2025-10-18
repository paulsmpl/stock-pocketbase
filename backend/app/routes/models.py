from fastapi import APIRouter
from app.core.pocketbase_auth import authenticated_request, POCKETBASE_URL

router = APIRouter(prefix="/models", tags=["Models"])

@router.get("")
def list_models():
    """Liste tous les modèles disponibles avec leurs variantes"""
    response = authenticated_request(
        "GET",
        f"{POCKETBASE_URL}/api/collections/products/records",
        params={"perPage": 500}
    )
    data = response.json()
    
    models = {}
    for product in data.get("items", []):
        name = product.get("name")
        if name:
            if name not in models:
                models[name] = {
                    "name": name,
                    "colors": set(),
                    "genders": set()
                }
            color = product.get("color")
            gender = product.get("gender")
            if color:
                models[name]["colors"].add(color)
            if gender:
                models[name]["genders"].add(gender)
    
    result = []
    for model in models.values():
        result.append({
            "name": model["name"],
            "colors": sorted(list(model["colors"])),
            "genders": sorted(list(model["genders"]))
        })
    
    return {"models": sorted(result, key=lambda x: x["name"])}