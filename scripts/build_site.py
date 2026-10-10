#!/usr/bin/env python3
"""Build catalog data, download images, and generate static pages.

When the raw WooCommerce export (RAW) is not available, the build falls back to
the committed data/products.json, so pages can be regenerated on any machine.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import urllib.parse
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(
    "/Users/dotcomsolutions/.cursor/projects/Users-dotcomsolutions-HTML-Tarak-Tube-Co/agent-tools/31571db3-5ab8-477e-b963-a32863a5c03d.txt"
)
CAT_RAW_FALLBACK = None

UA = "TarakTubeStaticRebuild/1.0"
COMPANY = (
    "Tarak Tube Co., a company based in Burabazar, Kolkata, West Bengal, India, "
    "that was established in the year 1993. The company is a partnership-based firm "
    "and has been engaged in the business of wholesaling, retailing and supplying various products."
)
MISSION = (
    "Our mission is to meet the diverse demands of agricultural, domestic, and commercial "
    "sectors by offering a wide range of high-quality products, maintaining efficient supply "
    "chains, fostering customer relationships, and adapting to evolving market trends to ensure "
    "comprehensive and reliable support for our clients."
)
VISION = (
    "To establish Tarak Tube Co. as a reliable and trusted name in the market, known for its "
    "quality products, competitive prices, and excellent customer service."
)
GOALS = (
    "Our goals include focusing on the supply of HDPE, PVC Borewell, UPVC, CPVC, SWR Pipes & "
    "Fittings, Ribbed Strainer Filters, India MII Hand Pump, MII Cylinders, and several other "
    "products. We aim to expand our product range to include CI Bib Cocks, Stop Cocks, Brass "
    "Ferrules, GI pipes & Fittings, PVC Garden Pipes, CP fittings, and more. We partner with "
    "prominent brands in the industry, such as Finolex, Oriplast, Tuffplast, Supreme Gold, "
    "APL Apollo, NeoSeal, and Astral, to ensure long-lasting quality, dependability, and "
    "effective functioning of products. We maintain an extensive track record of serving over "
    "2500+ customers, including contractors, plumbers, and renowned groups such as Merlin, "
    "Srijan, Ekta, and Ideal. Our dedicated team of professionals and robust distribution "
    "network ensures timely delivery and customer satisfaction."
)
HOME_INTRO = (
    "Our primary focus is on the supply of HDPE, PVC Borewell, UPVC, CPVC, SWR Pipes & Fittings, "
    "Ribbed Strainer Filters, India MII Hand Pump, MII Cylinders and several other products. "
    "Apart from these products, we also offer a wide range of other products, such as CI Bib Cocks, "
    "Stop Cocks, Brass Ferrules, GI pipes & Fittings, PVC Garden Pipes, CP fittings and the list goes on."
)
PARTNER_BRANDS = ["Finolex", "Oriplast", "Tuffplast", "Supreme Gold", "APL Apollo", "Neoseal", "Astral"]
CLIENT_GROUPS = ["Merlin", "Srijan", "Ekta", "Ideal"]
PHONE_1 = "+919831721718"
PHONE_2 = "+919831721719"
EMAIL = "taraktubeco@gmail.com"
ADDRESS = "30, Strand Road, Beside Jessop Company, Opposite Armenian Ghat, Kolkata - 700001"
WHATSAPP = "https://wa.me/919831721718"
MAP_QUERY = "Tarak Tube Co, 30 Strand Road, Kolkata 700001"

ACCESSORY_SLUGS = {
    "adaptor",
    "caps",
    "clamps",
    "flange",
    "toolkit",
    "hand-tools",
    "crack-filler-paste",
}

HOME_CATEGORIES = [
    "pipes-fittings",
    "water-storage-tanks",
    "pp-industrial-valves",
    "solvent-cement-adhesives",
    "house-connection-fittings",
    "valves",
    "pvc-hand-pump",
    "hand-pump",
]
BRAND_SLUGS = [
    "swr-pipes-fittings",
    "tata-pipes",
    "astm-upvc-pipes-fittings",
    "borewell-casing-pipes",
    "cpvc-pipes-fittings",
]
HOUSE_SLUGS = [
    "cast-iron-stop-cock",
    "cast-iron-bib-cock",
    "hdpe-brass-mta",
    "hdpe-spigot-plain-pipes-fittings",
    "brass-bibcock",
    "brass-stop-cock",
]
VALVE_SLUGS = [
    "cast-iron-sluice-valve",
    "pp-flanged-ball-valve",
    "pvc-ball-valve",
    "upvc-ball-valves",
    "cast-iron-nrv",
]
NAV_CATEGORIES = [
    ("Pipes & Fittings", "pipes-fittings"),
    ("Valves", "valves"),
    ("Bath Fittings", "bath-fittings"),
    ("Hand Pump", "hand-pump"),
    ("PVC Hand Pump", "pvc-hand-pump"),
    ("Solvent Cement", "solvent-cement-adhesives"),
    ("House Connection", "house-connection-fittings"),
    ("Water Storage Tanks", "water-storage-tanks"),
    ("G.I. Fittings", "g-i-fittings"),
    ("Pipes", "pipes"),
    ("Hand Pump Spare Parts", "hand-pump-spare-parts"),
    ("Accessories", "accessories"),
]

EXTRA_IMAGES = {
    "logo.png": "https://taraktubeco.com/wp-content/uploads/2025/02/Logo.png",
    "logo-white.png": "https://taraktubeco.com/wp-content/uploads/2024/07/Logo_White.png",
    "hero-finolex.jpg": "https://taraktubeco.com/wp-content/uploads/2024/08/finolex-fittings-1000x1000-1.jpg",
    "hero-paras.jpg": "https://taraktubeco.com/wp-content/uploads/2024/08/Bath-Faucets19.jpg",
}

# ---------------------------------------------------------------------------
# Naming cleanup: the WooCommerce export mixes ALL CAPS, slugs and typos.
# ---------------------------------------------------------------------------

ACRONYMS = {
    "PVC", "CPVC", "UPVC", "HDPE", "ASTM", "SWR", "UDS", "NRV", "PN", "MTA", "PP", "PTFE",
    "PTMT", "TTC", "MS", "GI", "SS", "GM", "MII", "II", "M", "Y", "CI", "SCH", "APL",
}
SMALL_WORDS = {"and", "in", "of", "for", "with", "to"}
NAME_FIXES = {
    "Kestrel pipe & fittings metrialss": "Kestrel Pipes & Fittings",
    "TUFFPLAST PIPE AND FITTNGS": "Tuffplast Pipes & Fittings",
    "Pvc Hand Pump – FlangeType": "PVC Hand Pump – Flange Type",
    "Standard Quality PTFE Taflon Tape": "Standard Quality PTFE Teflon Tape",
    "THREE IN ONE WALL MIXTURE": "Three-in-One Wall Mixer",
    "PP Y STRAINER FLANGE TYPE": "PP Y-Strainer Flange Type",
    "HOUSE CONNECTIONS FITTINGS": "House Connection Fittings",
}
BRAND_CANON = {
    "finolex": "Finolex",
    "aplapollo": "APL Apollo",
    "apl apollo": "APL Apollo",
    "tuffplast": "Tuffplast",
    "neo seal": "Neoseal",
    "neoseal": "Neoseal",
    "kestral": "Kestrel",
    "tata": "Tata",
    "atil": "Atil",
    "javia": "Javia",
}


def title_word(word: str, first: bool = True) -> str:
    m = re.match(r"^([(\[]*)(.*?)([)\],.:]*)$", word)
    pre, mid, post = m.groups()
    if not mid:
        return word
    if not first and mid.lower() in SMALL_WORDS:
        mid = mid.lower()
    elif re.fullmatch(r"[A-Za-z](\.[A-Za-z])+\.?", mid + post):
        mid, post = (mid + post).upper().rstrip(".") + ".", ""
    elif "-" in mid:
        mid = "-".join(title_word(part, i == 0) for i, part in enumerate(mid.split("-")))
    elif mid.upper() in ACRONYMS:
        mid = mid.upper()
    elif any(ch.isdigit() for ch in mid):
        pass
    else:
        mid = mid[:1].upper() + mid[1:].lower()
    return pre + mid + post


def clean_name(name: str) -> str:
    name = (name or "").strip()
    if name in NAME_FIXES:
        return NAME_FIXES[name]
    if " " not in name and "-" in name:
        name = name.replace("-", " ")
    name = re.sub(r"cast-iron", "Cast Iron", name, flags=re.I)
    name = re.sub(r"\s*/\s*", " / ", name)
    name = re.sub(r"\s+and\s+", " & ", name, flags=re.I)
    return " ".join(title_word(w, i == 0) for i, w in enumerate(name.split()))


def clean_brand(value: str) -> str:
    if not value:
        return ""
    out = []
    for part in re.split(r"\s*(?:,|/|\.\s)\s*", value):
        part = part.strip(" .")
        if not part:
            continue
        canon = BRAND_CANON.get(part.lower())
        if not canon:
            canon = part.title() if part.isupper() and len(part) > 3 else part
        if canon not in out:
            out.append(canon)
    return ", ".join(out)


def normalize(products: list[dict]) -> list[dict]:
    for product in products:
        product["name"] = clean_name(product["name"])
        product["brand"] = clean_brand(product.get("brand") or "")
        if "Brand" in product["specs"]:
            product["specs"]["Brand"] = clean_brand(product["specs"]["Brand"])
        for cat in product["categories"]:
            cat["name"] = clean_name(cat["name"])
    products.sort(key=lambda p: p["name"].lower())
    return products


def plural(n: int, word: str = "product") -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def esc(value: str) -> str:
    return html.escape(value or "")


# ---------------------------------------------------------------------------
# Icons
# ---------------------------------------------------------------------------

def icon(name: str, size: int = 18) -> str:
    paths = {
        "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
        "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
        "pin": '<path d="M12 22s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>',
        "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "check": '<path d="m5 12 4.5 4.5L19 7"/>',
        "close": '<path d="M6 6l12 12M18 6 6 18"/>',
        "prev": '<path d="m15 6-6 6 6 6"/>',
        "next": '<path d="m9 6 6 6-6 6"/>',
    }
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'
    )


WA_ICON = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.5 3.5A11 11 0 0 0 2.1 17.7L1 23l5.4-1.1A11 11 0 0 0 20.5 3.5zm-8.5 17a9 9 0 0 1-4.6-1.3l-.3-.2-3.2.7.7-3.1-.2-.3A9 9 0 1 1 12 20.5zm5-6.7c-.3-.1-1.6-.8-1.8-.9s-.4-.1-.6.1-.7.9-.8 1-.3.2-.6.1a7.4 7.4 0 0 1-2.2-1.4 8.2 8.2 0 0 1-1.5-1.9c-.2-.3 0-.4.1-.6l.3-.4.1-.3c0-.1 0-.3-.1-.4s-.6-1.4-.8-1.9-.4-.4-.6-.4h-.5c-.2 0-.4.1-.6.3s-.8.8-.8 1.9.8 2.2.9 2.3c.1.2 1.6 2.5 3.8 3.4s2.1.6 2.8.5 1.6-.7 1.8-1.3.2-1.2.1-1.3-.2-.2-.5-.3z"/></svg>'


def clean_text(value: str) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def ext_from(url: str) -> str:
    name = url.split("?")[0].rsplit("/", 1)[-1]
    suffix = Path(name).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"} else ".jpg"


def download(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return True
    req = urllib.request.Request(urllib.parse.quote(url, safe=":/?&=%"), headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as res, open(dest, "wb") as fh:
            shutil.copyfileobj(res, fh)
        return dest.stat().st_size > 0
    except Exception as exc:
        print(f"FAIL {url} -> {dest.name}: {exc}")
        return False


def load_products() -> list[dict]:
    if not RAW.exists():
        print(f"Raw export not found, rebuilding from data/products.json")
        products = json.loads((ROOT / "data/products.json").read_text())
        for product in products:
            product.setdefault("source_image", "")
        return normalize(products)

    raw = json.loads(RAW.read_text())
    products = []
    for item in raw:
        attrs = {}
        for attr in item.get("attributes") or []:
            name = html.unescape(attr.get("name") or "")
            terms = ", ".join(html.unescape(t.get("name") or "") for t in attr.get("terms") or [])
            if name and terms:
                attrs[name] = terms
        cats = []
        for cat in item.get("categories") or []:
            cats.append({"name": cat["name"], "slug": cat["slug"]})
        if not cats:
            cats = [{"name": "Pipes & Fittings", "slug": "pipes-fittings"}]
        if any(c["slug"] in ACCESSORY_SLUGS for c in cats) and not any(c["slug"] == "accessories" for c in cats):
            cats.append({"name": "Accessories", "slug": "accessories"})
        images = item.get("images") or []
        src = images[0]["src"] if images else ""
        image_rel = f"assets/img/products/{item['slug']}{ext_from(src)}" if src else "assets/img/logo.png"
        desc = clean_text(item.get("description") or item.get("short_description") or "")
        brand = attrs.get("Brand") or (item.get("brands") or [{}])
        if isinstance(brand, list):
            brand = brand[0].get("name") if brand else ""
        products.append(
            {
                "id": item["id"],
                "name": html.unescape(item["name"]),
                "slug": item["slug"],
                "sku": item.get("sku") or "",
                "brand": brand,
                "description": desc,
                "specs": attrs,
                "categories": cats,
                "image": image_rel,
                "source_image": src,
                "in_stock": bool(item.get("is_in_stock", True)),
            }
        )
    return normalize(products)


def build_categories(products: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for product in products:
        for cat in product["categories"]:
            slug = cat["slug"]
            grouped.setdefault(
                slug,
                {"name": cat["name"], "slug": slug, "count": 0, "image": product["image"]},
            )
            grouped[slug]["count"] += 1
    # Prefer known category images from live site later if present
    extras = {
        "pipes-fittings": "assets/img/categories/pipes-fittings.png",
        "valves": "assets/img/categories/valves.png",
        "hand-pump": "assets/img/categories/hand-pump.jpg",
        "pvc-hand-pump": "assets/img/categories/pvc-hand-pump.png",
        "solvent-cement-adhesives": "assets/img/categories/solvent-cement-adhesives.jpg",
        "house-connection-fittings": "assets/img/categories/house-connection-fittings.jpg",
        "water-storage-tanks": "assets/img/categories/water-storage-tanks.png",
        "pp-industrial-valves": "assets/img/categories/pp-industrial-valves.jpeg",
        "accessories": "assets/img/categories/accessories.png",
    }
    for slug, image in extras.items():
        if slug in grouped:
            grouped[slug]["image"] = image
    return sorted(grouped.values(), key=lambda c: c["name"].lower())


def by_slug(products: list[dict]) -> dict[str, dict]:
    return {p["slug"]: p for p in products}


def header_html(root: str, active: str = "") -> str:
    def nav(href: str, label: str, key: str) -> str:
        cls = ' class="is-active"' if active == key else ""
        return f'<a href="{root}{href}" data-nav{cls}>{label}</a>'

    mega = "".join(
        f'<a href="{root}product-category/{slug}/">{esc(name)}</a>'
        for name, slug in NAV_CATEGORIES
    )
    return f"""
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="{root}">
      <img src="{root}assets/img/logo.png" alt="Tarak Tube Co.">
      <span class="brand-name">Tarak Tube Co.</span>
    </a>
    <form class="search-form" data-search-form action="{root}shop/" method="get">
      <label class="sr-only" for="q">Search for products</label>
      <input id="q" name="q" type="search" placeholder="Search for products" required>
      <button type="submit" aria-label="Search"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg></button>
    </form>
    <button class="menu-toggle" type="button" data-open-drawer aria-label="Open mobile menu"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h10"/></svg></button>
  </div>
