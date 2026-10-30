#!/usr/bin/env python3
"""Build the static site from src/page.html and the scenario pages (src/bank.html, ...).

Writes one page per language for each group in GROUPS (main page at /, /it/, /es/;
scenarios at their localized paths). Each page gets its
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
LASTMOD = "2026-10-30"

MAIN = {
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
    "es": {
        "path": "/es/",
        "file": PUBLIC / "es" / "index.html",
        "title": "Calculadora de inversión en ETF: cuánto invertir cada mes | Your ETF Plan",
        "description": "Calculadora gratuita para invertir en ETF: descubre cuánto guardar para emergencias, cuánto invertir cada mes y cuánto podrías tener en 5 a 25 años frente a dejarlo en el banco.",
        "og_locale": "es_ES",
        "og_image": "/og-es.png",
        "timezone": "Europe/Madrid",
        "locale": "es-ES",
    },
}

LOCALE = {
    "en": {"timezone": "Europe/London", "locale": "en-GB", "og_locale": "en_GB", "og_image": "/og-en.png"},
    "it": {"timezone": "Europe/Rome", "locale": "it-IT", "og_locale": "it_IT", "og_image": "/og-it.png"},
    "es": {"timezone": "Europe/Madrid", "locale": "es-ES", "og_locale": "es_ES", "og_image": "/og-es.png"},
}


def scenario(src: str, paths: dict, titles: dict, descriptions: dict) -> dict:
    """A scenario page in three languages, e.g. bank vs ETF."""
    return {
        lang: dict(
            LOCALE[lang],
            path=paths[lang],
            file=PUBLIC / paths[lang].strip("/") / "index.html",
            title=titles[lang],
            description=descriptions[lang],
        )
        for lang in ("en", "it", "es")
    } | {"_src": ROOT / "src" / src}


# Every indexed page group: one source file, one URL per language (linked with hreflang).
GROUPS = {
    "main": MAIN | {"_src": SRC},
    "bank": scenario(
        "bank.html",
        {"en": "/bank-vs-etf/", "it": "/it/banca-vs-etf/", "es": "/es/banco-vs-etf/"},
        {
            "en": "Money in the bank or investing in ETFs? Savings vs ETF calculator | Your ETF Plan",
            "it": "Soldi in banca o investire in ETF? Calcolatore conto deposito vs ETF | Your ETF Plan",
            "es": "¿Dinero en el banco o invertir en ETF? Calculadora depósito vs ETF | Your ETF Plan",
        },
        {
            "en": "Free calculator: see what your savings become in a current account, a savings deposit or investing in ETFs, in today's money after inflation. Risks, costs and when to keep cash.",
            "it": "Calcolatore gratuito: guarda cosa diventano i tuoi risparmi sul conto corrente, su un conto deposito o investendo in ETF, in euro di oggi. Rischi, costi, tasse e quando tenerli in banca.",
            "es": "Calculadora gratuita: mira en qué se convierten tus ahorros en la cuenta corriente, en un depósito o invirtiendo en ETF, en euros de hoy. Riesgos, costes, impuestos y cuándo dejarlos en el banco.",
        },
    ),
    "buy": scenario(
        "buy.html",
        {"en": "/buy-vs-rent-etf/", "it": "/it/comprare-casa-o-affitto-etf/", "es": "/es/comprar-o-alquilar-etf/"},
        {
            "en": "Buy a home or rent and invest in ETFs? Calculator | Your ETF Plan",
            "it": "Comprare casa o affittare e investire in ETF? Calcolatore | Your ETF Plan",
            "es": "¿Comprar casa o alquilar e invertir en ETF? Calculadora | Your ETF Plan",
        },
        {
            "en": "Free calculator: buying a home with a mortgage compared with renting and investing the difference in ETFs. Price-to-rent ratio, break-even year and what each one owns, in today's money.",
            "it": "Calcolatore gratuito: comprare casa con il mutuo contro stare in affitto e investire la differenza in ETF. Rapporto prezzo/affitto, anno di pareggio e patrimonio finale in euro di oggi.",
            "es": "Calculadora gratuita: comprar casa con hipoteca frente a alquilar e invertir la diferencia en ETF. Relación precio/alquiler, año de equilibrio y patrimonio final en euros de hoy.",
        },
    ),
    "inherit": scenario(
        "inherit.html",
        {"en": "/inheritance-etf/", "it": "/it/eredita-investire-etf/", "es": "/es/herencia-invertir-etf/"},
        {
            "en": "I received an inheritance: keep it, rent it or invest in ETFs? | Your ETF Plan",
            "it": "Ho ricevuto un'eredità: tenerla, affittarla o investire in ETF? | Your ETF Plan",
            "es": "He recibido una herencia: ¿guardarla, alquilarla o invertir en ETF? | Your ETF Plan",
        },
        {
            "en": "Free calculator for an inheritance: money left in the bank or invested in ETFs, or a house kept empty, rented out or sold and invested in ETFs. In today's money, with the steps to take first.",
            "it": "Calcolatore gratuito per un'eredità: soldi lasciati in banca o investiti in ETF, oppure una casa tenuta vuota, affittata o venduta per investire in ETF. In euro di oggi, con i passi da fare prima e le tasse di successione.",
            "es": "Calculadora gratuita para una herencia: dinero en el banco o invertido en ETF, o una casa vacía, alquilada o vendida para invertir en ETF. En euros de hoy, con los pasos previos y los impuestos.",
        },
    ),
}
PAGES = MAIN  # kept for older references


def langs(group: dict) -> list:
    return [k for k in group if not k.startswith("_")]


def head_for(group: dict, lang: str) -> str:
    p = group[lang]
    url = SITE + p["path"]
    e = html.escape
    alt = "".join(
        f'<link rel="alternate" hreflang="{l}" href="{SITE}{group[l]["path"]}">\n'
        for l in langs(group)
    )
    alt += f'<link rel="alternate" hreflang="x-default" href="{SITE}{group["en"]["path"]}">\n'
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


def json_ld(group: dict, lang: str, faqs: list) -> str:
    p = group[lang]
    data = [
        {
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": p["title"].split(" | ")[0] if group is not GROUPS["main"] else "Your ETF Plan",
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


def wrap(group: dict, lang: str, fragment: str) -> str:
    # Drop the fragment's own <title>; the per-language head carries the SEO title.
    fragment = re.sub(r"<title>.*?</title>\s*", "", fragment, count=1, flags=re.S)
    style_end = fragment.index("</style>") + len("</style>")
    head_part, body_part = fragment[:style_end], fragment[style_end:]
    return (
        f'<!doctype html>\n<html lang="{lang}">\n<head>\n{head_for(group, lang)}{head_part}\n'
        f"</head>\n<body>{body_part}\n</body>\n</html>\n"
    )


FOOTER = '<p class="foot" style="text-align:center">© 2026 youretfplan.com</p>'
FOOTER_SITE = (
    '<p class="foot" style="text-align:center">© 2026 youretfplan.com · '
    '<a href="/" hreflang="en" lang="en">English</a> · '
    '<a href="/it/" hreflang="it" lang="it">Italiano</a> · '
    '<a href="/es/" hreflang="es" lang="es">Español</a></p>'
)


async def main() -> None:
    tmp = ROOT / ".build"
    tmp.mkdir(exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        for gname, group in GROUPS.items():
            fragment = group["_src"].read_text(encoding="utf-8")
            if gname == "main":
                assert FOOTER in fragment, "footer line not found in src/page.html"
                fragment = fragment.replace(FOOTER, FOOTER_SITE)
            for lang in langs(group):
                p = group[lang]
                raw = tmp / f"{gname}-{lang}.html"
                raw.write_text(wrap(group, lang, fragment), encoding="utf-8")
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
                    raise SystemExit(f"[{gname} {lang}] script error: {errors}")
                faqs = await page.eval_on_selector_all(
                    "details:not(#glossary):not(.assume)",
                    "els => els.map(d => [d.querySelector('summary').innerText.trim(), d.querySelector('div').innerText.trim()])",
                )
                out = "<!doctype html>\n" + await page.evaluate("document.documentElement.outerHTML")
                out = out.replace("</head>", json_ld(group, lang, faqs) + "</head>", 1)
                p["file"].parent.mkdir(parents=True, exist_ok=True)
                p["file"].write_text(out + "\n", encoding="utf-8")
                await ctx.close()
                print(f"built {p['file'].relative_to(ROOT)} ({len(out)//1024} KB, {len(faqs)} FAQs)")
        await browser.close()

    urls = []
    for group in GROUPS.values():
        for lang in langs(group):
            p = group[lang]
            alts = "".join(
                f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{group[l]["path"]}"/>'
                for l in langs(group)
            )
            alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{group["en"]["path"]}"/>'
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
        f"User-agent: *\nAllow: /\nDisallow: /v2/\nDisallow: /v3/\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8"
    )
    print("built public/sitemap.xml, public/robots.txt")

    # Previews of redesigns at /v2/ (hook first) and /v3/ (guided plan with illustrations):
    # not indexed, no tracking, language switches in place. Not in the sitemap.
    for name in ("v2", "v3"):
        src = (ROOT / "src" / f"{name}.html").read_text(encoding="utf-8")
        src = re.sub(r"<title>.*?</title>\s*", "", src, count=1, flags=re.S)
        head = (
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="robots" content="noindex">\n'
            "<title>Your ETF Plan (preview)</title>\n"
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
            "<style>body{margin:0}</style>\n"
        )
        end = src.index("</style>") + len("</style>")
        out = f'<!doctype html>\n<html lang="en">\n<head>\n{head}{src[:end]}\n</head>\n<body>{src[end:]}\n</body>\n</html>\n'
        (PUBLIC / name).mkdir(exist_ok=True)
        (PUBLIC / name / "index.html").write_text(out, encoding="utf-8")
        print(f"built public/{name}/index.html (preview, noindex)")

if __name__ == "__main__":
    asyncio.run(main())
