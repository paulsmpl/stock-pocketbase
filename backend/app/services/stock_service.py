from typing import Optional, Dict, Any, Listfrom typing import Optional, Dict, Any, List

from app.core.pb_client import get_pbfrom app.core.pb_client import get_pb

from app.services.fuzzy_matcher import best_matchfrom app.services.fuzzy_matcher import best_match



def list_inventory(model: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, gender: Optional[str] = None):def _expand_inventory() -> List[Dict[str, Any]]:

    pb = get_pb()    pb = get_pb()

    records = pb.collection("inventory").get_full_list(query_params={    # expand variant and product to filter in Python

        "expand": "variant,variant.product"    records = pb.collection("inventory").get_full_list(query_params={

    })        "expand": "variant,variant.product"

    result = []    })

        # convert to plain dicts

    # Prepare choices for fuzzy matching on model/color    out = []

    model_choices = []    for r in records:

    color_choices = []        d = r.__dict__.get('collection', r).__dict__ if hasattr(r, '__dict__') else dict(r)

            # Fallback: pocketbase Python SDK objects have .id and .get methods; use .export() if present

    for rec in records:        try:

        try:            d = r.export()  # newer SDKs

            expand = getattr(rec, "expand", {})        except Exception:

            variant = expand.get("variant") if isinstance(expand, dict) else getattr(expand, "variant", None)            # basic

                        d = {k: getattr(r, k, None) for k in dir(r) if not k.startswith("_")}

            if variant:        out.append(d if isinstance(d, dict) else r)

                v_expand = getattr(variant, "expand", {})    return records  # raw records are fine for attribute access

                product = v_expand.get("product") if isinstance(v_expand, dict) else getattr(v_expand, "product", None)

                def list_inventory(model: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, gender: Optional[str] = None):

                if product:    pb = get_pb()

                    pname = getattr(product, "name", None)    records = pb.collection("inventory").get_full_list(query_params={

                    pcolor = getattr(product, "color", None)        "expand": "variant,variant.product"

                    if pname and pname not in model_choices:    })

                        model_choices.append(pname)    result = []

                    if pcolor and pcolor not in color_choices:    # Prepare choices for fuzzy on model/color if needed

                        color_choices.append(pcolor)    model_choices = []

        except Exception:    color_choices = []

            pass    

        for rec in records:

    # Fuzzy matching for model        try:

    chosen_model = model            # Access expand - could be dict or object

    if model and model not in model_choices:            expand = getattr(rec, "expand", {})

        # Check case-insensitive exact match first            variant = expand.get("variant") if isinstance(expand, dict) else getattr(expand, "variant", None)

        exact_match = next((m for m in model_choices if m.lower() == model.lower()), None)            

        if exact_match:            if variant:

            chosen_model = exact_match                v_expand = getattr(variant, "expand", {})

        else:                product = v_expand.get("product") if isinstance(v_expand, dict) else getattr(v_expand, "product", None)

            # Use fuzzy matching                

            m, score = best_match(model, model_choices)                if product:

            if m:                    pname = getattr(product, "name", None)

                chosen_model = m                    pcolor = getattr(product, "color", None)

                        if pname and pname not in model_choices:

    # Fuzzy matching for color                        model_choices.append(pname)

    chosen_color = color                    if pcolor and pcolor not in color_choices:

    if color and color not in color_choices:                        color_choices.append(pcolor)

        # Check case-insensitive exact match first        except Exception:

        exact_match = next((c for c in color_choices if c.lower() == color.lower()), None)            pass

        if exact_match:    

            chosen_color = exact_match    chosen_model = model

        else:    if model and model not in model_choices:

            # Use fuzzy matching        # Check case-insensitive exact match first

            c, score = best_match(color, color_choices)        exact_match = next((m for m in model_choices if m.lower() == model.lower()), None)

            if c:        if exact_match:

                chosen_color = c            chosen_model = exact_match

        else:

    # Filter and build result            # Use fuzzy matching

    for rec in records:            m, score = best_match(model, model_choices)

        try:            if m:

            expand = getattr(rec, "expand", {})                chosen_model = m

            variant = expand.get("variant") if isinstance(expand, dict) else getattr(expand, "variant", None)    

            product = None    chosen_color = color

                if color and color not in color_choices:

            if variant:        # Check case-insensitive exact match first

                v_expand = getattr(variant, "expand", {})        exact_match = next((c for c in color_choices if c.lower() == color.lower()), None)

                product = v_expand.get("product") if isinstance(v_expand, dict) else getattr(v_expand, "product", None)        if exact_match:

            chosen_color = exact_match

            # Get values safely with getattr        else:

            v_size = getattr(variant, "size", None) if variant else None            # Use fuzzy matching

            p_name = getattr(product, "name", None) if product else None            c, score = best_match(color, color_choices)

            p_color = getattr(product, "color", None) if product else None            if c:

            p_gender = getattr(product, "gender", None) if product else None                chosen_color = c

            p_cost = getattr(product, "cost", None) if product else None

            p_price = getattr(product, "price", None) if product else None    for rec in records:

            p_sku = getattr(product, "sku", None) if product else None        try:

            p_photo = getattr(product, "photo", None) if product else None            # Access expand - could be dict or object

            p_id = getattr(product, "id", None) if product else None            for rec in records:

                    try:

            rec_qty = getattr(rec, "quantity", 0)            # Access expand - could be dict or object

            rec_reserved = getattr(rec, "reserved", 0)            expand = getattr(rec, "expand", {})

            variant = expand.get("variant") if isinstance(expand, dict) else getattr(expand, "variant", None)

            # Apply filters            product = None

            if size and v_size != size:            

                continue            if variant:

            if chosen_model and p_name != chosen_model:                v_expand = getattr(variant, "expand", {})

                continue                product = v_expand.get("product") if isinstance(v_expand, dict) else getattr(v_expand, "product", None)

            if chosen_color and p_color and p_color.lower() != chosen_color.lower():

                continue            # Get values safely with getattr

            if gender and p_gender and p_gender.lower() != gender.lower():            v_size = getattr(variant, "size", None) if variant else None

                continue            p_name = getattr(product, "name", None) if product else None

            p_color = getattr(product, "color", None) if product else None

            image_url = None            p_gender = getattr(product, "gender", None) if product else None

            if product and p_photo:            p_cost = getattr(product, "cost", None) if product else None

                # build PocketBase file URL            p_price = getattr(product, "price", None) if product else None

                image_url = f"{pb.base_url}/api/files/products/{p_id}/{p_photo}"            p_sku = getattr(product, "sku", None) if product else None

            p_photo = getattr(product, "photo", None) if product else None

            item = {            p_id = getattr(product, "id", None) if product else None

                "sku": p_sku,            

                "model": p_name,            rec_qty = getattr(rec, "quantity", 0)

                "color": p_color,            rec_reserved = getattr(rec, "reserved", 0)

                "gender": p_gender,

                "cost": p_cost,            # Apply filters

                "price": p_price,            if size and v_size != size:

                "size": v_size,                continue

                "quantity": rec_qty,            if chosen_model and p_name != chosen_model:

                "reserved": rec_reserved,                continue

                "image": image_url            if chosen_color and p_color and p_color.lower() != chosen_color.lower():

            }                continue

            result.append(item)            if gender and p_gender and p_gender.lower() != gender.lower():

        except Exception:                continue

            pass

                        image_url = None

    return {"filters_applied": {"model": chosen_model, "color": chosen_color, "size": size, "gender": gender}, "items": result}            if product and p_photo:

                # build PocketBase file URL

