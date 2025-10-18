from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.stock_service import add_stock, sell_stock, list_inventory
import traceback
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("")
def inventory_route(
    model: Optional[str] = Query(default=None, description="Nom du modèle (optionnel)"),
    color: Optional[str] = Query(default=None, description="Couleur (optionnel)"),
    size: Optional[str] = Query(default=None, description="Pointure/taille (optionnel)"),
    gender: Optional[str] = Query(default=None, description="Sexe (homme/femme/mixte, optionnel)"),
):
    try:
        logger.info(f"📞 Inventory called with: model={model}, color={color}, size={size}, gender={gender}")
        result = list_inventory(model=model, color=color, size=size, gender=gender)
        logger.info(f"✅ Result type: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
        logger.info(f"✅ Result content (first 200 chars): {str(result)[:200]}")
        return result
    except Exception as e:
        logger.error(f"🔥 ERROR in inventory_route:")
        logger.error(f"Type: {type(e).__name__}")
        logger.error(f"Message: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(400, detail=f"{type(e).__name__}: {str(e)}")

@router.post("/add_stock")
def add_stock_route(sku: str, size: str, quantity: int):
    try:
        return add_stock(sku, size, quantity)
    except Exception as e:
        logger.error(f"🔥 Error in add_stock: {traceback.format_exc()}")
        raise HTTPException(400, detail=str(e))

@router.post("/sale")
def sale_route(sku: str, size: str, quantity: int):
    try:
        return sell_stock(sku, size, quantity)
    except Exception as e:
        logger.error(f"🔥 Error in sale: {traceback.format_exc()}")
        raise HTTPException(400, detail=str(e))