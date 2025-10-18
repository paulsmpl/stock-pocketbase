from fastapi import APIRouter, HTTPException
from app.core.pb_client import get_pb

router = APIRouter(prefix="/models", tags=["Models"])

@router.get("")
def list_models():
    try:
        pb = get_pb()
        recs = pb.collection("products").get_full_list()
        out = []
        for r in recs:
            d = {
                "id": r.id,
                "sku": getattr(r, "sku", None),
                "name": getattr(r, "name", None),
                "color": getattr(r, "color", None),
                "gender": getattr(r, "gender", None),
                "cost": getattr(r, "cost", None),
                "price": getattr(r, "price", None),
                "photo": getattr(r, "photo", None)
            }
            out.append(d)
        return {"items": out}
    except Exception as e:
        raise HTTPException(400, detail=str(e))
