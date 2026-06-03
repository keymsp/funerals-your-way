#!/usr/bin/env python3
"""
Funerals Your Way — static site generator.
Reads pages/*.md (YAML front-matter + Markdown body) and renders a complete,
SEO-optimised static site into docs/ (served by GitHub Pages).
"""
import os, re, json, shutil, html, datetime
import yaml
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES_DIR = os.path.join(ROOT, "pages")
OUT = os.path.join(ROOT, "docs")
ASSETS_SRC = os.path.join(ROOT, "assets")

# ---------------------------------------------------------------- site config
LIVE_DOMAIN = "https://funeralsyourway.com"   # canonical target (the real site)
DEMO_NOINDEX = True   # keep the GitHub Pages preview out of search results
                      # (flip to False when this becomes the live site)
BASEURL = "/funerals-your-way"   # GitHub Pages project subpath; set to "" for a
                                 # root domain (custom domain or user/org pages site)

SITE = {
    "name": "Funerals Your Way",
    "tagline": "San Diego Funeral Home",
    "fd": "FD #2188",
    "phone": "619-550-7807",
    "tel": "+16195507807",
    "fax": "619-330-1832",
    "street": "7932 Convoy Ct.",
    "city": "San Diego",
    "region": "CA",
    "zip": "92111",
    "lat": 32.8252,
    "lng": -117.1609,
    "price_range": "$$",
    "logo": "https://funeralsyourway.com/wp-content/uploads/FYW-logo-transparent.png",
    "og_default": "https://funeralsyourway.com/wp-content/uploads/point-loma-lighthouse-san-diego.webp",
    "gpl_pdf": "https://funeralsyourway.com/wp-content/uploads/fyw-gpl-01-01-2026a.pdf",
    "consumer_pdf": "https://funeralsyourway.com/wp-content/uploads/consumer_guide-2024.pdf",
    "shop": "https://funeralsyourwayvmei.crescentmemorial.com/",
    "social": {
        "Facebook": "https://www.facebook.com/FuneralsYourWay",
        "YouTube": "https://www.youtube.com/channel/UC4rvAJXhC3LNW3aHWkAAO1w/videos",
        "LinkedIn": "https://www.linkedin.com/company/funerals-your-way/",
        "Pinterest": "https://www.pinterest.com/funeralsyourway/",
        "Instagram": "https://www.instagram.com/funeralsyourway/",
    },
}
SOCIAL_ICONS = {"Facebook": "f", "YouTube": "▶", "LinkedIn": "in", "Pinterest": "P", "Instagram": "◎"}

# Top utility bar links
TOPBAR = [
    ("Obituaries", "/obituaries/"), ("Videos", "/funeral-videos/"),
    ("Blog", "/funerals-your-way-blog/"), ("Shop", SITE["shop"]),
    ("Reviews", "/client-testimonials/"),
]