</header>
<nav class="desktop-nav">
  <div class="container">
    {nav("", "Home", "home")}
    {nav("about-us/", "About Us", "about")}
    {nav("shop/", "Products", "shop")}
    {nav("contact-us/", "Contact Us", "contact")}
    <a class="nav-cta" href="tel:{PHONE_1}">{icon("phone", 15)} +91 98317 21718</a>
  </div>
</nav>
<div class="drawer" data-drawer>
  <div class="drawer-panel">
    <div class="drawer-head">
      <strong>Menu</strong>
      <button type="button" data-close-drawer aria-label="Close menu">{icon("close", 20)}</button>
    </div>
    <div class="drawer-tabs">
      <button type="button" class="is-active" data-drawer-tab="menu">Pages</button>
      <button type="button" data-drawer-tab="categories">Categories</button>
    </div>
    <div class="drawer-list is-active" data-drawer-panel="menu">
      {nav("", "Home", "home")}
      {nav("about-us/", "About Us", "about")}
      {nav("shop/", "Products", "shop")}
      {nav("contact-us/", "Contact Us", "contact")}
    </div>
    <div class="drawer-list" data-drawer-panel="categories">{mega}</div>
  </div>
</div>
<div class="search-overlay" data-search-overlay>
  <div class="search-panel">
    <div class="search-panel-head">
      <strong>Search results</strong>
      <button type="button" data-close-search aria-label="Close search">{icon("close", 20)}</button>
    </div>
    <div class="search-results" data-search-results></div>
  </div>
