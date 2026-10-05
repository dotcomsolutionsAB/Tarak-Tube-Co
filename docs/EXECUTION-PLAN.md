# Tarak Tube Co. — Execution Plan

Static HTML rebuild of [https://www.taraktubeco.com](https://www.taraktubeco.com).
WordPress / WooCommerce is the content source. This project is a folder-based static site with clean URLs (no `.html` in the address bar).

## Goals

- Copy live company copy, product catalog, and MegaMarket-like styling.
- Serve every public page as a directory + `index.html`.
- Replace cart/checkout with WhatsApp and contact-form enquiry.
- Drop unused theme dummy widgets (Lorem, Dewalt, Lighting/Flooring).

## Site map

| URL | File | Role |
| --- | --- | --- |
| `/` | `index.html` | Home |
| `/about-us/` | `about-us/index.html` | About |
| `/contact-us/` | `contact-us/index.html` | Contact |
| `/shop/` | `shop/index.html` | All products |
| `/product-category/{slug}/` | `product-category/{slug}/index.html` | Category archive |
| `/product/{slug}/` | `product/{slug}/index.html` | Product detail |
| `/docs/wireframe/` | `docs/wireframe/index.html` | Gray-box wireframe |

## Shared chrome

- Blue header, logo, hamburger, product search
- Mega category menu
- WhatsApp floating button (`https://wa.me/919831721718`)
- Footer: company blurb, Quick Links, categories, address / phone / email
- Copyright: Tarak Tube Co. / Dot Com Solutions

## Page inventory

### Home

1. Hero slider (Finolex plumbing, Paras Ultra bath faucets)
2. Product category cards
3. Brand / featured product carousels
4. Company intro + Read More
5. Footer location strip

### About

Welcome (est. 1993, Burabazar partnership), Mission, Vision, Goals (2500+ customers; Merlin, Srijan, Ekta, Ideal).

### Contact

Owners Taha & Hussain Deesawala; 30 Strand Road, Kolkata 700001; +91 9831721718 / 9831721719; store hours; Drop Us A Line form (mailto / WhatsApp).

### Catalog

Shop grid, category archives, product pages (image, title, brand, SKU, specs, description, Enquire CTA, related products). Client-side search against `data/products.json`.

## Clean URL rules

- Never link to `*.html`.
- Every public URL is a folder with `index.html`.
- `.htaccess` sets `DirectoryIndex index.html`.
- Local preview: `npx serve .`

## Visual tokens

| Token | Value |
| --- | --- |
| Brand blue | `#2B4FE0` |
| Blue dark | `#1E3AB8` |
| Hero black | `#0B0B0B` |
| Text | `#1A1A1A` |
| Muted | `#5C6470` |
| Border | `#E6E8EE` |
| Surface | `#F5F6F8` |
| WhatsApp | `#25D366` |

Type: Inter / system sans.

## Build sequence

1. Store this plan and the browsable wireframe.
2. Foundation: tokens, chrome, partials, include script, `.htaccess`.
3. Core pages: Home, About, Contact.
4. Catalog data + images from the live site.
5. Shop, category, product, search.
6. Browser verification of routes, clean URLs, mobile chrome, enquiry flows.

## Out of scope

- WordPress, PHP, WooCommerce cart/checkout
- Pixel-cloning unused theme dummy widgets
- CMS / admin
- Production hosting deploy