# Primary navigation (mega menu)
NAV = [
    {"label": "Cremation", "children": [
        ("Cremation Packages", "/cremation/"),
        ("Pre-Need Planning", "/pre-need-funeral-planning/"),
        ("Memorial Services", "/san-diego-memorial-services/"),
        ("What to Do – Cremains", "/what-to-do-with-cremains/"),
    ]},
    {"label": "Burial", "children": [
        ("Burial Packages", "/burial/"),
        ("Pre-Need Planning", "/pre-need-funeral-planning/"),
        ("Muslim Burial", "/san-diego-muslim-burial/"),
        ("San Diego Cemeteries", "/san-diego-cemeteries/"),
    ]},
    {"label": "Green", "children": [
        ("Organic Reduction (NOR)", "/natural-organic-reduction/"),
        ("Green Burial", "/green-burial/"),
        ("Full-Body Sea Burial", "/full-body-burial-at-sea/"),
    ]},
    {"label": "Transport", "children": [
        ("Shipping Overview", "/shipping-human-remains/"),
        ("Shipping Nationally", "/shipping-human-remains-nationally/"),
        ("Shipping to Mexico", "/shipping-to-mexico/"),
        ("Shipping to Philippines", "/ship-body-to-philippines/"),
        ("Shipping International", "/shipping-internationally/"),
    ]},
    {"label": "Veteran", "children": [
        ("Veteran Funerals", "/san-diego-veteran-funerals/"),
        ("Veteran Cremation", "/san-diego-veteran-cremation/"),
        ("Veteran Burial", "/san-diego-veteran-burial-services/"),
        ("Veteran Headstones", "/veteran-headstones-grave-markers-san-diego/"),
        ("Military Honors", "/veteran-military-honors/"),
        ("National Cemeteries", "/national-cemetery/"),
        ("Miramar National", "/miramar-national-cemetery/"),
        ("Veteran Resources", "/veteran-resources/"),
    ]},
    {"label": "Sea", "children": [
        ("Sea Burial Overview", "/burial-at-sea-overview/"),
        ("Ash Scattering at Sea", "/san-diego-burial-at-sea/"),
        ("Full-Body Burial at Sea", "/full-body-burial-at-sea/"),
        ("What to Expect", "/burial-at-sea-what-to-expect/"),
        ("Biodegradable Urns", "/biodegradable-urns-burial-sea/"),
        ("Flowers & Wreaths", "/sea-burial-flowers/"),
        ("Sea Burial Gallery", "/sea-burial-photo-gallery/"),
    ]},
    {"label": "More", "children": [
        ("About Us", "/about-us/"),
        ("Contact Us", "/contact-us/"),
        ("Aftercare Program", "/aftercare-module-overview/"),
        ("Body Donation", "/body-donation/"),
        ("Tree Planting", "/tree-planting/"),
        ("When a Death Occurs", "/when-a-death-occurs/"),
        ("FAQ", "/funeral-q-a/"),
    ]},
]

FOOTER_SERVICES = [
    ("Funeral Services", "/san-diego-funeral-services/"),
    ("Cremation", "/cremation/"),
    ("Burial", "/burial/"),
    ("Veteran Services", "/veteran-military-honors/"),
    ("Burial at Sea", "/san-diego-burial-at-sea/"),
    ("Transportation", "/shipping-human-remains-nationally/"),
]
FOOTER_LOCATIONS = [
    ("San Diego", "/san-diego-cremation/"),
    ("Chula Vista", "/chula-vista-cremation/"),
    ("El Centro", "/el-centro-cremation/"),
    ("Alpine", "/alpine-cremation/"),
    ("El Cajon", "/el-cajon-cremation/"),
    ("Oceanside", "/oceanside-cremation/"),
]

md = markdown.Markdown(extensions=["extra", "sane_lists", "smarty", "toc", "attr_list"],
                       output_format="html5")

ROUTES = set(["/"])  # populated in main() before rendering

def fix_internal_links(html_str):
    """Any root-relative link whose target isn't a page we built falls back to
    the live site, so the preview never 404s on not-yet-migrated content."""
    def repl(m):
        href = m.group(1)
        if href.startswith("/assets") or href in ("/sitemap.xml", "/robots.txt"):
            return m.group(0)
        route = href if href.endswith("/") else href + "/"
        if href in ROUTES or route in ROUTES:
            return m.group(0)
        return 'href="' + LIVE_DOMAIN + href + '"'
    return re.sub(r'href="(/[^"#]*)"', repl, html_str)

def apply_baseurl(html_str):
    """Prefix remaining root-relative URLs (our own pages + assets) with BASEURL so
    the site works when served from a GitHub Pages project subpath."""
    if not BASEURL:
        return html_str
    return re.sub(r'(href|src)="(/[^"#]*)"',
                  lambda m: f'{m.group(1)}="{BASEURL}{m.group(2)}"', html_str)

# ---------------------------------------------------------------- helpers
def parse_page(path):
    raw = open(path, encoding="utf-8").read()
    fm, body = {}, raw
    if raw.startswith("---"):
        _, front, body = raw.split("---", 2)
        fm = yaml.safe_load(front) or {}
    fm["_body"] = body.strip()
    return fm

