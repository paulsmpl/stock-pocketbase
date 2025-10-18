from typing import Optional, Dict, Any, List
from app.core.pb_client import get_pb
from app.services.fuzzy_matcher import best_match

def _expand_inventory() -> List[Dict[str, Any]]:
    pb = get_pb()
    # expand variant and product to filter in Python
    records = pb.collection("inventory").get_full_list(query_params={
        "expand": "variant,variant.product"
    })
    # convert to plain dicts
    out = []
    for r in records:
        d = r.__dict__.get('collection', r).__dict__ if hasattr(r, '__dict__') else dict(r)
        # Fallback: pocketbase Python SDK objects have .id and .get methods; use .export() if present
        try:
            d = r.export()  # newer SDKs
        except Exception:
            # basic
            d = {k: getattr(r, k, None) for k in dir(r) if not k.startswith("_")}
        out.append(d if isinstance(d, dict) else r)
    return records  # raw records are fine for attribute access

def list_inventory(model: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, gender: Optional[str] = None):
    pb = get_pb()
    records = pb.collection("inventory").get_full_list(query_params={
        "expand": "variant,variant.product"
    })
    result = []
    # Prepare choices for fuzzy on model/color if needed
    model_choices = set()
    color_choices = set()
    for rec in records:
        product = None
        if hasattr(rec, "expand") and rec.expand:
            variant = getattr(rec.expand, "variant", None)
            if variant and hasattr(variant, "expand") and variant.expand:
                product = getattr(variant.expand, "product", None)
        if product:
            if getattr(product, "name", None):
                model_choices.add(getattr(product, "name"))
            if getattr(product, "color", None):
                color_choices.add(getattr(product, "color"))
    chosen_model = model
    if model and not any(m for m in model_choices if m.lower() == model.lower()):
        m, score = best_match(model, list(model_choices))
        if m:
            chosen_model = m
    chosen_color = color
    if color and not any(c for c in color_choices if c.lower() == color.lower()):
        c, score = best_match(color, list(color_choices))
        if c:
            chosen_color = c

    for rec in records:
        variant = getattr(rec.expand, "variant", None) if hasattr(rec, "expand") and rec.expand else None
        product = getattr(variant.expand, "product", None) if variant and hasattr(variant, "expand") and variant.expand else None

        # Apply filters
        if size and variant and getattr(variant, "size", None) != size:
            continue
        if chosen_model and product and getattr(product, "name", None) != chosen_model:
            continue
        if chosen_color and product and getattr(product, "color", None) and getattr(product, "color", "").lower() != chosen_color.lower():
            continue
        if gender and product and getattr(product, "gender", None) and getattr(product, "gender", "").lower() != gender.lower():
            continue

        image_url = None
        photo = getattr(product, "photo", None) if product else None
        if product and photo:
            # build PocketBase file URL
            image_url = f"{pb.base_url}/api/files/products/{product.id}/{photo}"

        item = {
            "sku": getattr(product, "sku", None) if product else None,
            "model": getattr(product, "name", None) if product else None,
            "color": getattr(product, "color", None) if product else None,
            "gender": getattr(product, "gender", None) if product else None,
            "cost": getattr(product, "cost", None) if product else None,
            "price": getattr(product, "price", None) if product else None,
            "size": getattr(variant, "size", None) if variant else None,
            "quantity": getattr(rec, "quantity", 0),
            "reserved": getattr(rec, "reserved", 0),
            "image": image_url
        }
        result.append(item)
    return {"filters_applied": {"model": chosen_model, "color": chosen_color, "size": size, "gender": gender}, "items": result}

def _get_product_by_sku(pb, sku: str):
    recs = pb.collection("products").get_list(1, 1, query_params={"filter": f"sku='{sku}'"})
    if recs.items:
        return recs.items[0]
    return None

def _get_variant(pb, product_id: str, size: str):
    recs = pb.collection("variants").get_list(1, 1, query_params={
        "filter": f"(product='{product_id}' && size='{size}')"
    })
    return recs.items[0] if recs.items else None

def _get_or_create_inventory(pb, variant_id: str):
    recs = pb.collection("inventory").get_list(1, 1, query_params={"filter": f"variant='{variant_id}'"})
    if recs.items:
        return recs.items[0]
    # create
    inv = pb.collection("inventory").create({"variant": variant_id, "quantity": 0, "reserved": 0})
    return inv

def add_stock(sku: str, size: str, quantity: int):
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    pb = get_pb()
    product = _get_product_by_sku(pb, sku)
    if not product:
        raise ValueError("Product not found")
    variant = _get_variant(pb, product.id, size)
    if not variant:
        # auto-create variant if size doesn't exist
        variant = pb.collection("variants").create({"product": product.id, "size": size})
    inv = _get_or_create_inventory(pb, variant.id)
    new_qty = (getattr(inv, "quantity", None) or 0) + quantity
    pb.collection("inventory").update(inv.id, {"quantity": new_qty})
    pb.collection("movements").create({
        "variant": variant.id,
        "movement_type": "ADD_STOCK",
        "quantity": quantity,
        "reason": "API add_stock"
    })
    return {"sku": sku, "size": size, "quantity_added": quantity, "new_quantity": new_qty}

def sell_stock(sku: str, size: str, quantity: int):
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    pb = get_pb()
    product = _get_product_by_sku(pb, sku)
    if not product:
        raise ValueError("Product not found")
    variant = _get_variant(pb, product.id, size)
    if not variant:
        raise ValueError("Variant not found")
    inv = _get_or_create_inventory(pb, variant.id)
    current = getattr(inv, "quantity", None) or 0
    if current < quantity:
        raise ValueError("Insufficient stock")
    new_qty = current - quantity
    pb.collection("inventory").update(inv.id, {"quantity": new_qty})
    pb.collection("movements").create({
        "variant": variant.id,
        "movement_type": "SALE",
        "quantity": quantity,
        "reason": "API sale"
    })
    return {"sku": sku, "size": size, "quantity_sold": quantity, "new_quantity": new_qty}