</div>
"""


def cta_html(root: str) -> str:
    return f"""
<section class="cta-band">
  <div class="container cta-inner">
    <div>
      <p class="eyebrow light">Bulk &amp; project supply</p>
      <h2>Need pipes, fittings or valves for your project?</h2>
      <p>Share your requirement and our team will get back with availability and the best pricing.</p>
    </div>
    <div class="cta-actions">
      <a class="btn light" href="{WHATSAPP}" target="_blank" rel="noopener">{WA_ICON} WhatsApp Us</a>
      <a class="btn outline-light" href="{root}contact-us/">Get a Quote</a>
    </div>
  </div>
</section>
"""


def footer_html(root: str) -> str:
    cats = "".join(
        f'<li><a href="{root}product-category/{slug}/">{esc(name)}</a></li>'
        for name, slug in NAV_CATEGORIES[:6]
    )
    return f"""
<footer class="site-footer">
  <div class="container footer-grid">
    <div class="footer-about">
      <a class="footer-brand" href="{root}"><img src="{root}assets/img/logo.png" alt=""> <span>Tarak Tube Co.</span></a>
      <p>{esc(COMPANY)}</p>
    </div>
    <div>
      <h4>Quick Links</h4>
      <ul>
        <li><a href="{root}">Home</a></li>
        <li><a href="{root}about-us/">About Us</a></li>
        <li><a href="{root}shop/">Products</a></li>
        <li><a href="{root}contact-us/">Contact Us</a></li>
      </ul>
    </div>
    <div>
      <h4>Categories</h4>
      <ul>{cats}<li><a href="{root}shop/">All Products</a></li></ul>
    </div>
    <div>
      <h4>Get in Touch</h4>
      <ul class="footer-contact">
        <li>{icon("pin", 16)}<span>{esc(ADDRESS)}</span></li>
        <li>{icon("phone", 16)}<span><a href="tel:{PHONE_1}">+91 98317 21718</a><br><a href="tel:{PHONE_2}">+91 98317 21719</a></span></li>
        <li>{icon("mail", 16)}<span><a href="mailto:{EMAIL}">{EMAIL}</a></span></li>
      </ul>
    </div>
  </div>
  <div class="container legal">
    <span>© 2026 Tarak Tube Co. All rights reserved.</span>
    <span>Powered by Dot Com Solutions</span>
  </div>
