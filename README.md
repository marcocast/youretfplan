# Your ETF Plan

Source of [youretfplan.com](https://youretfplan.com): a free page in English, Italian and Spanish that explains ETF investing to beginners and shows what a monthly plan could grow into.

- `src/page.html` is the source of the page.
- `python3 build.py` builds `public/` (English at `/`, Italian at `/it/`, Spanish at `/es/`, sitemap, robots). Needs Playwright with Chromium.
- `wrangler.jsonc` tells Cloudflare Workers to serve the `public` folder.
- Every push to `main` is deployed automatically by Cloudflare.