def url_for(slug):
    slug = (slug or "").strip("/")
    return "/" if slug == "" else f"/{slug}/"

def page_html_path(slug):
    slug = (slug or "").strip("/")
    return os.path.join(OUT, "index.html") if slug == "" else os.path.join(OUT, slug, "index.html")

def esc(s): return html.escape(str(s), quote=True)

# ---------------------------------------------------------------- chrome (header/footer)
def render_topbar():
    links = "".join(
        f'<a href="{esc(u)}"{" target=_blank rel=noopener" if u.startswith("http") else ""}>{esc(l)}</a>'
        for l, u in TOPBAR)
    return f'''<div class="topbar"><div class="container">
      <div class="tb-links">{links}</div>
      <a class="tb-phone" href="tel:{SITE['tel']}">📞 {SITE['phone']} · Available 24/7</a>
    </div></div>'''

def render_header():
    items = ['<li><a href="/" aria-label="Home">Home</a></li>']
    for m in NAV:
        kids = "".join(f'<li><a href="{esc(u)}">{esc(l)}</a></li>' for l, u in m["children"])
        items.append(
            f'<li class="has-mega"><a href="#" aria-haspopup="true">{esc(m["label"])}'
            f'<span class="caret">▼</span></a><div class="mega"><ul>{kids}</ul></div></li>')
    desktop = "".join(items)
    return f'''<header class="site-header"><div class="container"><div class="header-inner">
      <a class="brand" href="/">
        <img src="{SITE['logo']}" alt="Funerals Your Way logo" width="160" height="52" loading="eager">
      </a>
      <nav class="primary-nav" aria-label="Primary"><ul>{desktop}</ul></nav>
      <div class="nav-cta">
        <a class="btn btn-brass" href="tel:{SITE['tel']}">Call 24/7</a>
        <button class="btn nav-toggle" id="navToggle" aria-label="Open menu" aria-expanded="false">☰</button>
      </div>
    </div></div>{render_mobile_nav()}</header>'''

def render_mobile_nav():
    groups = ['<li class="m-flat"><a href="/">Home</a></li>']
    for m in NAV:
        kids = "".join(f'<a href="{esc(u)}">{esc(l)}</a>' for l, u in m["children"])
        groups.append(
            f'<li class="m-group"><button aria-expanded="false">{esc(m["label"])}<span>＋</span></button>'
            f'<div class="m-sub">{kids}</div></li>')
    for l, u in TOPBAR:
        tgt = " target=_blank rel=noopener" if u.startswith("http") else ""
        groups.append(f'<li class="m-flat"><a href="{esc(u)}"{tgt}>{esc(l)}</a></li>')
    return f'''<div class="mobile-nav" id="mobileNav"><ul>{"".join(groups)}
      <li class="m-cta"><a class="btn btn-brass btn-lg" href="tel:{SITE['tel']}">📞 Call {SITE['phone']}</a></li>
    </ul></div>'''

