#!/usr/bin/env python3
"""Import WooCommerce customers and orders into Shopify as historical records.

Usage (from the repo root):

  python3 -I migration/orders/woo_shopify_import.py plan  data/woo-export-test.json
  python3 -I migration/orders/woo_shopify_import.py run   data/woo-export-test.json [--limit N] [--dry-run]

  (paths to the export are relative to migration/orders/)

The export is JSON shaped {"orders": [...Woo REST v3 orders...], "customers": [...Woo REST v3 customers...]}.
It holds personal data, so it lives in migration/orders/data/, which is git-ignored.

What it does, per Woo order (oldest first):
  1. Customer: find the Shopify customer by email. If there is none, create one from the Woo customer
     record (registered) or the order's billing details (guest). Existing Shopify customers are left as
     they are apart from a `woo-import` tag. Nobody is subscribed to marketing.
  2. Order: skip it if `#W<number>` already exists in Shopify, otherwise create it with orderCreate:
     original date, archived, paid, fulfilled, VAT-inclusive prices, discount code, shipping, linked to
     the customer. No receipt or shipping emails and no stock movement.
  3. Check Shopify's order total and tax against Woo's, and log the result.

Talks to the Admin API as a private app (orderCreate requires an app's offline token). Put the app's
access token in data/admin-token, or its client ID and secret in data/app-credentials.json. The app needs
write_orders, read_all_orders, write_customers and read_products. Without either file it falls back to
`shopify store execute`, which can read and create customers but cannot create orders.
"""

import argparse
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, ROUND_HALF_UP

STORE = "melt-co-uk-maqm6c3j.myshopify.com"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
STATE_FILE = os.path.join(DATA, "import-state.json")
LOG_FILE = os.path.join(DATA, "import-log.jsonl")

IMPORT_TAG = "woo-import"
ORDER_PREFIX = "#W"

# Woo order statuses this script knows how to import. Others are skipped and reported.
SUPPORTED_STATUSES = {"completed", "processing"}

# Woo variation name -> Shopify product title suffix ("<Fragrance> <suffix>").
TYPE_MAP = {
    "tall & thin": "Tall & Thin",
    "short & fat": "Short & Fat",
    "tall & fat": "Tall & Fat",
    "luxury glass jar": "Luxury Glass Jar",
    "luxury jar": "Luxury Glass Jar",
    "room scenter": "Room Scenter",
    "travel candle": "Travel Tin",
    "scented truffles": "12 Pack",
    "scent truffle": "12 Pack",
}

# Whole Woo products that map to one Shopify product, by Woo product ID.
PRODUCT_MAP = {
    5232: "Christmas Hamper",
    5495: "Wax Sample Selection",
    5548: "Gift Voucher",
}

TWO = Decimal("0.01")


def money(x):
    return Decimal(str(x or "0")).quantize(TWO, rounding=ROUND_HALF_UP)


def mset(amount):
    return {"shopMoney": {"amount": str(money(amount)), "currencyCode": "GBP"}}


def iso(gmt):
    return gmt + "Z" if gmt and not gmt.endswith("Z") else gmt


def clean(s):
    return html.unescape(s or "").strip()


def norm(s):
    s = clean(s).lower().replace(" and ", " & ")
    return re.sub(r"\s+", " ", s)


# --------------------------------------------------------------------------- Shopify transport

API_VERSION = "2026-10"
TOKEN_FILE = os.path.join(DATA, "admin-token")             # an Admin API access token (shpat_...)
CREDENTIALS_FILE = os.path.join(DATA, "app-credentials.json")  # {"client_id": "...", "client_secret": "..."}
_token = {"value": None, "expires": 0}


