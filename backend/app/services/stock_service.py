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
        product = rec.expand.get("variant").expand.get("product") if rec.expand and rec.expand.get("variant") else None
        if product:
            if product.get("name"):
                model_choices.add(product["name"])
            if product.get("color"):
                color_choices.add(product["color"])
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
        variant = rec.expand.get("variant") if rec.expand else None
        product = variant.expand.get("product") if variant and variant.expand else None

        # Apply filters
        if size and variant and variant.get("size") != size:
            continue
        if chosen_model and product and product.get("name") != chosen_model:
            continue
        if chosen_color and product and product.get("color") and product.get("color").lower() != chosen_color.lower():
            continue
        if gender and product and product.get("gender") and product.get("gender").lower() != gender.lower():
            continue

        image_url = None
        if product and product.get("photo"):
            # build PocketBase file URL
            image_url = f"{pb.base_url}/api/files/products/{product['id']}/{product['photo']}"

        item = {
            "sku": product.get("sku") if product else None,
            "model": product.get("name") if product else None,
            "color": product.get("color") if product else None,
            "gender": product.get("gender") if product else None,
            "size": variant.get("size") if variant else None,
            "quantity": rec.get("quantity"),
            "reserved": rec.get("reserved", 0),
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
    new_qty = (inv.get("quantity") or 0) + quantity
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
    current = inv.get("quantity") or 0
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
