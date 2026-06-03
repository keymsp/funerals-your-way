# Funerals Your Way — Website Redesign

A full redesign of [funeralsyourway.com](https://funeralsyourway.com) — a licensed San Diego
funeral home (FD #2188). This is a fast, static, SEO-optimized rebuild of the existing site with a
**warm & traditional** look (deep sage green + warm cream + brass, Lora serif headings). All page
copy is migrated from the live site; the structure, services, pricing, and SEO are preserved and improved.

**Live preview:** _(GitHub Pages URL added after deploy)_

## How it works

This is a small static-site generator — no database, no build dependencies beyond Python.

```
pages/        One Markdown file per page (YAML front-matter + body). 57 pages.
assets/       css/style.css (design system), js/main.js (mobile nav), favicon
scripts/build.py   Renders pages/ -> docs/ with full SEO + structured data
docs/         The generated site (this is what GitHub Pages serves)
```

### Build

```bash
python3 scripts/build.py
```

Outputs the complete site into `docs/`. GitHub Pages is configured to serve from the
`main` branch `/docs` folder.

## What's improved for SEO

- Clean semantic HTML5, fast static pages (no WordPress/page-builder bloat), mobile-first.
- Per-page `<title>`, meta description, and **canonical** tags.
- **Structured data (JSON-LD)** on every page: `FuneralHome` (NAP, geo, 24/7 hours, socials,
  aggregate rating), `BreadcrumbList`, `Service` on service pages, and `FAQPage` on the FAQ.
- Open Graph + Twitter Card tags for rich social sharing.
- Auto-generated `sitemap.xml`, `robots.txt`, custom `404.html`, and a favicon.
- Original URL slugs are preserved (e.g. `/cremation/`, `/san-diego-veteran-cremation/`) so existing
  search rankings and inbound links carry over when this replaces the live site.
- Descriptive image `alt` text retained from the source.

## Important notes

- **Search-engine indexing is OFF for this preview.** In `scripts/build.py`, `DEMO_NOINDEX = True`
  adds `noindex` and a blocking `robots.txt` so this GitHub Pages copy does **not** compete with the
  live funeralsyourway.com in Google. **When this becomes the real site, set `DEMO_NOINDEX = False`,
  rebuild, and (ideally) point the domain at it.** Canonicals already point at `funeralsyourway.com`.
- **Images** are currently hot-linked from `funeralsyourway.com/wp-content/...` so the preview shows
  real photography without re-hosting. Before go-live, download them into `assets/img/` and update paths.
- **Links to content not yet migrated** (individual blog posts, obituaries, a few sub-pages) fall back
  to the live site automatically, so nothing 404s in the preview.
- **The contact form** is presented but not wired to a backend (GitHub Pages is static). Connect it to
  the existing form handler (e.g. Gravity Forms / a form service) at go-live.

_Built for Key MSP. Content © Funerals Your Way._
