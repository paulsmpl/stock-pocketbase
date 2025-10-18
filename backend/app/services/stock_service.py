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
        try:
            # Access expand - could be dict or object
            expand = rec.expand if hasattr(rec, "expand") else {}
            variant = expand.get("variant") if isinstance(expand, dict) else getattr(expand, "variant", None)
            
            if variant:
                v_expand = variant.expand if hasattr(variant, "expand") else {}
                product = v_expand.get("product") if isinstance(v_expand, dict) else getattr(v_expand, "product", None)
                
                if product:
                    pname = product.get("name") if isinstance(product, dict) else getattr(product, "name", None)
                    pcolor = product.get("color") if isinstance(product, dict) else getattr(product, "color", None)
                    if pname:
                        model_choices.add(pname)
                    if pcolor:
                        color_choices.add(pcolor)
        except Exception:
            pass
    
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
        try:
            # Access expand - could be dict or object
            expand = rec.expand if hasattr(rec, "expand") else {}
            variant = expand.get("variant") if isinstance(expand, dict) else getattr(expand, "variant", None)
            product = None
            
            if variant:
                v_expand = variant.expand if hasattr(variant, "expand") else {}
                product = v_expand.get("product") if isinstance(v_expand, dict) else getattr(v_expand, "product", None)

            # Get values safely
            v_size = variant.get("size") if isinstance(variant, dict) else getattr(variant, "size", None) if variant else None
            p_name = product.get("name") if isinstance(product, dict) else getattr(product, "name", None) if product else None
            p_color = product.get("color") if isinstance(product, dict) else getattr(product, "color", None) if product else None
            p_gender = product.get("gender") if isinstance(product, dict) else getattr(product, "gender", None) if product else None
            p_cost = product.get("cost") if isinstance(product, dict) else getattr(product, "cost", None) if product else None
            p_price = product.get("price") if isinstance(product, dict) else getattr(product, "price", None) if product else None
            p_sku = product.get("sku") if isinstance(product, dict) else getattr(product, "sku", None) if product else None
            p_photo = product.get("photo") if isinstance(product, dict) else getattr(product, "photo", None) if product else None
            p_id = product.get("id") if isinstance(product, dict) else getattr(product, "id", None) if product else None
            
            rec_qty = rec.get("quantity") if isinstance(rec, dict) else getattr(rec, "quantity", 0)
            rec_reserved = rec.get("reserved") if isinstance(rec, dict) else getattr(rec, "reserved", 0)

            # Apply filters
            if size and v_size != size:
                continue
            if chosen_model and p_name != chosen_model:
                continue
            if chosen_color and p_color and p_color.lower() != chosen_color.lower():
                continue
            if gender and p_gender and p_gender.lower() != gender.lower():
                continue

            image_url = None
            if product and p_photo:
                # build PocketBase file URL
                image_url = f"{pb.base_url}/api/files/products/{p_id}/{p_photo}"

            item = {
                "sku": p_sku,
                "model": p_name,
                "color": p_color,
                "gender": p_gender,
                "cost": p_cost,
                "price": p_price,
                "size": v_size,
                "quantity": rec_qty,
                "reserved": rec_reserved,
                "image": image_url
            }
            result.append(item)
        except Exception:
            pass
            
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
