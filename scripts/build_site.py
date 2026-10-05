#!/usr/bin/env python3
"""Build catalog data, download images, and generate static pages."""

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
    products.sort(key=lambda p: p["name"].lower())
    return products


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

    cat_links = "".join(
        f'<a href="{root}product-category/{slug}/">{html.escape(name)}</a>'
        for name, slug in NAV_CATEGORIES
    )
    mega = "".join(
        f"<details><summary>{html.escape(name)}</summary>"
        f'<a href="{root}product-category/{slug}/">View {html.escape(name)}</a></details>'
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
      <button type="submit" aria-label="Search">&#128269;</button>
    </form>
    <button class="menu-toggle" type="button" data-open-drawer aria-label="Open mobile menu">&#9776;</button>
  </div>
</header>
<nav class="desktop-nav">
  <div class="container">
    {nav("", "Home", "home")}
    {nav("about-us/", "About us", "about")}
    {nav("shop/", "Products", "shop")}
    {nav("contact-us/", "Contact Us", "contact")}
  </div>
</nav>
<div class="drawer" data-drawer>
  <div class="drawer-panel">
    <button type="button" data-close-drawer>Close</button>
    <div class="drawer-tabs">
      <button type="button" class="is-active" data-drawer-tab="menu">Menu</button>
      <button type="button" data-drawer-tab="categories">Categories</button>
    </div>
    <div class="drawer-list is-active" data-drawer-panel="menu">
      {nav("", "Home", "home")}
      {nav("about-us/", "About us", "about")}
      {nav("shop/", "Products", "shop")}
      {nav("contact-us/", "Contact Us", "contact")}
    </div>
    <div class="drawer-list" data-drawer-panel="categories">{mega}</div>
  </div>
</div>
<div class="search-overlay" data-search-overlay>
  <div class="search-panel">
    <button type="button" data-close-search>Close</button>
    <div class="search-results" data-search-results></div>
  </div>
</div>
"""


def footer_html(root: str) -> str:
    cats = "".join(
        f'<li><a href="{root}product-category/{slug}/">{html.escape(name)}</a></li>'
        for name, slug in NAV_CATEGORIES[:6]
    )
    return f"""
<footer class="site-footer">
  <div class="container footer-grid">
    <div>
      <h4>Tarak Tube Co.</h4>
      <p>{html.escape(COMPANY)}</p>
    </div>
    <div>
      <h4>Quick Links</h4>
      <ul>
        <li><a href="{root}">Home</a></li>
        <li><a href="{root}about-us/">About Us</a></li>
        <li><a href="{root}shop/">Products</a></li>
        <li><a href="{root}contact-us/">Contact Us</a></li>
      </ul>
      <h4>Product Categories</h4>
      <ul>{cats}<li><a href="{root}shop/">All Products</a></li></ul>
    </div>
    <div>
      <h4>Location Address</h4>
      <p>Know where to find us? Let's take a look and get in touch!</p>
      <ul>
        <li>30, Strand Road, Beside Jessop Company, Opposite Armenian Ghat, Kolkata - 700001</li>
        <li><a href="tel:+919831721718">+91 9831721718</a> / <a href="tel:+919831721719">9831721719</a></li>
        <li><a href="mailto:taraktubeco@gmail.com">taraktubeco@gmail.com</a></li>
      </ul>
    </div>
  </div>
  <div class="container legal">Copyright © 2026 Tarak Tube Co. All rights reserved. Proudly Powered By Dot Com Solutions</div>
</footer>
<a class="whatsapp-fab" href="https://wa.me/919831721718" target="_blank" rel="noopener" aria-label="WhatsApp">
  <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.5 3.5A11 11 0 0 0 2.1 17.7L1 23l5.4-1.1A11 11 0 0 0 20.5 3.5zm-8.5 17a9 9 0 0 1-4.6-1.3l-.3-.2-3.2.7.7-3.1-.2-.3A9 9 0 1 1 12 20.5zm5-6.7c-.3-.1-1.6-.8-1.8-.9s-.4-.1-.6.1-.7.9-.8 1-.3.2-.6.1a7.4 7.4 0 0 1-2.2-1.4 8.2 8.2 0 0 1-1.5-1.9c-.2-.3 0-.4.1-.6l.3-.4.1-.3c0-.1 0-.3-.1-.4s-.6-1.4-.8-1.9-.4-.4-.6-.4h-.5c-.2 0-.4.1-.6.3s-.8.8-.8 1.9.8 2.2.9 2.3c.1.2 1.6 2.5 3.8 3.4s2.1.6 2.8.5 1.6-.7 1.8-1.3.2-1.2.1-1.3-.2-.2-.5-.3z"/></svg>
</a>
"""


def page_shell(title: str, root: str, body: str, active: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="icon" href="{root}assets/img/logo.png">
  <link rel="stylesheet" href="{root}assets/css/tokens.css">
  <link rel="stylesheet" href="{root}assets/css/chrome.css">
  <link rel="stylesheet" href="{root}assets/css/pages.css">
</head>
<body>
{header_html(root, active)}
<main>{body}</main>
{footer_html(root)}
<script src="{root}assets/js/include.js"></script>
<script src="{root}assets/js/main.js"></script>
<script src="{root}assets/js/search.js"></script>
</body>
</html>
"""


def product_card(product: dict, root: str) -> str:
    specs_rows = ""
    for key in ("Size", "Brand", "Grade"):
        if key in product["specs"]:
            specs_rows += f"<tr><th>{html.escape(key)}</th><td>{html.escape(product['specs'][key])}</td></tr>"
    stock = '<p class="count">In stock</p>' if product["in_stock"] else ""
    return f"""
    <article class="card">
      <a href="{root}product/{product['slug']}/">
        <div class="media"><img src="{root}{product['image']}" alt="{html.escape(product['name'])}"></div>
        <div class="body">
          <h3>{html.escape(product['name'])}</h3>
          {stock}
          <table class="specs">{specs_rows}</table>
        </div>
      </a>
    </article>
    """


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def home_page(products: list[dict], categories: list[dict]) -> str:
    lookup = by_slug(products)
    cat_lookup = {c["slug"]: c for c in categories}
    cards = []
    for slug in HOME_CATEGORIES:
        cat = cat_lookup.get(slug)
        if not cat:
            continue
        cards.append(
            f"""<a class="card" href="./product-category/{cat['slug']}/">
              <div class="media"><img src="./{cat['image']}" alt="{html.escape(cat['name'])}"></div>
              <div class="body"><h3>{html.escape(cat['name'])}</h3><p class="count">{cat['count']} products</p></div>
            </a>"""
        )

    def carousel(title: str, slugs: list[str]) -> str:
        items = "".join(product_card(lookup[s], "./") for s in slugs if s in lookup)
        return f"""
        <section class="section">
          <div class="container">
            <div class="section-head"><h2>{html.escape(title)}</h2></div>
            <div class="carousel-wrap" data-carousel>
              <div class="carousel-nav"><button type="button" data-prev aria-label="Previous">‹</button>
              <button type="button" data-next aria-label="Next">›</button></div>
              <div class="carousel-track" data-track>{items}</div>
            </div>
          </div>
        </section>
        """

    body = f"""
    <section class="hero">
      <article class="hero-slide is-active" data-hero-slide style="background-image:linear-gradient(90deg,rgba(0,0,0,.72),rgba(0,0,0,.25)),url('./assets/img/hero-finolex.jpg')">
        <div class="container hero-copy">
          <p class="hero-kicker">Finolex Plumbing System</p>
          <h1>Right Choice For Hot &amp; Cold Water Plumbing System</h1>
          <a class="btn light" href="./shop/">Learn More</a>
        </div>
      </article>
      <article class="hero-slide" data-hero-slide style="background-image:linear-gradient(90deg,rgba(0,0,0,.72),rgba(0,0,0,.25)),url('./assets/img/hero-paras.jpg')">
        <div class="container hero-copy">
          <p class="hero-kicker">Paras Ultra</p>
          <h1>Look at Our Wide Range of Bath faucets</h1>
          <a class="btn light" href="./product-category/bath-fittings/">Learn More</a>
        </div>
      </article>
      <div class="hero-nav">
        <button type="button" data-hero-prev aria-label="Previous slide">‹</button>
        <button type="button" data-hero-next aria-label="Next slide">›</button>
      </div>
    </section>
    <section class="section">
      <div class="container">
        <div class="section-head"><h2>Product Categories</h2><a href="./shop/">All products</a></div>
        <div class="category-grid">{''.join(cards)}</div>
      </div>
    </section>
    {carousel("Our Brands", BRAND_SLUGS)}
    {carousel("House Connection Fittings", HOUSE_SLUGS)}
    {carousel("Valves", VALVE_SLUGS)}
    <section class="section alt">
      <div class="container intro-block">
        <div>
          <h2>Welcome To Tarak Tube Company!</h2>
          <p>{html.escape(COMPANY)} {html.escape(HOME_INTRO)}</p>
        </div>
        <div>
          <a class="btn" href="./about-us/">Read More</a>
        </div>
      </div>
    </section>
    """
    return page_shell("Tarak Tube Co.", "./", body, "home")


def about_page() -> str:
    body = f"""
    <section class="page-hero"><div class="container">
      <p class="crumbs"><a href="../">Home</a> / About us</p>
      <h1>Welcome To Tarak Tube Co</h1>
    </div></section>
    <section class="section"><div class="container">
      <p>{html.escape(COMPANY)}</p>
      <div class="about-grid" style="margin-top:28px">
        <article class="about-card"><h3>Mission</h3><p>{html.escape(MISSION)}</p></article>
        <article class="about-card"><h3>Vision</h3><p>{html.escape(VISION)}</p></article>
        <article class="about-card"><h3>Goals</h3><p>{html.escape(GOALS)}</p></article>
      </div>
    </div></section>
    """
    return page_shell("About us – Tarak Tube Co.", "../", body, "about")


def contact_page() -> str:
    body = """
    <section class="page-hero"><div class="container">
      <p class="crumbs"><a href="../">Home</a> / Contact Us</p>
      <h1>Contact Us</h1>
    </div></section>
    <section class="section"><div class="container contact-grid">
      <article class="contact-card">
        <h2>Tarak Tube Co</h2>
        <p>Taha &amp; Hussain Deesawala</p>
        <p>30, Strand Road, Beside Jessop Company, opposite Armenian Ghat, Kolkata - 700001</p>
        <p><a href="tel:+919831721718">+91 9831721718</a>, <a href="tel:+919831721719">9831721719</a></p>
        <p><a href="mailto:taraktubeco@gmail.com">taraktubeco@gmail.com</a></p>
        <h3>Store Hours:</h3>
        <p>Mon. – Fri: 10:00am - 7:00pm<br>Saturday: 10:00am - 5:00pm<br>Sunday Closed</p>
      </article>
      <article class="contact-card">
        <h2>Drop Us A Line</h2>
        <form class="form" action="mailto:taraktubeco@gmail.com" method="post" enctype="text/plain">
          <label>Your name<input name="name" required></label>
          <label>Your email<input name="email" type="email" required></label>
          <label>Subject<input name="subject" required></label>
          <label>Your message (optional)<textarea name="message"></textarea></label>
          <button class="btn" type="submit">Submit</button>
        </form>
      </article>
    </div></section>
    """
    return page_shell("Contact Us – Tarak Tube Co.", "../", body, "contact")


def shop_page(products: list[dict]) -> str:
    cards = "".join(product_card(p, "../") for p in products)
    body = f"""
    <section class="page-hero"><div class="container">
      <p class="crumbs"><a href="../">Home</a> / Products</p>
      <h1>Products</h1>
      <p class="meta">{len(products)} products</p>
    </div></section>
    <section class="section"><div class="container">
      <div class="product-grid">{cards}</div>
    </div></section>
    """
    return page_shell("Shop – Tarak Tube Co.", "../", body, "shop")


def category_page(category: dict, products: list[dict]) -> str:
    items = [p for p in products if any(c["slug"] == category["slug"] for c in p["categories"])]
    cards = "".join(product_card(p, "../../") for p in items)
    body = f"""
    <section class="page-hero"><div class="container">
      <p class="crumbs"><a href="../../">Home</a> / <a href="../../shop/">Products</a> / {html.escape(category['name'])}</p>
      <h1>{html.escape(category['name'])}</h1>
      <p class="meta">{len(items)} products</p>
    </div></section>
    <section class="section"><div class="container">
      <div class="product-grid">{cards or '<p>No products in this category yet.</p>'}</div>
    </div></section>
    """
    return page_shell(f"{category['name']} – Tarak Tube Co.", "../../", body, "shop")


def product_page(product: dict, products: list[dict]) -> str:
    cat = product["categories"][0]
    rows = "".join(
        f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>" for k, v in product["specs"].items()
    )
    related = [
        p
        for p in products
        if p["slug"] != product["slug"]
        and any(c["slug"] == cat["slug"] for c in p["categories"])
    ][:4]
    related_html = "".join(product_card(p, "../../") for p in related)
    desc = html.escape(product["description"]) if product["description"] else "Contact Tarak Tube Co. for sizes, brands, and current stock."
    wa = f"https://wa.me/919831721718?text={urllib.parse.quote('I would like to enquire about ' + product['name'])}"
    body = f"""
    <section class="page-hero"><div class="container">
      <p class="crumbs"><a href="../../">Home</a> / <a href="../../shop/">Products</a> / <a href="../../product-category/{cat['slug']}/">{html.escape(cat['name'])}</a> / {html.escape(product['name'])}</p>
    </div></section>
    <section class="section"><div class="container product-layout">
      <div class="product-photo"><img src="../../{product['image']}" alt="{html.escape(product['name'])}"></div>
      <div>
        <h1>{html.escape(product['name'])}</h1>
        <p class="meta">{html.escape(product['brand'] or '')} {('· SKU: ' + html.escape(product['sku'])) if product['sku'] else ''}</p>
        <p class="stock">{"In stock" if product["in_stock"] else "Enquire for stock"}</p>
        <table class="specs">{rows}</table>
        <p style="margin-top:20px"><a class="btn" href="{wa}" target="_blank" rel="noopener">Enquire on WhatsApp</a></p>
      </div>
    </div></section>
    <section class="section alt"><div class="container">
      <h2>Description</h2>
      <p>{desc}</p>
      <h3 style="margin-top:24px">Additional information</h3>
      <table class="specs">{rows}</table>
    </div></section>
    <section class="section"><div class="container">
      <div class="section-head"><h2>Related products</h2></div>
      <div class="product-grid">{related_html}</div>
    </div></section>
    """
    return page_shell(f"{product['name']} – Tarak Tube Co.", "../../", body, "shop")


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
        if product["source_image"]:
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
    write(ROOT / "about-us/index.html", about_page())
    write(ROOT / "contact-us/index.html", contact_page())
    write(ROOT / "shop/index.html", shop_page(products))
    for category in categories:
        write(ROOT / f"product-category/{category['slug']}/index.html", category_page(category, products))
    for product in products:
        write(ROOT / f"product/{product['slug']}/index.html", product_page(product, products))
    print(f"Wrote {len(products)} products and {len(categories)} categories")


if __name__ == "__main__":
    main()
