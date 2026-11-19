#!/usr/bin/env python3
"""Builds the SEO topic pages from index.html.
Run from the repo root:  python3 tools/build_seo.py
Re-run after editing the gimboree tab, so the page stays in sync."""
import re, json, html

ROOT = '.'
SITE = 'https://tzarichkfar.com'
idx = open(f'{ROOT}/index.html', encoding='utf-8').read()
about = open(f'{ROOT}/about.html', encoding='utf-8').read()

# shared pieces from about.html
style = about[about.index('<style>'):about.index('</style>') + 8]
theme = about[about.index("<script>try{var t=localStorage"):]
theme = theme[:theme.index('</script>') + 9]
bnav = about[about.index('<nav class="bnav"'):about.index('</nav>') + 6]

CARD_CSS = ('.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin-block:16px}'
            '.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;font-size:.92rem;min-width:0;overflow-wrap:anywhere}'
            ':root[data-theme="dark"] .card{background:#261f2a}'
            '.card h3{font-family:var(--f-display);font-size:1.2rem;color:var(--ink);margin:0;font-weight:700}'
            '.c-kind{display:inline-block;background:var(--accent);color:var(--accent-fg);border-radius:999px;padding:1px 10px;font-size:.78rem;margin:4px 0 8px}'
            '.c-row{margin-bottom:6px}.card a{color:var(--link);font-weight:600}'
            '.card table{border-collapse:collapse;width:100%}.card td{padding:2px 4px;border-bottom:1px dotted var(--line);font-size:.88rem}'
            '.tel{white-space:nowrap;text-decoration:none}.where{font-size:.75rem;color:var(--muted)}'
            '.toc{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}.toc a{background:var(--accent);color:var(--accent-fg);border-radius:999px;padding:4px 12px;text-decoration:none;font-size:.9rem;font-weight:600}')
style = style.replace('</style>', CARD_CSS + '</style>')


def cards_from(view_id, next_id):
    seg = idx[idx.index(f'id="{view_id}"'):idx.index(f'id="{next_id}"')]
    return re.findall(r'<article class="card">.*?</article>', seg, re.S)


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', s))).strip()


def parse(card):
    name = text(re.search(r'<div class="c-name">(.*?)</div>', card).group(1))
    city = text(re.search(r'<span class="where">(.*?)</span>', card).group(1))
    m = re.search(r'<b>כתובת:</b>(.*?)</div>', card)
    addr = text(m.group(1)) if m else city
    m = re.search(r'<b>כניסה:</b>(.*?)</div>', card)
    entry = text(m.group(1)) if m else ''
    hrs = [(text(a), text(b)) for a, b in re.findall(r'<tr><td>(.*?)</td><td[^>]*>(.*?)</td></tr>', card)]
    return dict(name=name, city=city, addr=addr, entry=entry, hrs=hrs)