def app_token():
    """Admin API token from a private app, or None to fall back to the Shopify CLI.

    orderCreate only works with an app's offline token, not the CLI's online user token.
    Put either an access token in data/admin-token, or a Dev Dashboard app's client ID and
    secret in data/app-credentials.json (exchanged for a 24-hour token). Both files are git-ignored.
    """
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    if _token["value"] and _token["expires"] > dt.datetime.now().timestamp() + 300:
        return _token["value"]
    with open(CREDENTIALS_FILE) as f:
        creds = json.load(f)
    if not (creds.get("client_id") and creds.get("client_secret")):
        return None
    body = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": creds["client_id"],
                                   "client_secret": creds["client_secret"]}).encode()
    req = urllib.request.Request(f"https://{STORE}/admin/oauth/access_token", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    _token["value"] = d["access_token"]
    _token["expires"] = dt.datetime.now().timestamp() + int(d.get("expires_in", 86399))
    return _token["value"]


def gql(query, variables=None, mutate=False):
    token = app_token()
    if token:
        return gql_http(token, query, variables)
    return gql_cli(query, variables, mutate)


def gql_http(token, query, variables, attempt=0):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(f"https://{STORE}/admin/api/{API_VERSION}/graphql.json", data=body,
                                 headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (429, 502, 503, 504) and attempt < 5:
            time.sleep(2 ** attempt)
            return gql_http(token, query, variables, attempt + 1)
        raise RuntimeError(f"HTTP {e.code}: {e.read()[:500]!r}")
    errors = data.get("errors") or []
    if any((er.get("extensions") or {}).get("code") == "THROTTLED" for er in errors) and attempt < 8:
        time.sleep(2)
        return gql_http(token, query, variables, attempt + 1)
    if errors:
        raise RuntimeError(f"GraphQL errors: {json.dumps(errors)[:800]}")
    # Stay well inside the cost bucket.
    throttle = ((data.get("extensions") or {}).get("cost") or {}).get("throttleStatus") or {}
    if throttle.get("currentlyAvailable", 1000) < 200:
        time.sleep(3)
    return data["data"]


def gql_cli(query, variables=None, mutate=False):
    with tempfile.TemporaryDirectory() as tmp:
        qf = os.path.join(tmp, "q.graphql")
        with open(qf, "w") as f:
            f.write(query)
        cmd = ["shopify", "store", "execute", "-s", STORE, "--no-input", "-j", "--query-file", qf]
        if variables is not None:
            vf = os.path.join(tmp, "v.json")
            with open(vf, "w") as f:
                json.dump(variables, f)
            cmd += ["--variable-file", vf]
        if mutate:
            cmd.append("--allow-mutations")
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    text = out.stdout
    lines = [l for l in text.splitlines() if '"type":"progress"' not in l]
    text = "\n".join(lines)
    if "{" not in text:
        raise RuntimeError(f"No JSON from Shopify CLI: {out.stdout[-500:]} {out.stderr[-500:]}")
    data, _ = json.JSONDecoder().raw_decode(text[text.index("{"):])
    if "error" in data:  # the CLI's own failure wrapper
        detail = (data["error"].get("details") or {}).get("errors") or data["error"].get("message")
        raise RuntimeError(f"Shopify CLI: {json.dumps(detail)[:800]}")
    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {json.dumps(data['errors'])[:800]}")
    return data["data"]


# --------------------------------------------------------------------------- product matching

def load_shopify_products():
    q = """query($after:String){ products(first:250, after:$after){ pageInfo{hasNextPage endCursor}
           nodes{ id title variants(first:50){ nodes{ id title price } } } } }"""
    products, after = [], None
    while True:
        d = gql(q, {"after": after})["products"]
        products += d["nodes"]
        if not d["pageInfo"]["hasNextPage"]:
            return products
        after = d["pageInfo"]["endCursor"]


def build_matcher(products):
    by_title = {norm(p["title"]): p for p in products}

    def match(li):
        """Return (variantId, productTitle) or (None, None) for a custom line item."""
        name = clean(li["name"])
        title = None
        if li["product_id"] in PRODUCT_MAP:
            title = PRODUCT_MAP[li["product_id"]]
        elif " - " in name:
            frag, typ = name.rsplit(" - ", 1)
            suffix = TYPE_MAP.get(norm(typ))
            if suffix:
                title = f"{frag} {suffix}"
        else:
            title = name  # e.g. "Angel Reed Diffuser"
        p = by_title.get(norm(title)) if title else None
        if not p:
            return None, None
        variants = p["variants"]["nodes"]
        if len(variants) == 1:
            return variants[0]["id"], p["title"]
        # Multi-variant product (Gift Voucher): match on the Woo variation's value, e.g. "£50".
        wanted = " ".join(clean(m.get("display_value", "")) for m in li.get("meta_data", []) if not m["key"].startswith("_"))
        for v in variants:
            if norm(v["title"]) and norm(v["title"]) in norm(wanted):
                return v["id"], p["title"]
        return None, None

    return match


# --------------------------------------------------------------------------- Woo -> Shopify inputs

def address(a, fallback_phone=None):
    if not a or not (a.get("address_1") or a.get("postcode")):
        return None
    out = {
        "firstName": clean(a.get("first_name")),
        "lastName": clean(a.get("last_name")),
        "company": clean(a.get("company")),
        "address1": clean(a.get("address_1")),
        "address2": clean(a.get("address_2")),
        "city": clean(a.get("city")),
        "zip": clean(a.get("postcode")).upper(),
        "countryCode": (a.get("country") or "GB").upper(),
        "phone": clean(a.get("phone") or fallback_phone or ""),
    }
    return {k: v for k, v in out.items() if v}


def same_address(a, b):
    keys = ("address1", "address2", "city", "zip", "countryCode")
    return a and b and all((a.get(k) or "").lower() == (b.get(k) or "").lower() for k in keys)


def customer_input(order, woo_customer):
    src = woo_customer or {}
    billing = src.get("billing") or order["billing"]
    shipping = src.get("shipping") or order["shipping"]
    email = (src.get("email") or order["billing"].get("email") or "").strip().lower()
    bill = address(billing)
    ship = address(shipping, billing.get("phone"))
    addresses = [a for a in (ship, bill) if a]
    if len(addresses) == 2 and same_address(*addresses):
        addresses = addresses[:1]
    if woo_customer:
        created = woo_customer["date_created"][:10]
        note = f"Imported from WooCommerce: registered customer #{woo_customer['id']}, joined {created}."
    else:
        note = "Imported from WooCommerce: guest checkout customer."
    return {
        "email": email,
        "firstName": clean(src.get("first_name") or billing.get("first_name")),
        "lastName": clean(src.get("last_name") or billing.get("last_name")),
        "note": note,
        "tags": [IMPORT_TAG],
        "addresses": addresses,
    }


def tax_lines(amount, rate):
    amount = money(amount)
    if amount == 0:
        return []
    return [{"title": "VAT", "rate": str(rate), "priceSet": mset(amount)}]


def order_input(order, customer_id, match):
    """Build OrderCreateOrderInput. Returns (input, notes)."""
    notes = []
    incl = bool(order["prices_include_tax"])
    rate = Decimal("0.2")
    if order["tax_lines"]:
        rate = (Decimal(str(order["tax_lines"][0]["rate_percent"])) / 100).normalize()

    lines = []
    for li in order["line_items"]:
        qty = int(li["quantity"])
        gross = money(li["subtotal"]) + (money(li["subtotal_tax"]) if incl else 0)
        unit = (gross / qty).quantize(TWO, rounding=ROUND_HALF_UP)
        if unit * qty != gross:
            notes.append(f"unit price rounding on '{clean(li['name'])}': {gross}/{qty}")
        variant_id, ptitle = match(li)
        item = {
            "quantity": qty,
            "priceSet": mset(unit),
            "taxLines": tax_lines(li["total_tax"], rate),
            "taxable": money(li["total_tax"]) > 0,
            "requiresShipping": True,
        }
        if variant_id:
            item["variantId"] = variant_id
        else:
            item["title"] = clean(li["name"])
            if li.get("sku"):
                item["sku"] = li["sku"]
            notes.append(f"no Shopify product for '{clean(li['name'])}': imported as a custom line item")
        lines.append(item)

    for fee in order.get("fee_lines", []):
        gross = money(fee["total"]) + (money(fee["total_tax"]) if incl else 0)
        lines.append({"title": clean(fee["name"]), "quantity": 1, "priceSet": mset(gross),
                      "taxLines": tax_lines(fee["total_tax"], rate), "requiresShipping": False})
        notes.append(f"fee line '{clean(fee['name'])}' imported as a custom line item")

    shipping = []
    for s in order["shipping_lines"]:
        gross = money(s["total"]) + (money(s["total_tax"]) if incl else 0)
        shipping.append({"title": clean(s["method_title"]) or "Shipping", "code": s.get("method_id") or None,
                         "priceSet": mset(gross), "taxLines": tax_lines(s["total_tax"], rate)})

    discount = None
    # Discount = what the lines lost between subtotal and total. Woo's discount_total + discount_tax
    # are rounded separately and can be 1p out from what the customer actually paid.
    disc_total = sum(
        (money(li["subtotal"]) - money(li["total"])) + ((money(li["subtotal_tax"]) - money(li["total_tax"])) if incl else 0)
        for li in order["line_items"]
    )
    codes = [c["code"] for c in order["coupon_lines"]]
    if disc_total > 0:
        discount = {"itemFixedDiscountCode": {"code": ", ".join(codes) or "Discount", "amountSet": mset(disc_total)}}

    created = iso(order["date_created_gmt"])
    paid_at = iso(order.get("date_paid_gmt")) or created
    closed = iso(order.get("date_completed_gmt")) or created
    billing = address(order["billing"])
    ship_addr = address(order["shipping"], order["billing"].get("phone")) or billing

    attrs = [{"key": "WooCommerce order", "value": str(order["number"])}]
    if order.get("payment_method_title"):
        # Drop card digits ("Visa ending in 1234" -> "Visa").
        attrs.append({"key": "Paid with", "value": re.sub(r"\s+ending in\s+\d+", "", clean(order["payment_method_title"]))})

    inp = {
        "name": f"{ORDER_PREFIX}{order['number']}",
        "sourceIdentifier": f"woo-{order['id']}",
        "email": (order["billing"].get("email") or "").strip().lower() or None,
        "processedAt": created,
        "closedAt": closed,
        "currency": order["currency"],
        "taxesIncluded": incl,
        "buyerAcceptsMarketing": False,
        "customer": {"toAssociate": {"id": customer_id}} if customer_id else None,
        "billingAddress": billing,
        "shippingAddress": ship_addr,
        "lineItems": lines,
        "shippingLines": shipping,
        "discountCode": discount,
        "fulfillmentStatus": "FULFILLED",
        "transactions": [{
            "kind": "SALE", "status": "SUCCESS", "gateway": order.get("payment_method") or "manual",
            "amountSet": mset(order["total"]), "processedAt": paid_at,
        }],
        "tags": [IMPORT_TAG],
        "customAttributes": attrs,
        "note": f"Customer note on the WooCommerce order: {clean(order['customer_note'])}" if order.get("customer_note") else None,
    }
    return {k: v for k, v in inp.items() if v not in (None, [], "")}, notes


# --------------------------------------------------------------------------- Shopify operations

Q_FIND_CUSTOMER = """query($q:String!){ customers(first:5, query:$q){ nodes{ id email tags } } }"""
M_CREATE_CUSTOMER = """mutation($input:CustomerInput!){ customerCreate(input:$input){
  customer{ id } userErrors{ field message } } }"""
M_TAGS_ADD = """mutation($id:ID!,$tags:[String!]!){ tagsAdd(id:$id, tags:$tags){ userErrors{ field message } } }"""
Q_FIND_ORDER = """query($q:String!){ orders(first:5, query:$q){ nodes{ id name } } }"""
M_CREATE_ORDER = """mutation($order:OrderCreateOrderInput!,$options:OrderCreateOptionsInput){
  orderCreate(order:$order, options:$options){
    order{ id name totalPriceSet{shopMoney{amount}} totalTaxSet{shopMoney{amount}}
           displayFinancialStatus displayFulfillmentStatus closed }
    userErrors{ field message } } }"""
ORDER_OPTIONS = {"inventoryBehaviour": "BYPASS", "sendReceipt": False, "sendFulfillmentReceipt": False}


def find_customer(email):
    nodes = gql(Q_FIND_CUSTOMER, {"q": f"email:\"{email}\""})["customers"]["nodes"]
    return next((n for n in nodes if (n["email"] or "").lower() == email), None)


def ensure_customer(cinput, dry):
    existing = find_customer(cinput["email"])
    if existing:
        if IMPORT_TAG not in existing["tags"] and not dry:
            errs = gql(M_TAGS_ADD, {"id": existing["id"], "tags": [IMPORT_TAG]}, mutate=True)["tagsAdd"]["userErrors"]
            if errs:
                raise RuntimeError(f"tagsAdd: {errs}")
        return existing["id"], "existing"
    if dry:
        return None, "would create"
    res = gql(M_CREATE_CUSTOMER, {"input": cinput}, mutate=True)["customerCreate"]
    if res["userErrors"]:
        # Most likely an address Shopify won't accept; retry without addresses rather than lose the customer.
        retry = dict(cinput, addresses=[])
        res2 = gql(M_CREATE_CUSTOMER, {"input": retry}, mutate=True)["customerCreate"]
        if res2["userErrors"]:
            raise RuntimeError(f"customerCreate: {res['userErrors']} / retry: {res2['userErrors']}")
        return res2["customer"]["id"], f"created without addresses ({res['userErrors']})"
    return res["customer"]["id"], "created"


def order_exists(name):
    nodes = gql(Q_FIND_ORDER, {"q": f"name:\"{name}\""})["orders"]["nodes"]
    return next((n["id"] for n in nodes if n["name"] == name), None)


# --------------------------------------------------------------------------- commands

def load_export(path):
    path = path if os.path.isabs(path) else os.path.join(HERE, path)
    with open(path) as f:
        d = json.load(f)
    customers = {c["id"]: c for c in d.get("customers", [])}
    orders = sorted(d["orders"], key=lambda o: o["date_created_gmt"])
    return orders, customers


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"customers": {}, "orders": {}}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=1)