def _get_product_by_sku(pb, sku: str):                image_url = f"{pb.base_url}/api/files/products/{p_id}/{p_photo}"

    recs = pb.collection("products").get_list(1, 1, query_params={"filter": f"sku='{sku}'"})

    if recs.items:            item = {

        return recs.items[0]                "sku": p_sku,

    return None                "model": p_name,

                "color": p_color,

def _get_variant(pb, product_id: str, size: str):                "gender": p_gender,

    recs = pb.collection("variants").get_list(1, 1, query_params={                "cost": p_cost,

        "filter": f"(product='{product_id}' && size='{size}')"                "price": p_price,

    })                "size": v_size,

    return recs.items[0] if recs.items else None                "quantity": rec_qty,

                "reserved": rec_reserved,

def _get_or_create_inventory(pb, variant_id: str):                "image": image_url

    recs = pb.collection("inventory").get_list(1, 1, query_params={"filter": f"variant='{variant_id}'"})            }

    if recs.items:            result.append(item)

        return recs.items[0]        except Exception:

    # create            pass

    inv = pb.collection("inventory").create({"variant": variant_id, "quantity": 0, "reserved": 0})            

    return inv    return {"filters_applied": {"model": chosen_model, "color": chosen_color, "size": size, "gender": gender}, "items": result}



