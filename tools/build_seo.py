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
<p style="margin-top:20px"><b>עוד באתר:</b> <a href="/gimboree-nahariya">ג׳ימבורי</a> · <a href="/cafes-nahariya">בתי קפה עם מדשאה</a> · <a href="/baby-activities-nahariya">פעילויות לתינוקות לפי ימים</a> · <a href="/hanukkah-nahariya">חנוכה 2026</a></p>
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


# ---------- cafes page ----------
def raw_card(c):
    c = re.sub(r'<div class="c-name">(.*?)</div>', r'<h3>\1</h3>', c, count=1)
    return c.replace('class="hrs"', '')

cafes_raw = cards_from('v-cafes', 'v-news')
cafes = []
for c in cafes_raw:
    p = parse(c)
    kind = text(re.search(r'<div class="c-kind">(.*?)</div>', c).group(1))
    m = re.search(r'<b>לילדים:</b>(.*?)</div>', c)
    kids = text(m.group(1)) if m else ''
    cafes.append(dict(p, kind=kind, kids=kids, raw=raw_card(c)))
groups = [('נהריה', [c for c in cafes if c['city'] == 'נהריה']),
          ('הגליל המערבי', [c for c in cafes if c['city'] != 'נהריה'])]
body = '<nav class="toc" aria-label="לפי אזור">' + ''.join(f'<a href="#area-{i}">{n} ({len(l)})</a>' for i, (n, l) in enumerate(groups)) + '</nav>'
for i, (n, l) in enumerate(groups):
    title = 'בתי קפה עם מדשאה בנהריה' if n == 'נהריה' else 'בתי קפה עם מדשאה בגליל המערבי'
    body += f'<h2 id="area-{i}">{title}</h2><div class="cards">' + ''.join(c['raw'] for c in l) + '</div>'

def fri(c):
    for d, h in c['hrs']:
        if 'ו׳' in d and 'סגור' not in h:
            return h
    return None

fri_open = [f"{c['name']} ({c['city']}, {fri(c)})" for c in cafes if fri(c)]
cfaq = [
    ("איפה יש בית קפה עם מדשאה בנהריה?", "בנהריה: " + ', '.join(f"{c['name']} ({c['addr']})" for c in groups[0][1]) + ". בכולם יש מדשאה או מקום נוח לשבת עם תינוקות ופעוטות."),
    ("אילו בתי קפה בגליל המערבי מתאימים לילדים?", ', '.join(f"{c['name']} ב{c['city']}" for c in groups[1][1]) + ". לכל מקום מצוין בעמוד למה הוא מתאים לילדים."),
    ("איזה בית קפה עם מדשאה פתוח ביום שישי?", "ביום שישי פתוחים: " + ', '.join(fri_open) + ". כדאי לוודא שעות לפני שמגיעים."),
    ("מה הופך בית קפה למתאים לתינוקות?", "בעמוד הזה מופיעים רק מקומות עם מדשאה, צל או פינה נוחה לפרוש שמיכה, שבהם נעים לשבת עם תינוק או פעוט. לא מסעדות ערב ולא מקומות צפופים בלבד."),
]
citems = [{"@type": "CafeOrCoffeeShop" if 'קפה' in c['kind'] or 'מאפייה' in c['kind'] else "FoodEstablishment",
           "name": c['name'], "address": {"@type": "PostalAddress", "streetAddress": c['addr'], "addressLocality": c['city'], "addressCountry": "IL"},
           "description": (c['kind'] + '. ' + c['kids'])[:300]} for c in cafes]
cintro = ('<p>בתי קפה, מאפיות ועגלות קפה בנהריה ובגליל המערבי שבהם יש מדשאה, צל או מקום נוח לשבת עם תינוקות ופעוטות. '
          'לכל מקום מצוינים כתובת, שעות פתיחה, טלפון ולמה הוא מתאים לילדים.</p>'
          '<p>גם <a href="/gimboree-nahariya">ג׳ימבורי בנהריה</a> ו<a href="/baby-activities-nahariya">פעילויות לתינוקות</a> מרוכזים אצלנו.</p>')