def page(slug, title, desc, h1, intro_html, body_html, faq, items, extra_ld=None):
    url = f'{SITE}/{slug}'
    ld = [
        {"@context": "https://schema.org", "@type": "CollectionPage", "url": url, "name": h1, "inLanguage": "he",
         "description": desc, "isPartOf": {"@id": f"{SITE}/#site"}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "צריך כפר שלם", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": h1, "item": url}]},
        {"@context": "https://schema.org", "@type": "ItemList", "name": h1, "numberOfItems": len(items),
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": it} for i, it in enumerate(items)]},
        {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": "he", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
    ] + (extra_ld or [])
    lds = ''.join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False) + '</script>' for x in ld)
    faq_html = ''.join(f'<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>' for q, a in faq)
    return f'''<!doctype html>
<html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:locale" content="he_IL"><meta property="og:title" content="{html.escape(h1)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/og-image.png">
<link rel="icon" type="image/png" sizes="32x32" href="/icon-32.png"><link rel="apple-touch-icon" href="/icon-180.png">
<link rel="preload" href="/fonts/assistant-var.woff" as="font" type="font/woff" crossorigin><link rel="preload" href="/fonts/playpen-hebrew-var.woff" as="font" type="font/woff" crossorigin>
{lds}
{style}
{theme}
</head><body><main>
<div class="top"><img src="/icon-192.png" alt=""><a class="home" href="/">צריך כפר שלם</a></div>
<h1>{h1}</h1>
{intro_html}
{body_html}
<h2>שאלות ותשובות</h2>
{faq_html}
<p style="margin-top:24px">המידע נאסף ממקורות ציבוריים וממארגני הפעילויות, ועשוי להשתנות. לפני שמגיעים כדאי לוודא שעות ומחירים מול המקום. משהו לא מדויק? <a href="/#join">כתבי לנו</a>.</p>
<a class="cta" href="/">ללוח הפעילויות היומי</a>
<footer><a href="/">לעמוד הראשי</a> · <a href="/about">אודות</a> · <a href="/#legal">כללי הקהילה, מדיניות פרטיות ותנאי שימוש</a></footer>
</main>
{bnav}
</body></html>
'''


# ---------- gimboree page ----------
gyms = [parse(c) for c in cards_from('v-play', 'v-cafes')]


def card_html(g):
    rows = ''.join(f'<tr><td>{html.escape(d)}</td><td dir="ltr" style="text-align:right">{html.escape(h)}</td></tr>' for d, h in g['hrs'])
    raw = next(c for c in cards_from('v-play', 'v-cafes') if g['name'] in text(c))
    extras = ''.join(m for m in re.findall(r'<div class="c-row">(?:(?!<b>כתובת:|<b>כניסה:|<b>שעות פעילות:).)*?</div>', raw, re.S))
    return (f'<article class="card"><h3>{html.escape(g["name"])}</h3><div class="c-kind">ג׳ימבורי</div> <span class="where">{html.escape(g["city"])}</span>'
            f'<div class="c-row"><b>כתובת:</b> {html.escape(g["addr"])}</div>'
            + (f'<div class="c-row"><b>כניסה:</b> {html.escape(g["entry"])}</div>' if g['entry'] else '')
            + f'<div class="c-row"><b>שעות פעילות:</b></div><table>{rows}</table>{extras}</article>')


free_nah = [g['name'].replace("ג'ימבורי ", '') for g in gyms if g['city'] == 'נהריה' and g['entry'] == 'חינם']
morning = [g for g in gyms if any(re.match(r'\s*(8|9|10|11):', h) for _, h in g['hrs'])]
by_city = {}
for g in gyms:
    by_city.setdefault(g['city'], []).append(g)
order = ['נהריה', 'עכו', 'שלומי'] + [c for c in by_city if c not in ('נהריה', 'עכו', 'שלומי')]
cities = [c for c in order if c in by_city]

body = '<nav class="toc" aria-label="לפי עיר">' + ''.join(f'<a href="#city-{i}">{c} ({len(by_city[c])})</a>' for i, c in enumerate(cities)) + '</nav>'
for i, c in enumerate(cities):
    body += f'<h2 id="city-{i}">ג׳ימבורי ב{c}</h2><div class="cards">' + ''.join(card_html(g) for g in by_city[c]) + '</div>'

def hrs_txt(g):
    return '; '.join(f'{d} {h}' for d, h in g['hrs'])

faq = [
    ("איפה יש ג׳ימבורי בנהריה?", f"בנהריה יש {len(by_city.get('נהריה', []))} ג׳ימבוריים: " + ', '.join(g['name'].replace("ג'ימבורי ", '') for g in by_city.get('נהריה', [])) + ". בעמוד הזה יש כתובת, שעות ומחיר לכל אחד מהם."),
    ("איפה יש ג׳ימבורי בחינם בנהריה?", "בכל הג׳ימבוריים של המתנ״סים בנהריה הכניסה חופשית: " + ', '.join(free_nah) + "."),
    ("איפה יש ג׳ימבורי בבוקר?", ' '.join(f"{g['name'].replace(chr(39),'׳')}: " + '; '.join(f"{d} {h.split(' · ')[0]}" for d, h in g['hrs'] if re.match(r'\s*(8|9|10|11):', h)) + '.' for g in morning) + " שאר הג׳ימבוריים פתוחים אחר הצהריים."),
    ("איפה יש ג׳ימבורי בעכו ובשלומי?", ' '.join(f"ב{c}: " + ', '.join(f"{g['name'].replace(chr(39),'׳')} ({g['addr']})" for g in by_city[c]) + '.' for c in cities if c != 'נהריה')),
    ("מאיזה גיל אפשר להגיע לג׳ימבורי?", "הג׳ימבוריים מתאימים לתינוקות ולפעוטות עד גיל 6. במקומות שיש בהם שעות לגילאים מסוימים, טווח הגילים מופיע ליד השעות."),
    ("האם צריך להירשם מראש?", "בדרך כלל לא. מגיעים בשעות הפתיחה. כדאי לוודא שעות מול המקום, כי לפעמים יש שינויים בחגים או אירועים."),
]

items = []
for g in gyms:
    items.append({"@type": "Place", "name": g['name'].replace("'", '׳'),
                  "address": {"@type": "PostalAddress", "streetAddress": g['addr'], "addressLocality": g['city'], "addressCountry": "IL"},
                  "description": f"ג׳ימבורי לתינוקות ופעוטות. כניסה: {g['entry'] or 'לבירור'}. שעות: {hrs_txt(g)}"})

intro = (f'<p>כל הג׳ימבוריים ומרחבי המשחק המקורים לתינוקות ולפעוטות בנהריה, בעכו ובשלומי, במקום אחד, עם כתובות, שעות פתיחה ומחירים. '
         f'בג׳ימבוריים של המתנ״סים בנהריה הכניסה חופשית.</p>'
         f'<p>מחפשת פעילות מסודרת עם מנחה? <a href="/">בלוח הפעילויות</a> יש מפגשים לאמהות ותינוקות כל יום.</p>')

out = page('gimboree-nahariya',
           'ג׳ימבורי בנהריה, עכו ושלומי – שעות, כתובות ומחירים | צריך כפר שלם',
           'כל הג׳ימבוריים לתינוקות ופעוטות בנהריה, עכו ושלומי: שעות פתיחה, כתובות ומחירים. ג׳ימבורי בחינם במתנ״סים, ג׳ימבורי בבוקר ואחר הצהריים.',
           'ג׳ימבורי בנהריה והגליל המערבי', intro, body, faq, items)
open(f'{ROOT}/gimboree-nahariya.html', 'w', encoding='utf-8').write(out)
print('gimboree-nahariya.html', len(gyms), 'places')
