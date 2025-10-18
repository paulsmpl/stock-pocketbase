from typing import Optional
from app.core.pb_client import get_pb
from app.services.fuzzy_matcher import best_match

def list_inventory(model=None, color=None, size=None, gender=None):
    pb = get_pb()
    records = pb.collection("inventory").get_full_list(query_params={"expand": "variant,variant.product"})
    result = []
    
    model_choices = []
    color_choices = []
    
    for rec in records:
        try:
            expand = getattr(rec, "expand", {})
            variant = getattr(expand, "variant", None)
            if variant:
                v_expand = getattr(variant, "expand", {})
                product = getattr(v_expand, "product", None)
                if product:
                    pname = getattr(product, "name", None)
                    pcolor = getattr(product, "color", None)
                    if pname and pname not in model_choices:
                        model_choices.append(pname)
                    if pcolor and pcolor not in color_choices:
                        color_choices.append(pcolor)
        except:
            pass
    
    chosen_model = model
    if model and model not in model_choices:
        exact_match = next((m for m in model_choices if m.lower() == model.lower()), None)
        if exact_match:
            chosen_model = exact_match
        else:
            m, score = best_match(model, model_choices)
            if m:
                chosen_model = m
    
    chosen_color = color
    if color and color not in color_choices:
        exact_match = next((c for c in color_choices if c.lower() == color.lower()), None)
        if exact_match:
            chosen_color = exact_match
        else:
            c, score = best_match(color, color_choices)
            if c:
                chosen_color = c

    for rec in records:
        try:
            expand = getattr(rec, "expand", {})
            variant = getattr(expand, "variant", None)
            product = None
            if variant:
                v_expand = getattr(variant, "expand", {})
                product = getattr(v_expand, "product", None)

            v_size = getattr(variant, "size", None) if variant else None
            p_name = getattr(product, "name", None) if product else None
            p_color = getattr(product, "color", None) if product else None
            p_gender = getattr(product, "gender", None) if product else None
            p_cost = getattr(product, "cost", None) if product else None
            p_price = getattr(product, "price", None) if product else None
            p_sku = getattr(product, "sku", None) if product else None
            p_photo = getattr(product, "photo", None) if product else None
            p_id = getattr(product, "id", None) if product else None
            rec_qty = getattr(rec, "quantity", 0)
            rec_reserved = getattr(rec, "reserved", 0)

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
                image_url = f"{pb.base_url}/api/files/products/{p_id}/{p_photo}"

            result.append({
                "sku": p_sku, "model": p_name, "color": p_color, "gender": p_gender,
                "cost": p_cost, "price": p_price, "size": v_size,
                "quantity": rec_qty, "reserved": rec_reserved, "image": image_url
            })
        except:
            pass
            
    return {"filters_applied": {"model": chosen_model, "color": chosen_color, "size": size, "gender": gender}, "items": result}

def _get_product_by_sku(pb, sku):
    recs = pb.collection("products").get_list(1, 1, query_params={"filter": f"sku='{sku}'"})
    return recs.items[0] if recs.items else None

def _get_variant(pb, product_id, size):
    recs = pb.collection("variants").get_list(1, 1, query_params={"filter": f"(product='{product_id}' && size='{size}')"})
    return recs.items[0] if recs.items else None

def _get_or_create_inventory(pb, variant_id):
    recs = pb.collection("inventory").get_list(1, 1, query_params={"filter": f"variant='{variant_id}'"})
    if recs.items:
        return recs.items[0]
    return pb.collection("inventory").create({"variant": variant_id, "quantity": 0, "reserved": 0})

def add_stock(sku, size, quantity):
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    pb = get_pb()
    product = _get_product_by_sku(pb, sku)
    if not product:
        raise ValueError("Product not found")
    variant = _get_variant(pb, product.id, size)
    if not variant:
        variant = pb.collection("variants").create({"product": product.id, "size": size})
    inv = _get_or_create_inventory(pb, variant.id)
    new_qty = (getattr(inv, "quantity", None) or 0) + quantity
    pb.collection("inventory").update(inv.id, {"quantity": new_qty})
    pb.collection("movements").create({"variant": variant.id, "movement_type": "ADD_STOCK", "quantity": quantity, "reason": "API add_stock"})
    return {"sku": sku, "size": size, "quantity_added": quantity, "new_quantity": new_qty}

def sell_stock(sku, size, quantity):
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
    pb.collection("movements").create({"variant": variant.id, "movement_type": "SALE", "quantity": quantity, "reason": "API sale"})
    return {"sku": sku, "size": size, "quantity_sold": quantity, "new_quantity": new_qty}