open(f'{ROOT}/cafes-nahariya.html', 'w', encoding='utf-8').write(page(
    'cafes-nahariya',
    'בתי קפה עם מדשאה לתינוקות ופעוטות בנהריה והגליל המערבי | צריך כפר שלם',
    'בתי קפה ומאפיות עם מדשאה בנהריה ובגליל המערבי שמתאימים לתינוקות ופעוטות: כתובות, שעות פתיחה, טלפונים ומה יש שם לילדים.',
    'בתי קפה עם מדשאה לתינוקות ופעוטות', cintro, body, cfaq, citems))
print('cafes-nahariya.html', len(cafes), 'places')


# ---------- baby activities page ----------
DAYS = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת']
import datetime
acts = []
for m in re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})"', idx):
    d = m.group(1)
    end = idx.find('</section>', m.end())
    for attrs, inner in re.findall(r'<article class="act"([^>]*)>(.*?)</article>', idx[m.end():end], re.S):
        if 'data-off' in attrs:
            continue
        amin = int((re.search(r'data-amin="(\d+)"', attrs) or [0, 0])[1] or 0)
        name = text(re.search(r'<span class="name">(.*?)</span>', inner).group(1))
        t = re.search(r'<span dir="ltr">(.*?)</span>', inner)
        def grab(pat):
            m2 = re.search(pat, inner, re.S)
            return text(m2.group(1)) if m2 else ''
        age = grab(r'גילאים: (.*?)(?:<br|$)')
        place = grab(r'מיקום: (.*?)(?: · מחיר|<br)')
        price = grab(r'מחיר: (.*?)(?:<br|$)').split(' · ')[0][:60]
        acts.append(dict(date=d, wd=(datetime.date.fromisoformat(d).weekday() + 1) % 7, amin=amin, name=name,
                         time=text(t.group(1)) if t else '', age=age, place=place, price=price))
today = datetime.date.today().isoformat()
window = [a for a in acts if a['date'] >= today]
count = {}
for a in window:
    count[(a['wd'], a['name'])] = count.get((a['wd'], a['name']), 0) + 1
weekly = {}
for a in window:
    if count[(a['wd'], a['name'])] >= 2 and a['amin'] <= 12:
        weekly.setdefault(a['wd'], {}).setdefault(a['name'], a)

def tkey(a):
    m = re.match(r'(\d{1,2}):(\d{2})', a['time'])
    return int(m.group(1)) * 60 + int(m.group(2)) if m else 9999

body = '<nav class="toc" aria-label="לפי יום">' + ''.join(f'<a href="#day-{w}">{DAYS[w]}</a>' for w in sorted(weekly)) + '</nav>'
aitems = []
for w in sorted(weekly):
    body += f'<h2 id="day-{w}">פעילויות לתינוקות ביום {DAYS[w]}</h2><div class="cards">'
    for a in sorted(weekly[w].values(), key=tkey):
        rows = ''.join(f'<div class="c-row"><b>{k}:</b> ' + (f'<span dir="ltr">{html.escape(v)}</span>' if k == 'שעה' else html.escape(v)) + '</div>' for k, v in
                       [('שעה', a['time']), ('גילאים', a['age']), ('מקום', a['place']), ('מחיר', a['price'])] if v)
        body += f'<article class="card"><h3>{html.escape(a["name"])}</h3><div class="c-kind">ימי {DAYS[w]}</div>{rows}</article>'
        aitems.append({"@type": "Thing", "name": a['name'], "description": f"ימי {DAYS[w]} {a['time']}, {a['place']}. {a['age']}".strip()})
    body += '</div>'
