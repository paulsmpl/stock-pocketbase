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
                "sku": r.get("sku"),
                "name": r.get("name"),
                "color": r.get("color"),
                "gender": r.get("gender"),
                "cost": r.get("cost"),
                "price": r.get("price"),
                "photo": r.get("photo")
            }
            out.append(d)
        return {"items": out}
    except Exception as e:
        raise HTTPException(400, detail=str(e))