def add_stock(sku: str, size: str, quantity: int):def _get_product_by_sku(pb, sku: str):

    if quantity <= 0:    recs = pb.collection("products").get_list(1, 1, query_params={"filter": f"sku='{sku}'"})

        raise ValueError("quantity must be > 0")    if recs.items:

    pb = get_pb()        return recs.items[0]

    product = _get_product_by_sku(pb, sku)    return None

    if not product:

        raise ValueError("Product not found")def _get_variant(pb, product_id: str, size: str):

    variant = _get_variant(pb, product.id, size)    recs = pb.collection("variants").get_list(1, 1, query_params={

    if not variant:        "filter": f"(product='{product_id}' && size='{size}')"

        # auto-create variant if size doesn't exist    })

        variant = pb.collection("variants").create({"product": product.id, "size": size})    return recs.items[0] if recs.items else None

    inv = _get_or_create_inventory(pb, variant.id)

    new_qty = (getattr(inv, "quantity", None) or 0) + quantitydef _get_or_create_inventory(pb, variant_id: str):

    pb.collection("inventory").update(inv.id, {"quantity": new_qty})    recs = pb.collection("inventory").get_list(1, 1, query_params={"filter": f"variant='{variant_id}'"})

    pb.collection("movements").create({    if recs.items:

        "variant": variant.id,        return recs.items[0]

        "movement_type": "ADD_STOCK",    # create

        "quantity": quantity,    inv = pb.collection("inventory").create({"variant": variant_id, "quantity": 0, "reserved": 0})

        "reason": "API add_stock"    return inv

    })

    return {"sku": sku, "size": size, "quantity_added": quantity, "new_quantity": new_qty}def add_stock(sku: str, size: str, quantity: int):

    if quantity <= 0:

def sell_stock(sku: str, size: str, quantity: int):        raise ValueError("quantity must be > 0")

    if quantity <= 0:    pb = get_pb()

        raise ValueError("quantity must be > 0")    product = _get_product_by_sku(pb, sku)

    pb = get_pb()    if not product:

    product = _get_product_by_sku(pb, sku)        raise ValueError("Product not found")

    if not product:    variant = _get_variant(pb, product.id, size)

        raise ValueError("Product not found")    if not variant:

    variant = _get_variant(pb, product.id, size)        # auto-create variant if size doesn't exist

    if not variant:        variant = pb.collection("variants").create({"product": product.id, "size": size})

        raise ValueError("Variant not found")    inv = _get_or_create_inventory(pb, variant.id)

    inv = _get_or_create_inventory(pb, variant.id)    new_qty = (getattr(inv, "quantity", None) or 0) + quantity

    current = getattr(inv, "quantity", None) or 0    pb.collection("inventory").update(inv.id, {"quantity": new_qty})

    if current < quantity:    pb.collection("movements").create({

        raise ValueError("Insufficient stock")        "variant": variant.id,

    new_qty = current - quantity        "movement_type": "ADD_STOCK",

    pb.collection("inventory").update(inv.id, {"quantity": new_qty})        "quantity": quantity,

    pb.collection("movements").create({        "reason": "API add_stock"

        "variant": variant.id,    })

        "movement_type": "SALE",    return {"sku": sku, "size": size, "quantity_added": quantity, "new_quantity": new_qty}

        "quantity": quantity,

        "reason": "API sale"def sell_stock(sku: str, size: str, quantity: int):

    })    if quantity <= 0:

    return {"sku": sku, "size": size, "quantity_sold": quantity, "new_quantity": new_qty}        raise ValueError("quantity must be > 0")

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