</footer>
<button class="to-top" type="button" data-to-top aria-label="Back to top"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 15 6-6 6 6"/></svg></button>
<a class="whatsapp-fab" href="{WHATSAPP}" target="_blank" rel="noopener" aria-label="WhatsApp">
  <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.5 3.5A11 11 0 0 0 2.1 17.7L1 23l5.4-1.1A11 11 0 0 0 20.5 3.5zm-8.5 17a9 9 0 0 1-4.6-1.3l-.3-.2-3.2.7.7-3.1-.2-.3A9 9 0 1 1 12 20.5zm5-6.7c-.3-.1-1.6-.8-1.8-.9s-.4-.1-.6.1-.7.9-.8 1-.3.2-.6.1a7.4 7.4 0 0 1-2.2-1.4 8.2 8.2 0 0 1-1.5-1.9c-.2-.3 0-.4.1-.6l.3-.4.1-.3c0-.1 0-.3-.1-.4s-.6-1.4-.8-1.9-.4-.4-.6-.4h-.5c-.2 0-.4.1-.6.3s-.8.8-.8 1.9.8 2.2.9 2.3c.1.2 1.6 2.5 3.8 3.4s2.1.6 2.8.5 1.6-.7 1.8-1.3.2-1.2.1-1.3-.2-.2-.5-.3z"/></svg>