free = sorted({re.split(r' – | \(', a['name'])[0] for w in weekly for a in weekly[w].values() if re.search(r'ללא עלות|חינם|כניסה חופשית', a['price'])})
nurse = sorted({re.split(r' – | \(', a['name'])[0] for w in weekly for a in weekly[w].values() if 'הנקה' in a['name']})
afaq = [
    ("אילו פעילויות יש לתינוקות בנהריה?", "כל שבוע יש בנהריה ובגליל המערבי מפגשים קבועים לאמהות ותינוקות: גן עם אמא, מפגשי תנועה ומוזיקה, יוגה ועיסוי תינוקות, מפגשי הנקה ומפגשי שיח לאמהות. בעמוד הזה הם מסודרים לפי ימי השבוע, ובלוח הפעילויות באתר יש גם פעילויות חד־פעמיות."),
    ("יש פעילויות חינמיות לאמהות בחופשת לידה?", ("כן, למשל: " + ', '.join(free) + ".") if free else "כן, בלוח הפעילויות אפשר לסנן לפי עלות ולראות רק פעילויות ללא עלות."),
    ("איפה יש מפגשי הנקה בנהריה?", ("מפגשי הנקה קבועים: " + ', '.join(nurse) + ".") if nurse else "בלוח הפעילויות באתר מופיעים מפגשי הנקה כשהם מתקיימים."),
    ("מאיזה גיל אפשר להגיע?", "בעמוד הזה מופיעות פעילויות שמתאימות כבר לתינוקות בשנה הראשונה. ליד כל פעילות מצוין טווח הגילים."),
]
aintro = ('<p>המפגשים הקבועים לאמהות ותינוקות בנהריה ובגליל המערבי, מסודרים לפי ימי השבוע: גן עם אמא, מוזיקה ותנועה, יוגה ועיסוי תינוקות, מפגשי הנקה ומפגשי שיח לאמהות בחופשת לידה.</p>'
          '<p>חלק מהמפגשים הם סדרות עם מספר מפגשים מוגבל, והתאריכים המדויקים מופיעים בלוח.</p><p>הלוח המלא, כולל פעילויות חד־פעמיות וסינון לפי גיל, שעה ומחיר, נמצא <a href="/">בעמוד הראשי</a>. יש גם <a href="/gimboree-nahariya">ג׳ימבורי</a> ו<a href="/cafes-nahariya">בתי קפה עם מדשאה</a>.</p>')
open(f'{ROOT}/baby-activities-nahariya.html', 'w', encoding='utf-8').write(page(
    'baby-activities-nahariya',
    'פעילויות לתינוקות ואמהות בנהריה והגליל המערבי – לפי ימים | צריך כפר שלם',
    'מפגשים קבועים לאמהות ותינוקות בנהריה ובגליל המערבי לפי ימי השבוע: גן עם אמא, יוגה ועיסוי תינוקות, מוזיקה ותנועה ומפגשי הנקה, עם שעות, מקומות ומחירים.',
    'פעילויות לתינוקות ואמהות בנהריה והגליל המערבי', aintro, body, afaq, aitems))
print('baby-activities-nahariya.html', sum(len(v) for v in weekly.values()), 'weekly activities')


# ---------- hanukkah page ----------
HSTART, HEND = '2026-12-04', '2026-12-12'
shows = []
for m in re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})"', idx):
    d = m.group(1)
    if not (HSTART <= d <= HEND):
        continue
    end = idx.find('</section>', m.end())
    for attrs, inner in re.findall(r'<article class="act"([^>]*)>(.*?)</article>', idx[m.end():end], re.S):
        name = text(re.search(r'<span class="name">(.*?)</span>', inner).group(1))
        if not name.startswith('חנוכה'):
            continue
        def grab(pat):
            m2 = re.search(pat, inner, re.S)
            return text(m2.group(1)) if m2 else ''
        t = grab(r'<span dir="ltr">(.*?)</span>')
        first = re.search(r'שעה: <span dir="ltr">[^<]*</span> · (.*?)<br', inner, re.S)
        age = text(first.group(1)).replace('גילאים: ', '') if first else ''
        place = grab(r'מיקום: (.*?)(?: · מחיר|<br)')
        price = grab(r'מחיר: (.*?)(?:<br|$)').split(' · ')[0]
        link = re.search(r'הרשמה:.*?<a href="([^"]+)"', inner, re.S)
        shows.append(dict(date=d, name=name.replace('חנוכה: ', ''), time=t, age=age, place=place, price=price,
                          link=html.unescape(link.group(1)) if link else ''))
DAYNAME = ['שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת', 'ראשון']
def hdate(d):
    dt = datetime.date.fromisoformat(d)
    return f'יום {DAYNAME[dt.weekday()]}, {dt.day}.{dt.month}'