def render_footer():
    svc = "".join(f'<li><a href="{esc(u)}">{esc(l)}</a></li>' for l, u in FOOTER_SERVICES)
    loc = "".join(f'<li><a href="{esc(u)}">{esc(l)}</a></li>' for l, u in FOOTER_LOCATIONS)
    soc = "".join(
        f'<a href="{esc(u)}" target="_blank" rel="noopener" aria-label="{esc(n)}" title="{esc(n)}">{SOCIAL_ICONS[n]}</a>'
        for n, u in SITE["social"].items())
    year = datetime.date.today().year
    return f'''<footer class="site-footer"><div class="container"><div class="footer-grid">
      <div class="footer-brand">
        <img src="{SITE['logo']}" alt="Funerals Your Way logo">
        <p>A locally owned San Diego funeral home ({SITE['fd']}) providing cremation, burial,
           veteran, and memorial services with transparent pricing and compassionate, no-pressure guidance.</p>
        <div class="footer-social">{soc}</div>
      </div>
      <div><h4>Services</h4><ul>{svc}</ul></div>
      <div><h4>Locations Served</h4><ul>{loc}</ul></div>
      <div>
        <h4>Our Location</h4>
        <p>{SITE['name']} ({SITE['fd']})<br>{SITE['street']}<br>{SITE['city']}, {SITE['region']} {SITE['zip']}</p>
        <p><a href="tel:{SITE['tel']}">{SITE['phone']}</a><br><span style="color:#9C9684">Funeral Director available 24 hours</span></p>
        <h4 style="margin-top:1.2rem">Guides</h4>
        <ul>
          <li><a href="{SITE['gpl_pdf']}" target="_blank" rel="noopener">General Price List (GPL)</a></li>
          <li><a href="{SITE['consumer_pdf']}" target="_blank" rel="noopener">Consumer Guide to Funeral Purchases</a></li>
        </ul>
      </div>
    </div></div>
    <div class="footer-bottom"><div class="container">
      <span>© {year} {SITE['name']} · {SITE['fd']} · {SITE['street']}, {SITE['city']}, {SITE['region']} {SITE['zip']}</span>
      <span><a href="/privacy-policy/">Privacy</a> · <a href="/terms-of-service/">Terms</a> · <a href="/accessibility-statement/">Accessibility</a></span>
    </div></div></footer>
    <a class="call-fab" href="tel:{SITE['tel']}">📞 Call 24/7</a>'''

# ---------------------------------------------------------------- JSON-LD
def org_schema():
    return {
        "@context": "https://schema.org", "@type": "FuneralHome",
        "@id": LIVE_DOMAIN + "/#org", "name": SITE["name"],
        "url": LIVE_DOMAIN + "/", "logo": SITE["logo"], "image": SITE["og_default"],
        "telephone": SITE["phone"], "faxNumber": SITE["fax"], "priceRange": SITE["price_range"],
        "address": {"@type": "PostalAddress", "streetAddress": SITE["street"],
                    "addressLocality": SITE["city"], "addressRegion": SITE["region"],
                    "postalCode": SITE["zip"], "addressCountry": "US"},
        "geo": {"@type": "GeoCoordinates", "latitude": SITE["lat"], "longitude": SITE["lng"]},
        "areaServed": {"@type": "AdministrativeArea", "name": "San Diego County, California"},
        "openingHoursSpecification": {"@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            "opens": "00:00", "closes": "23:59"},
        "sameAs": list(SITE["social"].values()),
        "aggregateRating": {"@type": "AggregateRating", "ratingValue": "5.0", "reviewCount": "220"},
    }

def breadcrumb_schema(page):
    crumbs = [("Home", LIVE_DOMAIN + "/")]
    parent = page.get("breadcrumb_parent")
    if parent and "|" in str(parent):
        plabel, purl = str(parent).split("|", 1)
        crumbs.append((plabel.strip(), LIVE_DOMAIN + url_for(purl.strip())))
    crumbs.append((page.get("h1") or page.get("title"), LIVE_DOMAIN + url_for(page["slug"])))
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u}
                                for i, (n, u) in enumerate(crumbs)]}

