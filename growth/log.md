# Growth log — youretfplan.com

One dated entry per daily growth session. Newest at the bottom.

## 2026-10-29 (setup)
- Site live in EN, IT, ES. Google Search Console: sitemap submitted (3 pages). Cloudflare Web Analytics on.
- Anonymous funnel counter and feedback live (Worker + D1). Daily export Action added; needs the `CLOUDFLARE_API_TOKEN` repo secret.
- Daily growth session scheduled at 08:49 Madrid time.
- No data yet. First real numbers expected from the 2026-10-30 export.
- Sliders added for salary, spending, savings and the monthly ETF amount (Marco's request: faster on phones). Moving a slider counts as `active`.
- Evening: Marco felt the page isn't catchy for first-time investors. Built a hook-first preview at /v2/ (one question, monthly-savings and age sliders, big animated result at 60 with 5–9% range, invest-vs-bank bars, second-salary line, 3 short points, honest risk note, CTA to the full plan). Not indexed, no tracking. Waiting for Marco's verdict before replacing the main page; then compare the `active` rate before/after.
- Marco on /v2/: "not bad", but showing "at 60" may scare people in their 30s. On hold while he thinks. Idea to try: replace age with near milestones (in 5 / 10 / 20 years, default 10) so the first number feels close.

## 2026-10-30
- **No data yet.** The 04:30 UTC scheduled export did not fire (first schedule of a new workflow; GitHub often skips it). Triggered it by hand: [run 41022593671](https://github.com/marcocast/youretfplan/actions/runs/41022593671) succeeded but every source failed with `missing settings: CF_API_TOKEN` → the repo secret `CLOUDFLARE_API_TOKEN` is not set. Blocked on Marco.
- Token needs: Account → D1 → Read, and Account → Account Analytics → Read, for account f133aba3…0908. Save as repo secret `CLOUDFLARE_API_TOKEN` (Settings → Secrets and variables → Actions), then re-run "Daily data export".
- Key numbers: none (active yesterday / 7d / MTD unknown). Pace needed for 100k by 2027-09-30: ~299 active users/day on average (334 days left).
- Funnel / feedback: no data.
- Checked `/`, `/it/`, `/es/` locally at 390px, light and dark: 200, no horizontal overflow, no JS errors (only the blocked analytics beacon). The live site is not reachable from the session sandbox.
- Changed: nothing on the site. Without data, and with /v2/ on hold for Marco's decision, no funnel change today.
- Watch tomorrow: first real export (if the secret is set); confirm the scheduled 04:30 UTC run fires.
- **Update 09:20 Madrid:** Marco added `CLOUDFLARE_API_TOKEN` (D1 Read + Account Analytics Read, no expiry, no IP filter). Re-run of the export succeeded with no errors.
- First numbers (launch day 2026-10-29, mostly Marco and testers): funnel view 16 → calc_seen 15 → active 3 → explore 4, start_seen 8, bottom 7, feedback 2. Today so far: view 4, active 0. Month to date: 3 active user-days.
- Biggest drop: calc_seen → active (15 → 3, 20%). Too few visitors to read anything by language/device yet.
- Web Analytics 7d: 55 visits, all direct (no search referrers yet); US 25 visits with no referrer probably bots/crawlers. Mobile 27, desktop 26.
- Feedback: 3 votes on "is this result clear?": 2 👍 (IT, mobile), 1 👎 (EN, mobile, DE), no comments.
- **Change (PR, needs Marco):** Marco decided to use the /v2/ hook as the top of the main page, with no age (5/10/20 years, default 10), and the full calculator below. [PR #1](https://github.com/marcocast/youretfplan/pull/1). Moving the hook counts as `active` (Marco agreed) plus a new `hook` step. Why: the biggest drop is calc_seen → active (20%), and the hook asks for a single number above the fold.
- Watch after merge: active/view rate (baseline 3/16 on 29 Oct), hook → calc_seen → explore, and 👍/👎 on the result.
- Merged PR #1 at Marco's request (squash 7dc25a9). The Workers Builds check on the PR branch failed instantly (0 s, preview build), while `wrangler deploy --dry-run` passes locally. Production deploy from main still needs a check on the live site.
- Marco: the new top still looks amateur, with no goal. Agreed direction: "your first ETF plan in 10 minutes" + illustrations. Built preview at /v3/ (noindex, no tracking): 3 questions (spend, bank, monthly) → one-page plan (cushion, invest now, monthly, which ETF, where) + growing tree for 5/10/20 years. Waiting for his verdict.
- **Main page = /v3/ design** (Marco: "metti tutto sulla pagina principale"). Top of `/`, `/it/`, `/es/`: guided 3 questions → one-page plan with illustrations and the "made by Marco for his brother" card; full calculator and guide stay below with the new palette and fonts. Answers carry into the full calculator (salary = spending + monthly, ETF = monthly). "How to start" ETF step reworded as criteria/example, not a recommendation. Funnel: new steps `hook` (clicked start) and `plan` (reached the plan); `active` = moved any slider. The PR #1 hook is replaced. Coffee/support section hidden while donations are off (the who card replaces it).
- Marco's note: targets include adults and retirees, not just young people; the design may feel young. Added to growth/plan.md to revisit.
- Watch: view → hook → active → plan, and plan → calc_seen/explore.
