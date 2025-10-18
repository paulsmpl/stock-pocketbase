from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.pb_client import get_pb

router = APIRouter(prefix="/movements", tags=["Movements"])

@router.get("")
def list_movements(
    sku: Optional[str] = Query(None),
    size: Optional[str] = Query(None),
    type: Optional[str] = Query(None, description="ADD_STOCK | SALE | RETURN | RESERVE | RELEASE"),
    limit: int = 50
):
    try:
        pb = get_pb()
        # build simple filter by joining conditions
        filters = []
        if type:
            filters.append(f"movement_type='{type}'")
        # We'll expand variant and product then filter in Python for sku/size
        recs = pb.collection("movements").get_list(1, limit, query_params={"expand": "variant,variant.product"})
        out = []
        for r in recs.items:
            variant = r.expand.get("variant") if r.expand else None
            product = variant.expand.get("product") if variant and variant.expand else None
            if sku and product and product.get("sku") != sku:
                continue
            if size and variant and variant.get("size") != size:
                continue
            if type and r.get("movement_type") != type:
                continue
            out.append({
                "sku": product.get("sku") if product else None,
                "size": variant.get("size") if variant else None,
                "movement_type": r.get("movement_type"),
                "quantity": r.get("quantity"),
                "timestamp": r.get("timestamp"),
                "reason": r.get("reason"),
            })
        return {"items": out}
    except Exception as e:
        raise HTTPException(400, detail=str(e))
