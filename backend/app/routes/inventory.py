from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.stock_service import add_stock, sell_stock, list_inventory

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("")
def inventory_route(
    model: Optional[str] = Query(default=None, description="Nom du modèle (optionnel)"),
    color: Optional[str] = Query(default=None, description="Couleur (optionnel)"),
    size: Optional[str] = Query(default=None, description="Pointure/taille (optionnel)"),
    gender: Optional[str] = Query(default=None, description="Sexe (homme/femme/mixte, optionnel)"),
):
    try:
        return list_inventory(model=model, color=color, size=size, gender=gender)
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@router.post("/add_stock")
def add_stock_route(sku: str, size: str, quantity: int):
    try:
        return add_stock(sku, size, quantity)
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@router.post("/sale")
def sale_route(sku: str, size: str, quantity: int):
    try:
        return sell_stock(sku, size, quantity)
    except Exception as e:
        raise HTTPException(400, detail=str(e))