</a>
"""


def page_shell(title: str, root: str, body: str, active: str = "", description: str = "") -> str:
    description = description or "Tarak Tube Co., Kolkata — wholesale supplier of pipes, fittings, valves, hand pumps and bath fittings since 1993."
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="icon" href="{root}assets/img/logo.png">
  <script>document.documentElement.classList.add("js")</script>
  <link rel="stylesheet" href="{root}assets/css/tokens.css">
  <link rel="stylesheet" href="{root}assets/css/chrome.css">
  <link rel="stylesheet" href="{root}assets/css/pages.css">
</head>
<body>
{header_html(root, active)}
<main>{body}</main>
{cta_html(root)}
{footer_html(root)}
<script src="{root}assets/js/include.js"></script>
<script src="{root}assets/js/main.js"></script>
<script src="{root}assets/js/search.js"></script>
</body>
</html>
"""


def page_hero(crumbs: list[tuple[str, str]], title: str = "", lead: str = "") -> str:
    trail = " ".join(
        f'<a href="{href}">{esc(label)}</a><span aria-hidden="true">/</span>' if href else f"<span>{esc(label)}</span>"
        for label, href in crumbs
    )
    heading = f"<h1>{esc(title)}</h1>" if title else ""
    lead_html = f'<p class="lead">{lead}</p>' if lead else ""
    return f"""
    <section class="page-hero{'' if title else ' compact'}"><div class="container">
      <nav class="crumbs" aria-label="Breadcrumb">{trail}</nav>
      {heading}{lead_html}
    </div></section>"""


def product_card(product: dict, root: str) -> str:
    cat = product["categories"][0]["name"]
    size = product["specs"].get("Size", "")
    brand = product["brand"]
    meta = []
    if brand:
        meta.append(f'<li><span>Brand</span>{esc(brand)}</li>')
    if size:
        meta.append(f'<li><span>Size</span>{esc(size)}</li>')
    return f"""
    <article class="card product-card">
      <a href="{root}product/{product['slug']}/">
        <div class="media"><img src="{root}{product['image']}" alt="{esc(product['name'])}" loading="lazy"></div>
        <div class="body">
          <p class="eyebrow">{esc(cat)}</p>
          <h3>{esc(product['name'])}</h3>
          <ul class="card-meta">{''.join(meta)}</ul>
          <span class="card-link">View details {icon("arrow", 16)}</span>
        </div>
      </a>
    </article>
    """


def category_card(cat: dict, root: str) -> str:
    return f"""
    <a class="card category-card" href="{root}product-category/{cat['slug']}/">
      <div class="media"><img src="{root}{cat['image']}" alt="{esc(cat['name'])}" loading="lazy"></div>
      <div class="body">
        <h3>{esc(cat['name'])}</h3>
        <span class="card-link">{plural(cat['count'])} {icon("arrow", 16)}</span>
      </div>
    </a>"""


def category_chips(root: str, active: str = "") -> str:
    chips = [f'<a class="chip{" is-active" if not active else ""}" href="{root}shop/">All</a>']
    for name, slug in NAV_CATEGORIES:
        cls = " is-active" if slug == active else ""
        chips.append(f'<a class="chip{cls}" href="{root}product-category/{slug}/">{esc(name)}</a>')
    return f'<div class="chips">{"".join(chips)}</div>'


def brand_strip() -> str:
    return "".join(f'<li>{esc(b)}</li>' for b in PARTNER_BRANDS)


