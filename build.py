#!/usr/bin/env python3
"""Build the static site from src/page.html.

Writes public/index.html (English) and public/it/index.html (Italian). Each page gets its
own <head> for search engines (title, description, canonical, hreflang, Open Graph,
JSON-LD), and the visible text is pre-rendered into the HTML with a headless browser so
crawlers and link previews see real content. The page script still runs in the browser
and keeps everything interactive.

Usage: python3 build.py     (needs Playwright with Chromium)
"""
import asyncio
import html
import json
import pathlib
import re

from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src" / "page.html"
PUBLIC = ROOT / "public"
SITE = "https://youretfplan.com"
LASTMOD = "2026-10-29"

PAGES = {
    "en": {
        "path": "/",
        "file": PUBLIC / "index.html",
        "title": "ETF Investment Calculator: Monthly Plan vs Bank | Your ETF Plan",
        "description": "Free ETF investment calculator: see how much to keep for emergencies, how much to invest each month and what you could have in 5 to 25 years compared with a bank account.",
        "og_locale": "en_GB",
        "og_image": "/og-en.png",
        "timezone": "Europe/London",
        "locale": "en-GB",
    },
    "it": {
        "path": "/it/",
        "file": PUBLIC / "it" / "index.html",
        "title": "Simulatore PAC in ETF: quanto investire ogni mese | Your ETF Plan",
        "description": "Simulatore gratuito di PAC in ETF: scopri quanto tenere per le emergenze, quanto investire ogni mese e quanto potresti avere tra 5 e 25 anni rispetto al conto in banca.",
        "og_locale": "it_IT",
        "og_image": "/og-it.png",
        "timezone": "Europe/Rome",
        "locale": "it-IT",
    },
}


def head_for(lang: str) -> str:
    p = PAGES[lang]
    url = SITE + p["path"]
    e = html.escape
    alt = "".join(
        f'<link rel="alternate" hreflang="{l}" href="{SITE}{PAGES[l]["path"]}">\n'
        for l in PAGES
    )
    alt += f'<link rel="alternate" hreflang="x-default" href="{SITE}/">\n'
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="page-lang" content="{lang}">
<title>{e(p['title'])}</title>
<meta name="description" content="{e(p['description'])}">
<link rel="canonical" href="{url}">
{alt}<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/logo.png">
<meta name="theme-color" content="#1f6b52">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Your ETF Plan">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{e(p['title'])}">
<meta property="og:description" content="{e(p['description'])}">
<meta property="og:image" content="{SITE}{p['og_image']}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{p['og_locale']}">
<meta name="twitter:card" content="summary_large_image">
<style>body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
"""


def json_ld(lang: str, faqs: list) -> str:
    p = PAGES[lang]
    data = [
        {
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": "Your ETF Plan",
            "url": SITE + p["path"],
            "description": p["description"],
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Any",
            "inLanguage": lang,
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
            "author": {"@type": "Person", "name": "Marco"},
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "inLanguage": lang,
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a},
                }
                for q, a in faqs
            ],
        },
    ]
    body = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{body}\n</script>\n'


def wrap(lang: str, fragment: str) -> str:
    # Drop the fragment's own <title>; the per-language head carries the SEO title.
    fragment = re.sub(r"<title>.*?</title>\s*", "", fragment, count=1, flags=re.S)
    style_end = fragment.index("</style>") + len("</style>")
    head_part, body_part = fragment[:style_end], fragment[style_end:]
    return (
        f'<!doctype html>\n<html lang="{lang}">\n<head>\n{head_for(lang)}{head_part}\n'
        f"</head>\n<body>{body_part}\n</body>\n</html>\n"
    )


FOOTER = '<p class="foot" style="text-align:center">© 2026 youretfplan.com</p>'
FOOTER_SITE = (
    '<p class="foot" style="text-align:center">© 2026 youretfplan.com · '
    '<a href="/" hreflang="en" lang="en">English</a> · '
    '<a href="/it/" hreflang="it" lang="it">Italiano</a></p>'
)


async def main() -> None:
    fragment = SRC.read_text(encoding="utf-8")
    assert FOOTER in fragment, "footer line not found in src/page.html"
    fragment = fragment.replace(FOOTER, FOOTER_SITE)
    tmp = ROOT / ".build"
    tmp.mkdir(exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        for lang, p in PAGES.items():
            raw = tmp / f"{lang}.html"
            raw.write_text(wrap(lang, fragment), encoding="utf-8")
            ctx = await browser.new_context(
                viewport={"width": 820, "height": 1000},
                timezone_id=p["timezone"],
                locale=p["locale"],
            )
            page = await ctx.new_page()
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            await page.goto(raw.as_uri())
            await page.wait_for_timeout(300)
            if errors:
                raise SystemExit(f"[{lang}] script error: {errors}")
            faqs = await page.eval_on_selector_all(
                "details:not(#glossary)",
                "els => els.map(d => [d.querySelector('summary').innerText.trim(), d.querySelector('div').innerText.trim()])",
            )
            out = "<!doctype html>\n" + await page.evaluate("document.documentElement.outerHTML")
            out = out.replace("</head>", json_ld(lang, faqs) + "</head>", 1)
            p["file"].parent.mkdir(parents=True, exist_ok=True)
            p["file"].write_text(out + "\n", encoding="utf-8")
            await ctx.close()
            print(f"built {p['file'].relative_to(ROOT)} ({len(out)//1024} KB, {len(faqs)} FAQs)")
        await browser.close()

    urls = []
    for lang, p in PAGES.items():
        alts = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{PAGES[l]["path"]}"/>'
            for l in PAGES
        )
        alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}/"/>'
        urls.append(
            f"  <url>\n    <loc>{SITE}{p['path']}</loc>\n    <lastmod>{LASTMOD}</lastmod>{alts}\n  </url>"
        )
    (PUBLIC / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n",
        encoding="utf-8",
    )
    (PUBLIC / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8"
    )
    print("built public/sitemap.xml, public/robots.txt")


if __name__ == "__main__":
    asyncio.run(main())
