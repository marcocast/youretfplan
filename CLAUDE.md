# youretfplan.com

- Edit only `src/page.html`. It is the single source: markup, CSS and JS, written as a claude.ai artifact fragment (no doctype/head).
- Then run `python3 build.py`. It writes `public/index.html` (English, `/`) and `public/it/index.html` (Italian, `/it/`) with per-language SEO head (title, description, canonical, hreflang, Open Graph, JSON-LD) and pre-rendered text, plus `public/sitemap.xml` and `public/robots.txt`. Commit `public/` together with the source.
- All visible text lives in the `T` object in the script, with `en` and `it` entries. Every copy change must be made in both languages. SEO titles and descriptions live in `build.py`.
- Language: on the site each language has its own URL (`<meta name="page-lang">`). First visit to `/` from Italy (time zone or browser language) redirects once to `/it/`; the EN/IT buttons save the choice. Without the meta tag (artifact copy) the page switches language in place.
- Donate links point to https://buymeacoffee.com/youretfplan.
- Pushing to `main` deploys to production through Cloudflare Workers Builds (static assets from `public/`). Check both pages in a headless browser (phone width, light and dark) before pushing.
- Social preview images `public/og-en.png` and `public/og-it.png` are 1200×630.
- Owner: Marco. He also keeps a copy of the page as a claude.ai artifact; keep it in sync when asked.