def page_schemas(page):
    out = [org_schema(), breadcrumb_schema(page)]
    st = page.get("schema_type", "WebPage")
    if st == "Service":
        out.append({"@context": "https://schema.org", "@type": "Service",
            "name": page.get("schema_service") or page.get("h1"),
            "serviceType": page.get("schema_service") or page.get("h1"),
            "provider": {"@id": LIVE_DOMAIN + "/#org"},
            "areaServed": "San Diego County, CA",
            "url": LIVE_DOMAIN + url_for(page["slug"]),
            "description": page.get("description", "")})
    if page.get("faqs"):
        out.append({"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": f["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                           for f in page["faqs"]]})
    return out

# ---------------------------------------------------------------- rendering
def render_breadcrumb(page):
    if page.get("hide_breadcrumb") or (page.get("slug") or "").strip("/") == "":
        return ""
    items = [f'<li><a href="/">Home</a></li>']
    parent = page.get("breadcrumb_parent")
    if parent and "|" in str(parent):
        plabel, purl = str(parent).split("|", 1)
        items.append(f'<li><a href="{esc(url_for(purl.strip()))}">{esc(plabel.strip())}</a></li>')
    items.append(f'<li>{esc(page.get("h1") or page.get("title"))}</li>')
    return f'<nav class="breadcrumb" aria-label="Breadcrumb"><div class="container"><ol>{"".join(items)}</ol></div></nav>'

def render_faqs(page):
    if not page.get("faqs"):
        return ""
    rows = "".join(
        f'<details class="quote" style="margin-bottom:.8rem"><summary style="cursor:pointer;font-weight:700;color:var(--green-900);font-family:var(--serif);font-size:1.1rem">{esc(f["q"])}</summary>'
        f'<div style="margin-top:.6rem">{md.reset().convert(f["a"])}</div></details>'
        for f in page["faqs"])
    return f'<section class="section--tight"><div class="container narrow"><h2>Frequently Asked Questions</h2>{rows}</div></section>'

def render_hero(page):
    style = page.get("hero_style", "page")
    h1 = esc(page.get("h1") or page.get("title"))
    intro = page.get("intro", "")
    img = page.get("hero_image")
    bg = f'<img class="hero-bg" src="{esc(img)}" alt="" aria-hidden="true" loading="eager">' if img else ""
    if style == "home":
        return ""  # home authors its own hero in body
    intro_html = f"<p>{esc(intro)}</p>" if intro else ""
    return f'''<section class="page-hero">{bg}<div class="container">
      <h1>{h1}</h1>{intro_html}
    </div></section>'''

PAGE_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
{robots}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Funerals Your Way">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_image}">
<meta name="theme-color" content="#2C463A">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/style.css">
{schema}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{topbar}
{header}
<main id="main">
{breadcrumb}
{hero}
{content}
{faqs}
</main>
{footer}
<script src="/assets/js/main.js" defer></script>
</body>
</html>
"""

def build_page(page):
    slug = page.get("slug", "")
    title = page.get("title") or page.get("h1") or SITE["name"]
    desc = page.get("description", "")
    canonical = LIVE_DOMAIN + url_for(slug)
    og_image = page.get("og_image") or page.get("hero_image") or SITE["og_default"]
    robots = '<meta name="robots" content="noindex,follow">' if DEMO_NOINDEX else '<meta name="robots" content="index,follow,max-image-preview:large">'
    schema = "\n".join(
        f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>'
        for s in page_schemas(page))
    body_html = md.reset().convert(page["_body"])
    full = page.get("layout") == "full" or page.get("hero_style") == "home"
    if full:
        content = body_html            # author owns the full-bleed section layout
        hero_html = ""
    else:
        content = f'<section class="section"><div class="container"><div class="prose narrow">{body_html}</div></div></section>'
        hero_html = render_hero(page)
    out = PAGE_TMPL.format(
        title=esc(title), desc=esc(desc), canonical=esc(canonical), robots=robots,
        og_type=("website" if slug.strip("/") == "" else "article"),
        og_image=esc(og_image), schema=schema, topbar=render_topbar(), header=render_header(),
        breadcrumb=render_breadcrumb(page), hero=hero_html,
        content=content, faqs=render_faqs(page), footer=render_footer())
    out = apply_baseurl(fix_internal_links(out))
    dest = page_html_path(slug)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(out)
    return slug, page.get("lastmod", datetime.date.today().isoformat()), page.get("priority", "0.7")

# ---------------------------------------------------------------- site files
def write_sitemap(entries):
    rows = ""
    for slug, lastmod, prio in entries:
        rows += (f"  <url><loc>{LIVE_DOMAIN}{url_for(slug)}</loc>"
                 f"<lastmod>{lastmod}</lastmod><priority>{prio}</priority></url>\n")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f"{rows}</urlset>\n")
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(xml)

def write_robots():
    if DEMO_NOINDEX:
        txt = "User-agent: *\nDisallow: /\n"  # keep preview out of search
    else:
        txt = f"User-agent: *\nAllow: /\n\nSitemap: {LIVE_DOMAIN}/sitemap.xml\n"
    open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(txt)

def write_favicon():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect width="64" height="64" rx="12" fill="#2C463A"/>'
           '<path d="M32 12c-7 9-12 15-12 22a12 12 0 0 0 24 0c0-7-5-13-12-22z" fill="#B08D57"/>'
           '<rect x="30" y="30" width="4" height="22" rx="2" fill="#F7F2E9"/>'
           '<rect x="22" y="38" width="20" height="4" rx="2" fill="#F7F2E9"/></svg>')
    open(os.path.join(OUT, "assets", "favicon.svg"), "w", encoding="utf-8").write(svg)

def write_404():
    page = {"slug": "404", "title": "Page Not Found | Funerals Your Way",
            "description": "The page you were looking for could not be found.",
            "h1": "We couldn't find that page", "hide_breadcrumb": True,
            "intro": "The page may have moved. Please use the menu above or call us any time.",
            "_body": ('<section class="section"><div class="container narrow text-center">'
                      '<p class="lead">Try one of these instead:</p>'
                      '<p class="center-btns"><a class="btn btn-primary" href="/">Home</a>'
                      '<a class="btn btn-ghost" href="/cremation/">Cremation</a>'
                      '<a class="btn btn-ghost" href="/burial/">Burial</a>'
                      '<a class="btn btn-ghost" href="/contact-us/">Contact</a></p>'
                      f'<p class="mt-3"><a class="cta-phone" href="tel:{SITE["tel"]}">📞 {SITE["phone"]}</a></p>'
                      '</div></section>')}
    html_out = PAGE_TMPL.format(
        title=esc(page["title"]), desc=esc(page["description"]),
        canonical=esc(LIVE_DOMAIN + "/404"), robots='<meta name="robots" content="noindex">',
        og_type="website", og_image=esc(SITE["og_default"]),
        schema=f'<script type="application/ld+json">{json.dumps(org_schema())}</script>',
        topbar=render_topbar(), header=render_header(), breadcrumb="",
        hero=render_hero(page), content=page["_body"], faqs="", footer=render_footer())
    html_out = apply_baseurl(fix_internal_links(html_out))
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(html_out)

def clean_out():
    """Remove generated files without rmdir-ing (cloud mounts forbid rmdir)."""
    os.makedirs(OUT, exist_ok=True)
    for root, dirs, files in os.walk(OUT, topdown=False):
        for f in files:
            try: os.remove(os.path.join(root, f))
            except OSError: pass
        for d in dirs:
            try: os.rmdir(os.path.join(root, d))
            except OSError: pass

def copy_assets():
    for root, _dirs, files in os.walk(ASSETS_SRC):
        rel = os.path.relpath(root, ASSETS_SRC)
        dest = os.path.join(OUT, "assets") if rel == "." else os.path.join(OUT, "assets", rel)
        os.makedirs(dest, exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(root, f), os.path.join(dest, f))

def main():
    clean_out()
    copy_assets()
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    files = sorted(f for f in os.listdir(PAGES_DIR) if f.endswith(".md"))
    parsed = []
    for f in files:
        page = parse_page(os.path.join(PAGES_DIR, f))
        if "slug" not in page:
            page["slug"] = os.path.splitext(f)[0]
        parsed.append(page)
        ROUTES.add(url_for(page["slug"]))
    entries = [build_page(page) for page in parsed]
    write_favicon()
    write_sitemap(entries)
    write_robots()
    write_404()
    print(f"Built {len(entries)} pages -> {OUT}")
    print("noindex(demo)=" + str(DEMO_NOINDEX))

if __name__ == "__main__":
    main()