def stats_html(product_count: int) -> str:
    stats = [
        ("1993", "Established in Kolkata"),
        ("2500+", "Customers served"),
        (f"{product_count}", "Products in catalogue"),
        (f"{len(PARTNER_BRANDS)}+", "Leading brand partners"),
    ]
    return "".join(f'<div class="stat"><strong>{v}</strong><span>{esc(l)}</span></div>' for v, l in stats)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def home_page(products: list[dict], categories: list[dict]) -> str:
    lookup = by_slug(products)
    cat_lookup = {c["slug"]: c for c in categories}
    cards = "".join(category_card(cat_lookup[s], "./") for s in HOME_CATEGORIES if s in cat_lookup)

    def carousel(eyebrow: str, title: str, slugs: list[str], link: str) -> str:
        items = "".join(product_card(lookup[s], "./") for s in slugs if s in lookup)
        return f"""
        <section class="section" data-carousel>
          <div class="container">
            <div class="section-head">
              <div><p class="eyebrow">{esc(eyebrow)}</p><h2>{esc(title)}</h2></div>
              <div class="section-actions">
                <a class="text-link" href="{link}">View all {icon("arrow", 16)}</a>
                <div class="carousel-nav">
                  <button type="button" data-prev aria-label="Previous">{icon("prev")}</button>
                  <button type="button" data-next aria-label="Next">{icon("next")}</button>
                </div>
              </div>
            </div>
            <div class="carousel-track" data-track>{items}</div>
          </div>
        </section>
        """

    features = [
        "Wholesale, retail &amp; project supply",
        "Authorised range from leading brands",
        "Trusted by contractors, plumbers &amp; builders",
        "Robust distribution for timely delivery",
    ]
    # The list is doubled so the CSS loop scrolls seamlessly.
    ticker = "".join(f"<li>{esc(b)}</li>" for b in PARTNER_BRANDS * 4)
    feature_list = "".join(f"<li>{icon('check', 18)}<span>{f}</span></li>" for f in features)

    body = f"""
    <section class="hero">
      <article class="hero-slide is-active" data-hero-slide style="background-image:linear-gradient(90deg,rgba(6,12,34,.85) 0%,rgba(6,12,34,.55) 45%,rgba(6,12,34,.1) 100%),url('./assets/img/hero-finolex.jpg')">
        <div class="container"><div class="hero-copy">
          <p class="hero-kicker">Finolex Plumbing System</p>
          <h1>Right Choice for Hot &amp; Cold Water Plumbing</h1>
          <p class="hero-lead">CPVC, UPVC and SWR pipes &amp; fittings from Finolex, supplied in bulk across Kolkata.</p>
          <div class="hero-actions">
            <a class="btn light" href="./shop/">Explore Products</a>
            <a class="btn outline-light" href="./contact-us/">Request a Quote</a>
          </div>
        </div></div>
      </article>
      <article class="hero-slide" data-hero-slide style="background-image:linear-gradient(90deg,rgba(6,12,34,.85) 0%,rgba(6,12,34,.55) 45%,rgba(6,12,34,.1) 100%),url('./assets/img/hero-paras.jpg')">
        <div class="container"><div class="hero-copy">
          <p class="hero-kicker">Paras Ultra</p>
          <h1>A Wide Range of Premium Bath Faucets</h1>
          <p class="hero-lead">Pillar cocks, sink cocks, showers and wall mixers for every bathroom and kitchen.</p>
          <div class="hero-actions">
            <a class="btn light" href="./product-category/bath-fittings/">View Bath Fittings</a>
            <a class="btn outline-light" href="./contact-us/">Request a Quote</a>
          </div>
        </div></div>
      </article>
      <div class="hero-nav container">
        <div class="hero-dots">
          <button type="button" data-hero-dot aria-label="Slide 1"><span></span></button>
          <button type="button" data-hero-dot aria-label="Slide 2"><span></span></button>
        </div>
        <div class="hero-arrows">
          <button type="button" data-hero-prev aria-label="Previous slide">{icon("prev")}</button>
          <button type="button" data-hero-next aria-label="Next slide">{icon("next")}</button>
        </div>
      </div>
    </section>
    <section class="stats-band"><div class="container stats-grid">{stats_html(len(products))}</div></section>
    <section class="brand-ticker" aria-label="Brands we supply">
      <p class="container ticker-label">Authorised supplier of leading brands</p>
      <div class="ticker"><ul class="ticker-track">{ticker}</ul></div>
    </section>
    <section class="section">
      <div class="container">
        <div class="section-head">
          <div><p class="eyebrow">What we supply</p><h2>Product Categories</h2></div>
          <a class="text-link" href="./shop/">View all products {icon("arrow", 16)}</a>
        </div>
        <div class="category-grid">{cards}</div>
      </div>
    </section>
    {carousel("Featured", "Pipes & Fittings", BRAND_SLUGS, "./product-category/pipes-fittings/")}
    <section class="section alt">
      <div class="container intro-block">
        <div>
          <p class="eyebrow">About us</p>
          <h2>Welcome to Tarak Tube Co.</h2>
          <p>{esc(COMPANY)}</p>
          <p>{esc(HOME_INTRO)}</p>
          <a class="btn" href="./about-us/">More About Us</a>
        </div>
        <div class="intro-panel">
          <ul class="feature-list">{feature_list}</ul>
          <div class="brand-block">
            <p class="eyebrow">Brands we supply</p>
            <ul class="brand-list">{brand_strip()}</ul>
          </div>
        </div>
      </div>
    </section>
    {carousel("Featured", "House Connection Fittings", HOUSE_SLUGS, "./product-category/house-connection-fittings/")}
    {carousel("Featured", "Valves", VALVE_SLUGS, "./product-category/valves/")}
    """
    return page_shell("Tarak Tube Co. — Pipes, Fittings & Valves Supplier, Kolkata", "./", body, "home")


def about_page(product_count: int) -> str:
    clients = ", ".join(CLIENT_GROUPS)
    body = f"""
    {page_hero([("Home", "../"), ("About Us", "")], "About Tarak Tube Co.",
               "A trusted name in pipes, fittings and plumbing supplies in Kolkata since 1993.")}
    <section class="section"><div class="container">
      <div class="about-intro">
        <div>
          <p class="eyebrow">Who we are</p>
          <h2>Three decades of dependable supply</h2>
          <p>{esc(COMPANY)}</p>
          <p>We serve contractors, plumbers and renowned groups such as {esc(clients)}, backed by a dedicated team and a robust distribution network.</p>
        </div>
        <div class="stats-grid boxed">{stats_html(product_count)}</div>
      </div>
    </div></section>
    <section class="section alt"><div class="container">
      <div class="section-head"><div><p class="eyebrow">Our purpose</p><h2>Mission, Vision &amp; Goals</h2></div></div>
      <div class="about-grid">
        <article class="about-card"><span class="about-num">01</span><h3>Mission</h3><p>{esc(MISSION)}</p></article>
        <article class="about-card"><span class="about-num">02</span><h3>Vision</h3><p>{esc(VISION)}</p></article>
        <article class="about-card wide"><span class="about-num">03</span><h3>Goals</h3><p>{esc(GOALS)}</p></article>
      </div>
    </div></section>
    <section class="section"><div class="container">
      <div class="section-head"><div><p class="eyebrow">Partners</p><h2>Brands We Supply</h2></div></div>
      <ul class="brand-list large">{brand_strip()}</ul>
    </div></section>
    """
    return page_shell("About Us – Tarak Tube Co.", "../", body, "about")


