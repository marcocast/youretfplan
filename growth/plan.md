# Growth plan — youretfplan.com

## Goal
- **100,000 active users by 30 September 2027.**
- **Active user** = someone who enters their own numbers in the calculator (not just a page view).
- Intermediate checkpoints to be set once the first month of real data is in.

## Constraints (from Marco)
- No social media posting by Marco. Growth comes from search, word of mouth (users sharing), and links.
- No money spent for now (no ads, no paid tools).
- No donations or paid services until the Beckham-regime tax question is cleared with an asesor fiscal.
- Content changes about finance go through pull requests that Marco approves; small fixes (typos, bugs, speed) can go straight to `main`.

## Roadmap (ideas, in rough priority)
1. Measurement: anonymous "plan created" counter + 👍/👎 feedback box (Cloudflare Worker + D1), daily export to `growth/data/` via GitHub Action, privacy note on the page.
2. ~~Spanish version at `/es/`.~~ Done 2026-10-29.
3. "Share my plan" button that creates an image of the user's result.
4. Comparison subpages (Marco's idea), each with its own calculator and IT/EN/ES versions:
   - Buying a house vs investing in ETFs (casa vs ETF), including the angle "I inherited a house, now what? Keep, rent or sell and invest" (Marco's idea)
   - Bank account vs ETFs, a more specific version of today's comparison
   - Other investments vs ETFs: savings deposit accounts, government bonds (BTP), gold, pension funds…
5. Beginner articles answering common questions, linking to the calculator.
6. Embeddable widget for blogs (earns links).
7. Later (towards end of 2027): pages for specific monthly amounts ("PAC 100 € al mese", "PAC 300 €"…).

## Later: paid services (2028 or later, after the Beckham period — Marco's ideas)
- Premium "connected" version with real data for selected ETFs (prices, history, costs), instead of fixed average returns. Check market-data licensing costs first (index and exchange data is often paid).
- Calculators and guides for special tax regimes for people moving countries (e.g. Spain's Beckham Law, Italy's impatriati regime, Portugal's IFICI). Free guides could already bring expat traffic before any paid version.
- Nothing paid before the tax question is cleared (see Constraints).

## Log
- 2026-10-29: site live at youretfplan.com (EN `/`, IT `/it/`), sitemap submitted to Google Search Console, Cloudflare Web Analytics on, donate button switched off.
- 2026-10-29: Spanish version live at `/es/` (Spain time zone or Spanish browser → `/es/`).
