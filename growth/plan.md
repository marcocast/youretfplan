# Growth plan — youretfplan.com

## Goal
- **100,000 active users by 30 September 2027.**
- **Active user** = someone who enters their own numbers in the calculator (not just a page view).
- Intermediate checkpoints to be set once the first month of real data is in.

## Constraints (from Marco)
- No social media posting by Marco. Growth comes from search, word of mouth (users sharing), and links.
- No money spent for now (no ads, no paid tools).
- No donations or paid services until the Beckham-regime tax question is cleared with an asesor fiscal.
- Audience (Marco, 2026-10-30): not only young beginners but also adults and retirees. The current illustrated design may speak mostly to young people; revisit later (e.g. a calmer variant or sections for people with savings already).
- Content changes about finance go through pull requests that Marco approves; small fixes (typos, bugs, speed) can go straight to `main`.

## Roadmap (ideas, in rough priority)
1. ~~Measurement~~ (counter and feedback live 2026-10-29; daily export pending): anonymous "plan created" counter + 👍/👎 feedback box (Cloudflare Worker + D1), daily export to `growth/data/` via GitHub Action, privacy note on the page.
2. ~~Spanish version at `/es/`.~~ Done 2026-10-29.
3. "Share my plan" button that creates an image of the user's result.
4. Comparison subpages (Marco's idea), each with its own calculator and IT/EN/ES versions:
   - Buying a house vs investing in ETFs (casa vs ETF), including the angle "I inherited a house, now what? Keep, rent or sell and invest" (Marco's idea)
   - Bank account vs ETFs, a more specific version of today's comparison
   - Other investments vs ETFs: savings deposit accounts, government bonds (BTP), gold, pension funds…
5. Beginner articles answering common questions, linking to the calculator.
5b. Free guide "Investing in ETFs under the Beckham Law" (Marco's angle: always tied to what the regime means for ETF investors). Points to cover, each verified against current sources before publishing:
   - Foreign-source gains and dividends are not taxed in Spain during the regime, so non-Spanish-domiciled ETFs (e.g. Irish ISIN IE…) are in practice tax-free in Spain while it lasts; Spanish-source investments are still taxed.
   - No Modelo 720 while the regime applies (DGT position), as long as the regime is valid.
   - The trap at the end: after the 6 years you become an ordinary resident and later sales are taxed on the whole gain, so the timing of sales before the regime ends matters.
   - Wealth tax and the end-of-regime planning need an asesor; the page says so clearly.
   - Same pattern later for Italy (impatriati) and Portugal (IFICI).
6. Embeddable widget for blogs (earns links).
7. Later (towards end of 2027): pages for specific monthly amounts ("PAC 100 € al mese", "PAC 300 €"…).

## Later: paid services (2028 or later, after the Beckham period — Marco's ideas)
- Premium "connected" version with real data for selected ETFs (prices, history, costs), instead of fixed average returns. Check market-data licensing costs first (index and exchange data is often paid).
- Calculators and guides for special tax regimes for people moving countries (e.g. Spain's Beckham Law, Italy's impatriati regime, Portugal's IFICI). Free guides could already bring expat traffic before any paid version.
- Nothing paid before the tax question is cleared (see Constraints).

## Log
- 2026-10-29: site live at youretfplan.com (EN `/`, IT `/it/`), sitemap submitted to Google Search Console, Cloudflare Web Analytics on, donate button switched off.
- 2026-10-29: Spanish version live at `/es/` (Spain time zone or Spanish browser → `/es/`).
- 2026-10-29: anonymous funnel counter and feedback (after results + bottom) live via Worker + D1; privacy line added.

## Scenario pages (agreed with Marco 2026-10-30)
Order: 1) money in the bank vs investing in ETFs (live), 2) buy your home vs rent and invest in ETFs (live), 3) inheritance (money or a house), 4) I own a house: rent it or sell and invest in ETFs, 5) buy a home to rent out vs invest in ETFs (Marco's idea, shares the calculator with 4). Each has its own page per language, its own calculator, a card on the main page, and verified country-specific tax notes. Always say "investing in ETFs".