def contact_page() -> str:
    q = urllib.parse.quote(MAP_QUERY)
    map_embed = f"https://www.google.com/maps?q={q}&z=16&output=embed"
    map_link = f"https://www.google.com/maps/dir/?api=1&destination={q}"
    body = f"""
    {page_hero([("Home", "../"), ("Contact Us", "")], "Contact Us",
               "Have a requirement or a question? Call, WhatsApp or send us a message.")}
    <section class="section"><div class="container contact-grid">
      <article class="contact-card">
        <p class="eyebrow">Visit our store</p>
        <h2>Tarak Tube Co.</h2>
        <p class="muted">Taha &amp; Hussain Deesawala</p>
        <ul class="contact-list">
          <li>{icon("pin")}<div><strong>Address</strong><span>{esc(ADDRESS)}</span></div></li>
          <li>{icon("phone")}<div><strong>Phone</strong><span><a href="tel:{PHONE_1}">+91 98317 21718</a>, <a href="tel:{PHONE_2}">+91 98317 21719</a></span></div></li>
          <li>{icon("mail")}<div><strong>Email</strong><span><a href="mailto:{EMAIL}">{EMAIL}</a></span></div></li>
          <li>{icon("clock")}<div><strong>Store Hours</strong><span>Mon – Fri: 10:00 am – 7:00 pm<br>Saturday: 10:00 am – 5:00 pm<br>Sunday: Closed</span></div></li>
        </ul>
        <a class="btn whatsapp" href="{WHATSAPP}" target="_blank" rel="noopener">{WA_ICON} Chat on WhatsApp</a>
      </article>
      <article class="contact-card">
        <p class="eyebrow">Send a message</p>
        <h2>Drop Us a Line</h2>
        <form class="form" action="mailto:{EMAIL}" method="post" enctype="text/plain">
          <div class="form-row">
            <label>Your name<input name="name" required></label>
            <label>Your email<input name="email" type="email" required></label>
          </div>
          <label>Subject<input name="subject" required></label>
          <label><span>Your message <span class="muted">(optional)</span></span><textarea name="message"></textarea></label>
          <button class="btn" type="submit">Send Message</button>
        </form>
      </article>
    </div></section>
    <section class="section alt map-section"><div class="container">
      <div class="section-head">
        <div><p class="eyebrow">Find us</p><h2>Our Location</h2></div>
        <a class="text-link" href="{map_link}" target="_blank" rel="noopener">Get directions {icon("arrow", 16)}</a>
      </div>
      <div class="map-card">
        <iframe title="Tarak Tube Co. on Google Maps" src="{map_embed}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
      </div>
    </div></section>
    """
    return page_shell("Contact Us – Tarak Tube Co.", "../", body, "contact")


def shop_page(products: list[dict]) -> str:
    cards = "".join(product_card(p, "../") for p in products)
    body = f"""
    {page_hero([("Home", "../"), ("Products", "")], "All Products", plural(len(products)) + " across pipes, fittings, valves, hand pumps and bath fittings.")}
    <section class="section"><div class="container">
      {category_chips("../")}
      <div class="product-grid">{cards}</div>
    </div></section>
    """
    return page_shell("Products – Tarak Tube Co.", "../", body, "shop")


def category_page(category: dict, products: list[dict]) -> str:
    items = [p for p in products if any(c["slug"] == category["slug"] for c in p["categories"])]
    cards = "".join(product_card(p, "../../") for p in items)
    body = f"""
    {page_hero([("Home", "../../"), ("Products", "../../shop/"), (category['name'], "")], category["name"], plural(len(items)))}
    <section class="section"><div class="container">
      {category_chips("../../", category["slug"])}
      <div class="product-grid">{cards or '<p class="empty">No products in this category yet.</p>'}</div>
    </div></section>
    """
    return page_shell(f"{category['name']} – Tarak Tube Co.", "../../", body, "shop")