def log(entry):
    entry["at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def cmd_plan(args):
    orders, customers = load_export(args.export)
    match = build_matcher(load_shopify_products())
    for o in orders[: args.limit or None]:
        if o["status"] not in SUPPORTED_STATUSES:
            print(f"#{o['number']}: SKIP status {o['status']}")
            continue
        cinp = customer_input(o, customers.get(o["customer_id"]))
        oinp, notes = order_input(o, "gid://shopify/Customer/0", match)
        matched = sum(1 for l in oinp["lineItems"] if "variantId" in l)
        print(f"#{o['number']} {o['date_created'][:10]} {o['status']} £{o['total']} "
              f"{'registered' if o['customer_id'] else 'guest'} lines {matched}/{len(oinp['lineItems'])} matched"
              + (f" discount {oinp['discountCode']['itemFixedDiscountCode']['code']}" if "discountCode" in oinp else ""))
        for n in notes:
            print("   note:", n)
        if args.verbose:
            print(json.dumps({"customer": cinp, "order": oinp}, indent=1))


def cmd_run(args):
    orders, customers = load_export(args.export)
    match = build_matcher(load_shopify_products())
    state = load_state()
    done = 0
    for o in orders:
        if args.limit and done >= args.limit:
            break
        num = str(o["number"])
        name = f"{ORDER_PREFIX}{num}"
        if o["status"] not in SUPPORTED_STATUSES:
            print(f"{name}: skipped, status {o['status']}")
            log({"order": num, "result": "skipped", "status": o["status"]})
            continue
        if num in state["orders"]:
            print(f"{name}: already imported ({state['orders'][num]})")
            continue
        done += 1
        try:
            existing = order_exists(name)
            if existing:
                state["orders"][num] = existing
                save_state(state)
                print(f"{name}: already in Shopify, recorded")
                continue
            cinp = customer_input(o, customers.get(o["customer_id"]))
            if not cinp["email"]:
                raise RuntimeError("order has no email address")
            cid = state["customers"].get(cinp["email"])
            how = "known"
            if not cid:
                cid, how = ensure_customer(cinp, args.dry_run)
                if cid and not args.dry_run:
                    state["customers"][cinp["email"]] = cid
                    save_state(state)
            oinp, notes = order_input(o, cid, match)
            if args.dry_run:
                print(f"{name}: dry run, customer {how}, {len(oinp['lineItems'])} lines; notes: {notes}")
                continue
            res = gql(M_CREATE_ORDER, {"order": oinp, "options": ORDER_OPTIONS}, mutate=True)["orderCreate"]
            if res["userErrors"]:
                raise RuntimeError(f"orderCreate: {res['userErrors']}")
            so = res["order"]
            state["orders"][num] = so["id"]
            save_state(state)
            total_ok = money(so["totalPriceSet"]["shopMoney"]["amount"]) == money(o["total"])
            tax_ok = money(so["totalTaxSet"]["shopMoney"]["amount"]) == money(o["total_tax"])
            check = "totals match" if total_ok and tax_ok else (
                f"MISMATCH total {so['totalPriceSet']['shopMoney']['amount']} vs {o['total']}, "
                f"tax {so['totalTaxSet']['shopMoney']['amount']} vs {o['total_tax']}")
            print(f"{name}: created {so['id']} ({so['displayFinancialStatus']}, {so['displayFulfillmentStatus']}, "
                  f"{'archived' if so['closed'] else 'open'}), customer {how}, {check}")
            for n in notes:
                print("   note:", n)
            log({"order": num, "result": "created", "shopify_id": so["id"], "customer": how,
                 "total_ok": total_ok, "tax_ok": tax_ok, "notes": notes})
        except Exception as e:  # keep going; failures are logged and can be re-run
            print(f"{name}: FAILED {e}")
            log({"order": num, "result": "failed", "error": str(e)[:1000]})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "run"):
        p = sub.add_parser(name)
        p.add_argument("export")
        p.add_argument("--limit", type=int, default=0)
        if name == "plan":
            p.add_argument("--verbose", action="store_true")
        else:
            p.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    {"plan": cmd_plan, "run": cmd_run}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