body = '<h2>הצגות ומופעי חנוכה לפעוטות וילדים</h2><div class="cards">'
eitems = []
for sh in shows:
    rows = ''.join(f'<div class="c-row"><b>{k}:</b> ' + (f'<span dir="ltr">{html.escape(v)}</span>' if k == 'שעה' else html.escape(v)) + '</div>'
                   for k, v in [('מתי', hdate(sh['date'])), ('שעה', sh['time']), ('גילאים', sh['age']), ('מקום', sh['place']), ('מחיר', sh['price'])] if v)
    lk = f'<div class="c-row"><a href="{html.escape(sh["link"])}" rel="noopener">לפרטים והרשמה</a></div>' if sh['link'] else ''
    body += f'<article class="card"><h3>{html.escape(sh["name"])}</h3><div class="c-kind">חנוכה</div>{rows}{lk}</article>'
    st = re.match(r'(\d{1,2}):(\d{2})', sh['time'])
    ev = {"@type": "Event", "name": sh['name'], "startDate": sh['date'] + (f"T{int(st.group(1)):02d}:{st.group(2)}:00+02:00" if st else ''),
          "eventStatus": "https://schema.org/EventScheduled", "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
          "location": {"@type": "Place", "name": sh['place'], "address": {"@type": "PostalAddress", "addressLocality": "נהריה", "addressCountry": "IL"}},
          "description": f"{sh['name']} – {sh['age']}. {sh['price']}".strip(), "isAccessibleForFree": False}
    pm = re.search(r'(\d+)\s*₪', sh['price'])
    if pm:
        ev["offers"] = {"@type": "Offer", "price": pm.group(1), "priceCurrency": "ILS", "url": sh['link'] or f'{SITE}/hanukkah-nahariya', "availability": "https://schema.org/InStock"}
    eitems.append(ev)
body += '</div>'
body += ('<h2>פעילויות לתינוקות בחנוכה</h2><p>רוב המפגשים הקבועים לאמהות ותינוקות ממשיכים בחנוכה כרגיל, כמו גן עם אמא, מפגשי תנועה ומוזיקה ומפגשי הנקה. '
         'כל המפגשים לפי ימים נמצאים ב<a href="/baby-activities-nahariya">עמוד הפעילויות לתינוקות</a>, וכדאי לוודא מול המארגנת שהמפגש מתקיים בחג.</p>'
         '<h2>עוד רעיונות לימי החג</h2><p><a href="/gimboree-nahariya">ג׳ימבורי בנהריה</a>, ברוב המתנ״סים בכניסה חופשית, ו<a href="/cafes-nahariya">בתי קפה עם מדשאה</a> לבוקר יפה בחוץ.</p>')
hfaq = [
    ("מתי חנוכה 2026?", "חנוכה תשפ״ז מתחיל ביום שישי, 4 בדצמבר 2026, עם הדלקת הנר הראשון, ונמשך עד מוצאי שבת, 12 בדצמבר 2026."),
    ("אילו הצגות חנוכה יש לפעוטות בנהריה?", ' '.join(f"{sh['name']} ({hdate(sh['date'])}, {sh['place']}, {sh['age']})." for sh in shows if sh['age'] and re.search(r'[2-3]', sh['age']))),
    ("כמה עולה הצגת חנוכה בנהריה?", "רוב מופעי החנוכה של העירייה עולים 20 ₪ לכרטיס, וכל משתתף צריך כרטיס. המחיר של כל מופע מצוין ליד הפרטים שלו."),
    ("יש פעילויות לתינוקות בחנוכה?", "כן. רוב המפגשים הקבועים לאמהות ותינוקות ממשיכים כרגיל בחנוכה. הרשימה המלאה לפי ימים נמצאת בעמוד הפעילויות לתינוקות באתר."),
]
hintro = ('<p>חנוכה תשפ״ז מתחיל ביום שישי, 4 בדצמבר 2026, ונמשך עד מוצאי שבת, 12 בדצמבר. כאן ריכזנו את הצגות ומופעי החנוכה לפעוטות ולילדים בנהריה, '
          'יחד עם רעיונות לבילוי עם תינוקות בימי החג.</p><p>כדאי להזמין כרטיסים מראש, כי למופעים רבים המקומות מוגבלים.</p>')
open(f'{ROOT}/hanukkah-nahariya.html', 'w', encoding='utf-8').write(page(
    'hanukkah-nahariya',
    'חנוכה 2026 בנהריה: הצגות ופעילויות לפעוטות ותינוקות | צריך כפר שלם',
    'הצגות ומופעי חנוכה 2026 לפעוטות וילדים בנהריה, עם תאריכים, שעות, גילאים ומחירים, ורעיונות לפעילויות עם תינוקות בימי החג.',
    'חנוכה 2026 בנהריה: הצגות ופעילויות לפעוטות ותינוקות', hintro, body, hfaq, eitems))
print('hanukkah-nahariya.html', len(shows), 'shows')