def product_page(product: dict, products: list[dict]) -> str:
    cat = product["categories"][0]
    specs = product["specs"]
    rows = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in specs.items())
    key_rows = "".join(
        f"<tr><th>{k}</th><td>{esc(specs[k])}</td></tr>" for k in ("Size", "Brand", "Grade") if k in specs
    )
    related = [
        p
        for p in products
        if p["slug"] != product["slug"]
        and any(c["slug"] == cat["slug"] for c in p["categories"])
    ][:4]
    related_html = "".join(product_card(p, "../../") for p in related)
    desc = esc(product["description"]) if product["description"] else "Contact Tarak Tube Co. for sizes, brands, and current stock."
    wa = f"{WHATSAPP}?text={urllib.parse.quote('I would like to enquire about ' + product['name'])}"
    sku = f'<span class="sku">SKU: {esc(product["sku"])}</span>' if product["sku"] else ""
    stock = '<span class="stock">In stock</span>' if product["in_stock"] else '<span class="stock out">Enquire for stock</span>'
    specs_section = (
        f'<div><h2>Specifications</h2><table class="specs">{rows}</table></div>' if rows else ""
    )
    related_section = (
        f"""<section class="section"><div class="container">
      <div class="section-head"><div><p class="eyebrow">More from {esc(cat['name'])}</p><h2>Related Products</h2></div>
      <a class="text-link" href="../../product-category/{cat['slug']}/">View category {icon("arrow", 16)}</a></div>
      <div class="product-grid">{related_html}</div>
    </div></section>"""
        if related
        else ""
    )
    body = f"""
    {page_hero([("Home", "../../"), ("Products", "../../shop/"), (cat['name'], f"../../product-category/{cat['slug']}/"), (product['name'], "")])}
    <section class="section"><div class="container product-layout">
      <div class="product-photo"><img src="../../{product['image']}" alt="{esc(product['name'])}"></div>
      <div class="product-info">
        <a class="eyebrow" href="../../product-category/{cat['slug']}/">{esc(cat['name'])}</a>
        <h1>{esc(product['name'])}</h1>
        <div class="product-tags">{stock}{sku}</div>
        {f'<table class="specs">{key_rows}</table>' if key_rows else ''}
        <div class="product-actions">
          <a class="btn whatsapp" href="{wa}" target="_blank" rel="noopener">{WA_ICON} Enquire on WhatsApp</a>
          <a class="btn ghost" href="tel:{PHONE_1}">{icon("phone")} Call Us</a>
        </div>
      </div>
    </div></section>
    <section class="section alt"><div class="container detail-grid{'' if specs_section else ' single'}">
      <div><h2>Description</h2><p>{desc}</p></div>
      {specs_section}
    </div></section>
    {related_section}
    """
    return page_shell(f"{product['name']} – Tarak Tube Co.", "../../", body, "shop", product["description"][:155])


def accessories_page() -> dict:
    return {"name": "Accessories", "slug": "accessories", "count": 0, "image": "assets/img/categories/accessories.png"}


def download_all(products: list[dict]) -> None:
    jobs = []
    for name, url in EXTRA_IMAGES.items():
        jobs.append((url, ROOT / "assets/img" / name))
    cat_images = {
        "pipes-fittings.png": "https://taraktubeco.com/wp-content/uploads/2024/07/Agriculture-pipes-fittings-1.png",
        "valves.png": "https://taraktubeco.com/wp-content/uploads/2022/05/fip-ball-valve.png",
        "hand-pump.jpg": "https://taraktubeco.com/wp-content/uploads/2025/02/TTC.jpg",
        "pvc-hand-pump.png": "https://taraktubeco.com/wp-content/uploads/2024/07/Pvc-hand-pump-clamp-type-1.png",
        "solvent-cement-adhesives.jpg": "https://taraktubeco.com/wp-content/uploads/2025/02/1.jpg",
        "house-connection-fittings.jpg": "https://taraktubeco.com/wp-content/uploads/2024/08/brass-stop-valve-it-40-mm-500x500-1.jpg",
        "water-storage-tanks.png": "https://taraktubeco.com/wp-content/uploads/2024/07/Water-storage-tanks-1.png",
        "pp-industrial-valves.jpeg": "https://taraktubeco.com/wp-content/uploads/2024/08/pp-diaphragm-valve-flange-end-1.jpeg",
        "accessories.png": "https://taraktubeco.com/wp-content/uploads/2022/05/accessories-1.png",
    }
    for name, url in cat_images.items():
        jobs.append((url, ROOT / "assets/img/categories" / name))
    for product in products:
        if product.get("source_image"):
            jobs.append((product["source_image"], ROOT / product["image"]))

    ok = 0
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(download, url, dest): dest for url, dest in jobs}
        for future in as_completed(futures):
            if future.result():
                ok += 1
    print(f"Downloaded {ok}/{len(jobs)} images")


def write_partials() -> None:
    write(ROOT / "partials/header.html", header_html("./"))
    write(ROOT / "partials/footer.html", footer_html("./"))


def main() -> None:
    products = load_products()
    categories = build_categories(products)
    if not any(c["slug"] == "accessories" for c in categories):
        categories.append(accessories_page())
        categories.sort(key=lambda c: c["name"].lower())

    (ROOT / "data").mkdir(exist_ok=True)
    slim = [{k: v for k, v in p.items() if k != "source_image"} for p in products]
    (ROOT / "data/products.json").write_text(json.dumps(slim, indent=2), encoding="utf-8")
    (ROOT / "data/categories.json").write_text(json.dumps(categories, indent=2), encoding="utf-8")

    download_all(products)
    write_partials()
    write(ROOT / "index.html", home_page(products, categories))
    write(ROOT / "about-us/index.html", about_page(len(products)))
    write(ROOT / "contact-us/index.html", contact_page())
    write(ROOT / "shop/index.html", shop_page(products))
    for category in categories:
        write(ROOT / f"product-category/{category['slug']}/index.html", category_page(category, products))
    for product in products:
        write(ROOT / f"product/{product['slug']}/index.html", product_page(product, products))
    print(f"Wrote {len(products)} products and {len(categories)} categories")


if __name__ == "__main__":
    main()
