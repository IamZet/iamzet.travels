import json, re, html, os, shutil
from urllib.parse import urlparse, parse_qs

S = os.path.dirname(os.path.abspath(__file__))          # src/: generator, templates, data
ROOT = os.path.dirname(S)                               # repo root = published site
OUT = os.environ.get('SITE_OUT', ROOT)
T = json.load(open(os.path.join(S, 'trips.json'), encoding='utf-8'))
N = json.load(open(os.path.join(S, 'notes.json'), encoding='utf-8'))
e = lambda s: html.escape(s or '', quote=True)

MONTHS = ['январь','февраль','март','апрель','май','июнь','июль','август','сентябрь','октябрь','ноябрь','декабрь']
def season(m):
    if m < 0: return 'winter'
    return 'winter' if m in (11,0,1) else 'spring' if m < 5 else 'summer' if m < 8 else 'autumn'
def plural(n, a, b, c):
    m10, m100 = n % 10, n % 100
    return a if m10 == 1 and m100 != 11 else b if 2 <= m10 <= 4 and not 10 <= m100 < 20 else c

TR = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюя', ['a','b','v','g','d','e','e','zh','z','i','y','k','l','m','n','o','p','r','s','t','u','f','h','ts','ch','sh','sch','','y','','e','yu','ya']))
def slugify(s):
    s = ''.join(TR.get(c, c) for c in s.lower())
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

def yt_id(u):
    m = re.match(r'https://youtu\.be/([\w-]{11})', u)
    return m.group(1) if m else None
def playlist_id(u):
    return parse_qs(urlparse(u).query).get('list', [None])[0] if 'playlist' in u else None
def map_mid(u):
    if not u: return None
    if 'maps/d/' in u:
        return parse_qs(urlparse(u).query).get('mid', [None])[0]
    m = re.search(r'!1s([\w-]{20,})', u) or re.search(r'[?&]id=([\w-]{20,})', u)
    return m.group(1) if m else None

# ---------- enrich ----------
used = set()
for i, t in enumerate(T):
    t['mi'] = MONTHS.index(t['w'].split('-')[0].strip().lower())
    t['s'] = season(t['mi'])
    key = t['t'].rsplit('/', 1)[1][:20] if t['t'] else None
    t['note'] = N.get(key) if key else None
    t['vids'] = [yt_id(u) for u in t['v']]
    t['thumb'] = next((v for v in t['vids'] if v), None)
    t['words'] = t['note']['w'] if t['note'] else 0
    t['page'] = True
    t['gal'] = None
    if t['p']:
        import hashlib
        tok = t['p'].split('#')[1]; t['akey'] = hashlib.sha1(tok.encode()).hexdigest()[:10]
        ip = os.path.join(S, 'photo_index', t['akey'] + '.json')
        if os.path.exists(ip):
            g = json.load(open(ip, encoding='utf-8'))
            if g['photos']:
                for ph in g['photos']: ph['k'] = t['akey']
                t['gal'] = g['photos']
    base = f"{t['y']}-{slugify(t['n'])}"
    slug, k = base, 2
    while slug in used: slug, k = f'{base}-{k}', k + 1
    used.add(slug); t['slug'] = slug
    t['maps'] = [(None, t['m'])] if t['m'] else []
    t['plist'] = [t['p']] if t['p'] else []
EX = json.load(open(os.path.join(S, 'excludes.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'excludes.json')) else []
T[:] = [t for t in T if t['slug'] not in EX]
MG = json.load(open(os.path.join(S, 'merges.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'merges.json')) else {}
for slug, mg in MG.items():
    parts = [next(t for t in T if t['slug'] == x) for x in mg['from']]
    pos = min(T.index(p) for p in parts)
    nt = dict(parts[0]); nt.update(n=mg['n'], y=mg['y'], w=mg['w'], slug=slug, e=None)
    nt['note'] = next((p['note'] for p in parts if p['note']), None)
    nt['t'] = next((p['t'] for p in parts if p['t']), None)
    nt['words'] = nt['note']['w'] if nt['note'] else 0
    nt['v'] = [u for p in parts for u in p['v']]; nt['vids'] = [v for p in parts for v in p['vids']]
    nt['thumb'] = next((v for v in nt['vids'] if v), None)
    labels = mg.get('maplabels', [p['n'] for p in parts])
    nt['maps'] = [(labels[i], p['m']) for i, p in enumerate(parts) if p['m']]
    nt['m'] = nt['maps'][0][1] if nt['maps'] else None
    nt['plist'] = [p['p'] for p in parts if p['p']]; nt['p'] = nt['plist'][0] if nt['plist'] else None
    gal = [ph for p in parts for ph in (p['gal'] or [])]
    nt['gal'] = gal or None; nt['akey'] = gal[0]['k'] if gal else None
    nt['mi'] = MONTHS.index(mg['w'].split('-')[0].strip().lower()); nt['s'] = season(nt['mi'])
    for p in parts: T.remove(p)
    T.insert(pos, nt)
T.sort(key=lambda t: -t['y'])
VO = json.load(open(os.path.join(S, 'videos.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'videos.json')) else {}
for t in T:
    o = VO.get(t['slug'])
    t['vtitles'] = None; t['vplaylist'] = None
    if o:
        t['v'] = ['https://youtu.be/' + v[0] for v in o['videos']]
        t['vids'] = [v[0] for v in o['videos']]
        t['vtitles'] = o['videos']; t['vplaylist'] = o.get('playlist')
        t['thumb'] = t['thumb'] or t['vids'][0]
DO = json.load(open(os.path.join(S, 'dates.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'dates.json')) else {}
for t in T:
    o = DO.get(t['slug'], {})
    t['wshort'] = o.get('short', t['w']); t['wfull'] = o.get('full', f"{t['w']} {t['y']}"); t['ylab'] = o.get('years', str(t['y']))
CN = json.load(open(os.path.join(S, 'countries.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'countries.json')) else {}
CNAME = {'ab':'Абхазия','al':'Албания','am':'Армения','at':'Австрия','az':'Азербайджан','ba':'Босния и Герцеговина','be':'Бельгия','bg':'Болгария','by':'Беларусь','cd':'ДР Конго','cz':'Чехия','de':'Германия','ge':'Грузия','gr':'Греция','hr':'Хорватия','il':'Израиль','ir':'Иран','it':'Италия','ke':'Кения','kg':'Кыргызстан','kz':'Казахстан','lt':'Литва','lv':'Латвия','md':'Молдова','me':'Черногория','mn':'Монголия','nl':'Нидерланды','pl':'Польша','ps':'Палестина','ro':'Румыния','ru':'Россия','rw':'Руанда','si':'Словения','tr':'Турция','tz':'Танзания','ua':'Украина','us':'США','uz':'Узбекистан'}
def flag_html(t, root):
    cs = CN.get(t['slug'], [])
    if not cs: return ''
    return '<span class="flags">' + ''.join(f'<img src="{root}assets/flags/{c}.svg" alt="{CNAME.get(c, c.upper())}" title="{CNAME.get(c, c.upper())}" width="20" height="15">' for c in cs) + '</span>'
LV = json.load(open(os.path.join(S, 'localvideos.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'localvideos.json')) else {}
CV = json.load(open(os.path.join(S, 'cloudvideos.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'cloudvideos.json')) else {}
COV = json.load(open(os.path.join(S, 'covers_list.json'))) if os.path.exists(os.path.join(S, 'covers_list.json')) else {}
DZ = json.load(open(os.path.join(S, 'dzen.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'dzen.json')) else {}
DZX = json.load(open(os.path.join(S, 'dzen_extra.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'dzen_extra.json')) else {}
DZY = json.load(open(os.path.join(S, 'dzen_byyt.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'dzen_byyt.json')) else {}
paged = [t for t in T if t['page']]

ICO = {
 'map': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M1.5 3.5l4-1.5 5 2 4-1.5v10l-4 1.5-5-2-4 1.5z"/><path d="M5.5 2v10M10.5 4v10"/></svg>',
 'text': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M3.5 1.5h6l3 3v10h-9z"/><path d="M5.5 7.5h5M5.5 10h5M5.5 12.5h3"/></svg>',
 'play': '<svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M4.5 2.8v10.4L13 8z"/></svg>',
 'photo': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="1.5" y="3.5" width="13" height="10" rx="1.5"/><circle cx="8" cy="8.5" r="2.5"/><path d="M5.5 3.5l1-2h3l1 2"/></svg>',
 'out': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M6 3H3v10h10v-3M9 2h5v5M14 2L7 9"/></svg>',
}
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700;800&family=Golos+Text:wght@400;500;600&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&family=JetBrains+Mono:wght@400;500&display=swap">'

import hashlib as _h
VER = _h.md5(open(os.path.join(S,'style.css'),'rb').read()+open(os.path.join(S,'site.js'),'rb').read()).hexdigest()[:8]
def head(title, desc, root, extra=''):
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
{extra}
<meta name="theme-color" content="#EDF0EC" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#10181C" media="(prefers-color-scheme: dark)">
{FONTS}
<link rel="stylesheet" href="{root}assets/style.css?v={VER}">
</head>
'''

def ext(href, label, icon, cls='l'):
    return f'<a class="{cls}" href="{e(href)}" target="_blank" rel="noopener">{ICO[icon]}{label}</a>'

def read_min(w): return max(1, round(w / 180))

# ---------- index ----------
def row(t):
    meta = []
    name = e(t['n'])
    href = f"trips/{t['slug']}.html"
    if t['slug'] in COV:
        cw, ch = COV[t['slug']]
        img = f'<img src="covers/{t["slug"]}.webp" alt="" loading="lazy" width="{cw}" height="{ch}">'
    elif t['thumb']:
        img = f'<img src="https://i.ytimg.com/vi/{t["thumb"]}/mqdefault.jpg" alt="" loading="lazy" width="320" height="180"><span class="play">{ICO["play"]}</span>'
    elif t['gal']:
        p0 = t['gal'][0]
        img = f'<img src="photos/{p0["k"]}/t/{p0["n"]:03d}.webp" alt="" loading="lazy" width="{p0["tw"]}" height="{p0["th"]}">'
    else:
        img = f'<span class="ph s-{t["s"]}">{ICO["play"] if t["v"] else ICO["text"] if t["note"] else ICO["photo"]}</span>'
    thumb = f'<a class="thumb" href="{href}" tabindex="-1" aria-hidden="true">{img}</a>'
    title = f'<a class="tname" href="{href}">{name}</a>'
    chips = []
    if t['note']: chips.append(f'<a class="l l-main" href="{href}">{ICO["text"]}Заметки</a>')
    if t['gal']: chips.append(f'<a class="l" href="{href}#photo">{ICO["photo"]}Фото <small>{len(t["gal"])}</small></a>')
    elif t['p']: chips.append(ext(t['p'], 'Фото', 'photo'))
    if t['v']: chips.append(f'<a class="l" href="{href}#video">{ICO["play"]}Видео' + (f' <small>{len(t["v"]) + len(DZX.get(t["slug"], []))}</small>' if len(t['v']) + len(DZX.get(t['slug'], [])) > 1 else '') + '</a>')
    if t['m']: chips.append(f'<a class="l" href="{href}#map">{ICO["map"]}Карта</a>')
    flags = ' '.join(k for k, v in (('v', t['v']), ('t', t['note']), ('m', t['m']), ('p', t['p'])) if v)
    return f'''<li class="trip" id="t-{t['slug']}" data-f="{flags}" data-q="{e((t['n'] + ' ' + t['w'] + ' ' + str(t['y'])).lower())}">
  {thumb}
  <div class="tbody"><div class="when"><i class="s-{t['s']}"></i>{e(t['wshort'])}</div>{title}{flag_html(t, '')}{'<div class="meta">' + ' · '.join(meta) + '</div>' if meta else ''}</div>
  <div class="links">{''.join(chips)}</div>
</li>'''

years = sorted({t['y'] for t in T}, reverse=True)
minY, maxY = min(years), max(years)
hist, labels = [], []
for y in range(minY, maxY + 1):
    ts = [t for t in T if t['y'] == y][::-1]
    if ts:
        word = plural(len(ts), 'поездка', 'поездки', 'поездок')
        hist.append(f'<a class="hbar" href="#y{y}" title="{y}: {len(ts)} {word}" aria-label="{y}: {len(ts)} {word}">' + ''.join(f'<span class="s-{t["s"]}"></span>' for t in ts) + '</a>')
    else:
        hist.append(f'<span class="hbar" title="{y}: нет записей"></span>')
    labels.append(f"<span>{'’' + str(y)[2:] if y % 5 == 0 or y in (minY, maxY) else ''}</span>")

nv = sum(len(t['v']) for t in T); nt = len({t['t'] for t in T if t['t']}); np_ = sum(1 for t in T if t['p'])
total_words = sum(N[k]['w'] for k in N)
stats = [(len(T), plural(len(T), 'поездка', 'поездки', 'поездок')), (maxY - minY + 1, plural(maxY - minY + 1, 'год', 'года', 'лет') + ' в дороге'),
         (nv, 'видео'), (nt, plural(nt, 'дневник', 'дневника', 'дневников')), (np_, plural(np_, 'фотоальбом', 'фотоальбома', 'фотоальбомов'))]

latest = [t for t in T if t['slug'] in COV or t['thumb']][:5]
_more = next((t for t in T if t['y'] >= 2021 and T.index(t) > T.index(latest[-1])), None)
latest_html = ''.join(f'''<a class="feat" href="trips/{t['slug']}.html">
  <span class="fimg"><img src="{('covers/' + t['slug'] + '.webp') if t['slug'] in COV else ('https://i.ytimg.com/vi/' + t['thumb'] + '/hqdefault.jpg')}" alt="" width="{COV[t['slug']][0] if t['slug'] in COV else 640}" height="{COV[t['slug']][1] if t['slug'] in COV else 360}"><span class="play">{ICO['play']}</span></span>
  <span class="fwhen">{e(t['wfull'])}</span><span class="fname">{e(t['n'])}</span></a>''' for t in latest)

ARCH_Y = 2021  # trips before this year live on archive.html
def year_sections(ys, root=''):
    out = []
    for y in ys:
        ts = [t for t in T if t['y'] == y]
        out.append(f'''<section class="year" id="y{y}"><h2>{y}<small>{len(ts)} {plural(len(ts), 'поездка', 'поездки', 'поездок')}</small></h2>
<ul class="trips">{''.join(row(t) for t in ts)}</ul></section>''')
    return out
recentY = [y for y in years if y >= ARCH_Y]; archY = [y for y in years if y < ARCH_Y]
nRecent = sum(1 for t in T if t['y'] >= ARCH_Y); nArch = len(T) - nRecent
sections = year_sections(recentY)
def tools(n):
    return f'''<div class="tools" role="search">
  <input id="q" type="search" placeholder="Поиск: Танзания, Крым, Петербург…" aria-label="Поиск по названию">
  <button class="chip" type="button" data-k="v" aria-pressed="false">С видео</button>
  <button class="chip" type="button" data-k="t" aria-pressed="false">С заметками</button>
  <button class="chip" type="button" data-k="m" aria-pressed="false">С картой</button>
  <span class="count" id="count">{n} из {n}</span>
</div>'''
_me = next((f for f in ('me.webp', 'me.jpg', 'me.png') if os.path.exists(os.path.join(S, f))), None)
_svg = lambda d: f'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
SOC_ICONS = [  # generic pictograms (not brand marks)
    ('YouTube', 'https://www.youtube.com/@alex.zakharov', _svg('<rect x="3" y="5" width="18" height="14" rx="4"/><path d="M10 9.2v5.6l4.8-2.8z" fill="currentColor" stroke="none"/>')),
    ('Telegram', 'https://t.me/iamzet', _svg('<path d="M21 4 3 11l6.5 2.2L12 20l3-5 5.5 4z"/><path d="M9.5 13.2 21 4"/>')),
    ('Дзен', 'https://dzen.ru/alexzakharov', _svg('<path d="M12 3c.6 4.7 4.3 8.4 9 9-4.7.6-8.4 4.3-9 9-.6-4.7-4.3-8.4-9-9 4.7-.6 8.4-4.3 9-9z"/>')),
    ('Почта', 'mailto:alex.m.zakharov@gmail.com', _svg('<rect x="3" y="5.5" width="18" height="13" rx="2.5"/><path d="m4 7 8 6 8-6"/>')),
]
AU_LINKS = ''.join(('<a href="%s" title="%s" aria-label="%s">%s</a>' if u.startswith('mailto:') else '<a href="%s" target="_blank" rel="noopener" title="%s" aria-label="%s">%s</a>') % (u, n, n, ic) for n, u, ic in SOC_ICONS)
YT_AVATAR = 'https://yt3.googleusercontent.com/VCV5s0xMYvfGBBXp79TL5JZM0dhkc3p_IdxonkBYF7Lofq0zzr30_OuFVT5qtI9wx7KWGdDy=s176-c-k-c0x00ffffff-no-rj'
_av = f'<img src="assets/{_me}" alt="" width="128" height="128">' if _me else f'<img src="{YT_AVATAR}" alt="" width="64" height="64" referrerpolicy="no-referrer" onerror="this.remove()"><span>АЗ</span>'
AUTHOR = f'''<aside class="author" aria-label="Об авторе"><div class="av">{_av}</div><div class="au-b"><div class="au-n">Александр Захаров</div><div class="au-d">На машине по России и не только</div>
<a class="au-go" href="travels.html">Путешествия →</a><div class="au-l">{AU_LINKS}</div></div></aside>'''
EMPTY = '<p class="empty" id="empty" hidden>Ничего не нашлось. Попробуйте другое название или снимите фильтры.</p>'
SOCIAL = ' · '.join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in (('YouTube', 'https://www.youtube.com/@alex.zakharov'), ('Telegram', 'https://t.me/iamzet'), ('Дзен', 'https://dzen.ru/alexzakharov'))) + ' · <a href="mailto:alex.m.zakharov@gmail.com">alex.m.zakharov@gmail.com</a>'
FOOT = f'<footer class="foot">© {maxY} Александр Захаров · {SOCIAL}</footer>'

TRAVELS_LINK = f'<a class="archlink" href="travels.html"><span class="al-k">Путешествия</span><span class="al-t">{ARCH_Y}–{maxY}</span><span class="al-n">{nRecent} {plural(nRecent, "поездка", "поездки", "поездок")} →</span></a>'
ARCH_LINK = f'<a class="archlink" href="archive.html"><span class="al-k">Архив</span><span class="al-t">{min(archY)}–{max(archY)}</span><span class="al-n">{nArch} {plural(nArch, "поездка", "поездки", "поездок")} →</span></a>'
index = head('Все путешествия — iamzet.travels', f'Путевой журнал Александра Захарова: {len(T)} поездок с {minY} года — путевые заметки, видеоотчёты, карты маршрутов и фотоальбомы.', '') + f'''<body class="home">
<div class="wrap">
<h1 class="vh">iamzet.travels — на машине по России и не только</h1>
<section class="latest" aria-label="Последние поездки"><div class="top">{AUTHOR}<div class="carousel"><div class="cnav"><button type="button" class="cprev" aria-label="Назад"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 4l-6 6 6 6"/></svg></button><button type="button" class="cnext" aria-label="Вперёд"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 4l6 6-6 6"/></svg></button></div><div class="feats" tabindex="0">{latest_html}<div class="more"><span class="more-c"><a class="more-t" href="{"travels.html#t-" + _more["slug"] if _more else "travels.html"}">Ещё →</a></span></div></div></div></div></section>
<section class="worldmap" aria-label="Карта всех поездок"><div class="mapbox" id="worldmap"><span class="maploading">Загружаем карту…</span></div></section>
</div>
<script src="assets/site.js?v={VER}" defer></script>
</body>
</html>'''

travels = head('Путешествия — iamzet.travels', f'Путешествия Александра Захарова с {ARCH_Y} года: {nRecent} поездок — путевые заметки, видеоотчёты, карты маршрутов и фотоальбомы.', '') + f'''<body class="home arch">
<div class="topbar"><div class="wrap"><a href="index.html" class="back">← Главная</a><span class="brand">iamzet.travels</span></div></div>
<div class="wrap">
<header class="masthead"><h1 class="brandh">Путешествия</h1><p class="archsub">{ARCH_Y}–{maxY} · {nRecent} {plural(nRecent, 'поездка', 'поездки', 'поездок')}</p></header>
{tools(nRecent)}
<main id="list">{''.join(sections)}{EMPTY}</main>
<nav class="sections">{ARCH_LINK}</nav>
{FOOT}
</div>
<script src="assets/site.js?v={VER}" defer></script>
</body>
</html>'''

# ---------- trip pages ----------
def add_ids(h):
    if len(re.findall(r'<h2>', h)) == 1:
        h = re.sub(r'<h2>.*?</h2>\n?', '', h, count=1)
    levels = sorted({int(x) for x in re.findall(r'<h([234])>', h)})
    if levels and levels[0] > 2:
        sh = levels[0] - 2
        h = re.sub(r'<(/?)h([234])>', lambda m: f'<{m.group(1)}h{max(2, min(4, int(m.group(2)) - sh))}>', h)
        levels = sorted({int(x) for x in re.findall(r'<h([234])>', h)})
    toc, n = [], [0]
    def rep(m):
        n[0] += 1; tag, inner = m.group(1), m.group(2)
        hid = f's{n[0]}'
        txt = re.sub('<[^>]+>', '', inner)
        if tag == 'h2': toc.append((hid, txt, 1))
        elif tag == 'h3' and 2 in levels: toc.append((hid, txt, 2))
        return f'<{tag} id="{hid}">{inner}</{tag}>'
    return re.sub(r'<(h[234])>(.*?)</\1>', rep, h), toc

LOGO_DZ = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="12" fill="currentColor"/><path d="M12 3.2c.25 4.6 4.2 8.55 8.8 8.8-4.6.25-8.55 4.2-8.8 8.8-.25-4.6-4.2-8.55-8.8-8.8 4.6-.25 8.55-4.2 8.8-8.8z" fill="var(--bg)"/></svg>'
LOGO_YT = '<svg viewBox="0 0 28 20" aria-hidden="true"><rect width="28" height="20" rx="5" fill="#FF0000"/><path d="M11.2 5.8v8.4L18.4 10z" fill="#fff"/></svg>'

def vcard(num, yt, dz, title, dur):
    """yt: youtube id or None; dz: (embed, thumb) or None"""
    cls = 'yt' + (' has-dz' if dz else '') + (' has-yt' if yt else '')
    attrs = (f' data-id="{yt}"' if yt else '') + (f' data-dzen="{dz[0]}"' if dz else '')
    imgs = ''
    if dz: imgs += f'<img class="th-dz" src="{dz[1]}" alt="" loading="lazy" width="516" height="290">'
    if yt: imgs += f'<img class="th-yt" src="https://i.ytimg.com/vi/{yt}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360">'
    links = ''
    if dz: links += f'<a class="ytlink l-dz" href="https://dzen.ru/embed/{dz[0]}" target="_blank" rel="noopener">Дзен {ICO["out"]}</a>'
    if yt: links += f'<a class="ytlink l-yt" href="https://youtu.be/{yt}" target="_blank" rel="noopener">YouTube {ICO["out"]}</a>'
    lab = e(title) if title else 'видео'
    box = f'<div class="{cls}"{attrs}>{imgs}<button type="button" class="ytplay" aria-label="Смотреть: {lab}">{ICO["play"]}</button>{links}</div>'
    vt = ''
    if title or dur:
        vt = '<div class="vt">' + (f'<span class="vn">{num}</span>' if num else '') + (f'<b>{e(title)}</b>' if title else '<b></b>') + (f'<span class="vd">{dur}</span>' if dur else '') + '</div>'
    return f'<div class="vcard">{box}{vt}</div>'

def video_block(t):
    items = []; anyyt = anydz = False
    if t.get('vtitles'):
        for k, (i, ti, d) in enumerate(t['vtitles'], 1):
            dz = DZY.get(i)
            items.append(vcard(k, i, (dz[0], dz[1]) if dz else None, ti, d)); anyyt = True; anydz = anydz or bool(dz)
    else:
        dzl = DZ.get(t['slug'], [])
        ytn = 0
        for u, vid in zip(t['v'], t['vids']):
            if vid:
                dz = dzl[ytn] if ytn < len(dzl) else None
                if not dz and vid in DZY and len(DZY[vid]) >= 4:
                    y = DZY[vid]; dz = [y[0], y[2], y[3], y[1]]
                ytn += 1
                multi = len([x for x in t['vids'] if x]) > 1
                items.append(vcard(ytn if multi and dz else None, vid, (dz[0], dz[3]) if dz else None, dz[1] if dz else '', dz[2] if dz else ''))
                anyyt = True; anydz = anydz or bool(dz)
            elif playlist_id(u):
                items.append(f'''<div class="yt pl has-yt" data-list="{playlist_id(u)}"><span class="plbg"><span class="plt">Плейлист<br>«{e(t['n'])}»</span></span><button type="button" class="ytplay" aria-label="Смотреть плейлист">{ICO['play']}</button><a class="ytlink l-yt" href="{e(u)}" target="_blank" rel="noopener">YouTube {ICO['out']}</a></div>'''); anyyt = True
            else:
                lv = LV.get(t['slug'])
                if lv and 'yandex' in u:
                    items.append(f'<div class="vcard"><video class="lvid" controls preload="none" playsinline poster="../covers/{t["slug"]}.video.webp" width="{lv[0]}" height="{lv[1]}" style="aspect-ratio:{lv[0]}/{lv[1]}"><source src="{(CV["base"] + t["slug"] + ".mp4") if t["slug"] in CV.get("slugs", []) else ("../videos/" + t["slug"] + ".mp4")}" type="video/mp4"></video><div class="vt"><b>Видео</b><span class="vd">{lv[2]}</span></div></div>')
                    continue
                items.append(f'''<a class="ydisk" href="{e(u)}" target="_blank" rel="noopener"><span class="plt">{ICO['play']} Видео на Яндекс Диске</span><span class="sub">Откроется в новой вкладке {ICO['out']}</span></a>''')
    for x in sorted(DZX.get(t['slug'], []), reverse=True):
        pos, em, th, ti, du = x[:5]; yx = x[5] if len(x) > 5 else None
        items.insert(pos, vcard(None, yx, (em, th), ti, du)); anydz = True; anyyt = anyyt or bool(yx)
    if not items: return ''
    sw = ''
    if anyyt or anydz:
        sw = ('<div class="vsrc" role="group" aria-label="Где смотреть">'
              + f'<button type="button" data-src="dzen" aria-pressed="true"{"" if anydz else " disabled title='Этих видео пока нет на Дзене'"}>{LOGO_DZ}<span>Дзен</span></button>'
              + f'<button type="button" data-src="yt" aria-pressed="false">{LOGO_YT}<span>YouTube</span></button></div>')
    cls = 'vids one' if len(items) == 1 else 'vids'
    pl = f'<p class="mapnote"><a href="{e(t["vplaylist"])}" target="_blank" rel="noopener">Плейлист на YouTube {ICO["out"]}</a></p>' if t.get('vplaylist') else ''
    return f'{sw}<div class="{cls}">{"".join(items)}</div>{pl}'

def trip_page(t, prev, nxt):
    note = t['note']
    body_html, toc = add_ids(note['html']) if note else ('', [])
    mid = map_mid(t['m'])
    tabs, panels = [], []
    # Заметки
    tochtml = ''
    if len(toc) >= 3:
        tochtml = '<nav class="toc" aria-label="Содержание"><details><summary class="kicker">Содержание · ' + str(len(toc)) + '</summary><ol>' + ''.join(f'<li class="l{lv}"><a href="#{i}">{e(x)}</a></li>' for i, x, lv in toc) + '</ol></details></nav>'
    if note:
      tabs.append(('notes', 'Заметки', 'text', f"{read_min(t['words'])} мин"))
      panels.append(('notes', f'''<div class="reading{' has-toc' if tochtml else ''}">{tochtml}<article class="prose">{body_html}</article></div>'''))
    # Фото
    if t['gal']:
        tabs.append(('photo', 'Фото', 'photo', str(len(t['gal']))))
        items = ''.join(
            f'<a class="gi" href="../photos/{p["k"]}/{p["n"]:03d}.webp" data-w="{p["w"]}" data-h="{p["h"]}" style="--r:{p["w"]/p["h"]:.4f}"'
            + (f' data-c="{e(p["c"])}"' if p['c'] else '')
            + f'><img src="../photos/{p["k"]}/t/{p["n"]:03d}.webp" width="{p["tw"]}" height="{p["th"]}" loading="lazy" alt="{e(p["c"] or t["n"] + ", фото " + str(i + 1))}"></a>'
            for i, p in enumerate(t['gal']))
        panels.append(('photo', f'<div class="gal">{items}</div>'))
    elif t['p']:
        tabs.append(('photo', 'Фото', 'photo', ''))
        panels.append(('photo', f'''<a class="album" href="{e(t['p'])}" target="_blank" rel="noopener">
<span class="album-ico">{ICO['photo']}</span><span class="album-t">Фотоальбом поездки</span>
<span class="album-s">Общий альбом iCloud — откроется в новой вкладке {ICO['out']}</span></a>'''))
    # Видео
    if t['v']:
        n = len(t['v']) + len(DZX.get(t['slug'], [])); cnt = '' if n == 1 else str(n)
        tabs.append(('video', 'Видео', 'play', cnt))
        panels.append(('video', video_block(t)))
    # Карта
    if t['maps']:
        tabs.append(('map', 'Карта', 'map', str(len(t['maps'])) if len(t['maps']) > 1 else ''))
        blocks = []
        for lab, u in t['maps']:
            mid = map_mid(u)
            h = f'<h3 class="maph">{e(lab)}</h3>' if lab and len(t['maps']) > 1 else ''
            if mid:
                blocks.append(f'<div class="mapitem"><div class="mapbox" data-mid="{e(mid)}"><span class="maploading">Загружаем карту…</span></div>{h}</div>')
            else:
                blocks.append(f'''<div class="mapitem">{h}<a class="album" href="{e(u)}" target="_blank" rel="noopener"><span class="album-ico">{ICO['map']}</span><span class="album-t">Карта маршрута</span><span class="album-s">Откроется в Google Maps {ICO['out']}</span></a></div>''')
        panels.append(('map', f'<div class="maps{" multi" if len(blocks) > 1 else ""}">' + ''.join(blocks) + '</div>'))
    tabbar = '<div class="tabbar" role="tablist" aria-label="Материалы поездки">' + ''.join(
        f'<a class="tab" role="tab" id="tab-{k}" href="#{k}" aria-controls="p-{k}" aria-selected="{"true" if i == 0 else "false"}">{ICO[ic]}<span>{lab}</span>{f'<small class="{"min" if "мин" in c else "n"}">{c}</small>' if c else ""}</a>'
        for i, (k, lab, ic, c) in enumerate(tabs)) + '</div>'
    panelhtml = ''.join(f'<section class="panel" role="tabpanel" id="p-{k}" aria-labelledby="tab-{k}"{"" if i == 0 else " hidden"}>{h}</section>' for i, (k, h) in enumerate(panels))
    def nav(x, lab, cls):
        if not x: return '<span></span>'
        return f'<a class="pn {cls}" href="{x["slug"]}.html"><span class="pl2">{lab}</span><span class="pnn">{e(x["n"])}</span><span class="pny">{e(x["wfull"])}</span></a>'
    parts = [x for x, ok in (('путевые заметки', note), ('фотографии', t['p']), ('видео', t['v']), ('карта маршрута', t['m'])) if ok]
    desc = f"{t['n']}, {t['wfull'].lower()}: " + ', '.join(parts) + '.'
    og = f'<meta property="og:image" content="https://i.ytimg.com/vi/{t["thumb"]}/hqdefault.jpg">' if t['thumb'] else ''
    return head(f"{t['n']} · {t['ylab']} — iamzet.travels", desc, '../', og) + f'''<body class="tripp">
<div class="topbar"><div class="wrap"><a href="../{'archive.html' if t['y'] < ARCH_Y else 'travels.html'}" class="back">← {'Архив' if t['y'] < ARCH_Y else 'Путешествия'}</a><span class="brand">iamzet.travels</span></div></div>
<div class="wrap">
<header class="thead">
  <div class="twhen"><i class="s-{t['s']}"></i>{e(t['wfull'])}</div>
  <h1>{e(t['n'])}</h1>
  {flag_html(t, '../')}
</header>
</div>
<div class="tabwrap"><div class="wrap">{tabbar}</div></div>
<div class="wrap">
{panelhtml}
<nav class="prevnext" aria-label="Соседние поездки">{nav(nxt, '← Раньше', 'older')}{nav(prev, 'Позже →', 'newer')}</nav>
<footer class="foot">© {maxY} Александр Захаров · <a href="../index.html">Главная</a> · <a href="../{'archive.html' if t['y'] < ARCH_Y else 'travels.html'}">{'Архив' if t['y'] < ARCH_Y else 'Путешествия'}</a> · {SOCIAL}</footer>
</div>
<script src="../assets/site.js?v={VER}" defer></script>
</body>
</html>'''

# regenerate pages in place: photos/, covers/, maps/, CNAME are left untouched
import glob as _glob
for _f in _glob.glob(os.path.join(OUT, 'trips', '*.html')): os.remove(_f)
os.makedirs(os.path.join(OUT, 'trips'), exist_ok=True); os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(index)
open(os.path.join(OUT, 'travels.html'), 'w', encoding='utf-8').write(travels)
archive = head('Архив — iamzet.travels', f'Архив путевого журнала Александра Захарова: {nArch} поездок {min(archY)}–{max(archY)} годов.', '') + f'''<body class="home arch">
<div class="topbar"><div class="wrap"><a href="index.html" class="back">← Главная</a><span class="brand">iamzet.travels</span></div></div>
<div class="wrap">
<header class="masthead"><h1 class="brandh">Архив</h1><p class="archsub">{min(archY)}–{max(archY)} · {nArch} {plural(nArch, 'поездка', 'поездки', 'поездок')}</p></header>
{tools(nArch)}
<main id="list">{''.join(year_sections(archY))}{EMPTY}</main>
<nav class="sections">{TRAVELS_LINK}</nav>
{FOOT}
</div>
<script src="assets/site.js?v={VER}" defer></script>
</body>
</html>'''
open(os.path.join(OUT, 'archive.html'), 'w', encoding='utf-8').write(archive)
for i, t in enumerate(paged):
    prev = paged[i - 1] if i > 0 else None          # newer
    nxt = paged[i + 1] if i + 1 < len(paged) else None  # older
    open(os.path.join(OUT, 'trips', t['slug'] + '.html'), 'w', encoding='utf-8').write(trip_page(t, prev, nxt))
for k in sorted({ph['k'] for t in T if t['gal'] for ph in t['gal']}):
    dst = os.path.join(OUT, 'photos', k)
    if not os.path.exists(dst) and os.path.isdir(os.path.join(S, 'photos', k)):
        shutil.copytree(os.path.join(S, 'photos', k), dst, ignore=shutil.ignore_patterns('index.json'))
_cv = os.path.join(S, 'covers_new')  # drop new cover images here; they are copied to /covers
if os.path.isdir(_cv):
    shutil.copytree(_cv, os.path.join(OUT, 'covers'), ignore=shutil.ignore_patterns('*.txt'), dirs_exist_ok=True)
os.makedirs(os.path.join(OUT, 'assets', 'flags'), exist_ok=True)
for c in {c for v in CN.values() for c in v}:
    shutil.copy(os.path.join(S, 'flags', c + '.svg'), os.path.join(OUT, 'assets', 'flags', c + '.svg'))
if _me: shutil.copy(os.path.join(S, _me), os.path.join(OUT, 'assets', _me))
shutil.copy(os.path.join(S, 'style.css'), os.path.join(OUT, 'assets', 'style.css'))
shutil.copy(os.path.join(S, 'site.js'), os.path.join(OUT, 'assets', 'site.js'))
shutil.copytree(os.path.join(S, 'vendor'), os.path.join(OUT, 'assets', 'vendor'), dirs_exist_ok=True)
# World map data (from maps/cities.kml + simplified countries)
import xml.etree.ElementTree as _ET
_K = '{http://www.opengis.net/kml/2.2}'
_titles = {t['slug']: t['n'] for t in T}
_pts = {}
for _p in _ET.parse(os.path.join(ROOT, 'maps', 'cities.kml')).getroot().iter(_K + 'Placemark'):
    _d = {d.get('name'): d.findtext(_K + 'value') for d in _p.iter(_K + 'Data')}
    _lon, _lat = map(float, _p.findtext('.//' + _K + 'coordinates').strip().split(',')[:2])
    _link = _d.get('Trip link') or ''
    _slug = _link.rsplit('/', 1)[-1][:-5] if _link else ''
    _key = (_p.findtext(_K + 'name').strip(), round(_lat, 3), round(_lon, 3))
    _o = _pts.setdefault(_key, {'n': _key[0], 'la': round(_lat, 4), 'lo': round(_lon, 4), 'y': '', 's': '', 't': ''})
    if (_d.get('Last visit') or '') > _o['y']: _o['y'] = _d.get('Last visit') or ''
    if _slug and _slug in _titles and not _o['s']: _o['s'] = _slug; _o['t'] = _titles[_slug]
# Country of each city: point-in-polygon over the visited-countries layer, with the site's own conventions
from shapely.geometry import shape as _shape, Point as _Pt
_CK = json.load(open(os.path.join(S, 'countries.geojson'), encoding='utf-8'))
_RCN = {v: k for k, v in CNAME.items()}; _RCN['Великобритания'] = 'gb'; CNAME.setdefault('gb', 'Великобритания'); CNAME.setdefault('jo', 'Иордания')
_shp = [(_RCN.get(f['properties']['n']), _shape(f['geometry'])) for f in _CK['features']]
def _country(o):
    la, lo = o['la'], o['lo']
    if o['n'] in ('Гагра', 'Сухуми', 'Очамчира', 'Пицунда', 'Новый Афон', 'Гудаута'): return 'ab'
    if 32.4 <= lo <= 36.7 and 44.3 <= la <= 46.0: return 'ua' if (o['y'] or '9999') <= '2013' else 'ru'
    if o['n'] == 'Иерихон': return 'ps'
    pt = _Pt(lo, la); best = min(_shp, key=lambda cs: cs[1].distance(pt))
    return best[0] if best[1].distance(pt) < 0.6 else ''
WIKI = {'Санкт Петербург': 'Санкт-Петербург', 'Ростов на Дону': 'Ростов-на-Дону', 'Хвбвровск': 'Хабаровск', 'Сауз Бенд': 'Саут-Бенд',
        'Мбамба-Бэй': 'Мбамба-Бей', 'Ростов': 'Ростов (город)', 'Онега': 'Онега (город)', 'Бейгеу': 'Бейнеу', 'Плимут': 'Плимут (Массачусетс)',
        'Салем': 'Салем (Массачусетс)', 'Kalyazin': 'Калязин', 'Крк': 'Крк (город)', 'Бакар': 'Бакар (Хорватия)',
        'Ош': 'Ош (город)', 'Талас': 'Талас (город)', 'Нарын': 'Нарын (город)', 'Алания': 'Аланья', 'Кемь': 'Кемь (город)', 'Умба': 'Умба (посёлок)',
        'Мышкин': 'Мышкин (город)', 'Лида': 'Лида (город)', 'Хасан': 'Хасан (посёлок)', 'Шуя': 'Шуя (город)', 'Плёс': 'Плёс (город)',
        'Юрьевец': 'Юрьевец (Ивановская область)', 'Кировск': 'Кировск (Мурманская область)', 'Белогорск': 'Белогорск (Амурская область)',
        'Александров': 'Александров (город)', 'Дмитров': 'Дмитров', 'Звенигород': 'Звенигород', 'Городец': 'Городец', 'Брест': 'Брест (Белоруссия)',
        'Борзя': 'Борзя', 'Терней': 'Терней (посёлок)', 'Аршан': 'Аршан (Бурятия)', 'Хужир': 'Хужир', 'Бабати': 'Бабати', 'Моши': 'Моши (Танзания)',
        'Тендума': 'Тундума', 'Гома': 'Гома (город)', 'Чалус': 'Чалус', 'Астара': 'Астара (Иран)', 'Орду': 'Орду', 'Атырау': 'Атырау',
        'Rodi Garganico': 'Роди-Гарганико', 'Мегри': 'Мегри', 'Каракол': 'Каракол', 'Ховд': 'Ховд (город)', 'Чойболсан': 'Чойбалсан (город)', 'Хархорин': 'Хархорин'}
WIKI.update({'Домбай': 'Домбай (посёлок)', 'Листвянка': 'Листвянка (Иркутская область)', 'Несебар': 'Несебыр', 'Ростов': 'Ростов (Ярославская область)',
             'Сауз Бенд': 'Саут-Бенд (Индиана)', 'Светлогорск': 'Светлогорск (Калининградская область)', 'Табора': 'Табора (город)', 'Татван': 'Татван',
             'Тендума': 'Тундума', 'Териберка': 'Териберка (село)', 'Трескол': 'Терскол', 'Хужир': 'Хужир (Иркутская область)', 'Мбамба-Бэй': 'Мбамба-Бей'})
for _o in _pts.values():
    _o['c'] = _country(_o)
    if WIKI.get(_o['n']): _o['w'] = WIKI[_o['n']]
# City cards: Wikipedia photo/link + official site, cached in src/city_info.json and assets/cities/.
# Every build tries to refresh the cache (CI has internet); offline builds just reuse it.
import urllib.request, urllib.parse, math, io, hashlib as _hh
_CI_PATH = os.path.join(S, 'city_info.json')
_CI = json.load(open(_CI_PATH, encoding='utf-8')) if os.path.exists(_CI_PATH) else {}
_UA = {'User-Agent': 'iamzet.travels site builder (https://iamzet.ru; alex.m.zakharov@gmail.com)'}
def _get(url, raw=False):
    import time; time.sleep(0.05)
    with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=15) as r:
        b = r.read()
    return b if raw else json.loads(b.decode('utf-8'))
def _km(a1, o1, a2, o2):
    r = math.pi / 180; x = (o2 - o1) * r * math.cos((a1 + a2) / 2 * r); y = (a2 - a1) * r
    return math.hypot(x, y) * 6371
def _api(params, host='ru.wikipedia.org'):
    import time
    for i in range(4):
        try:
            return _get(f'https://{host}/w/api.php?' + urllib.parse.urlencode(dict(params, format='json', formatversion=2)))
        except Exception as ex:
            err = ex; time.sleep(2 * (i + 1))
    raise err
def _wiki_batch(objs):
    """Resolve each city to a ru.wikipedia article near its point (<60 km): image, url, official site."""
    cands = {id(o): list(dict.fromkeys([o.get('w') or o['n'], o['n'] + ' (город)', o['n']])) for o in objs}
    titles = sorted({t for v in cands.values() for t in v})
    pages, norm = {}, {}
    for i in range(0, len(titles), 40):
        j = _api({'action': 'query', 'redirects': 1, 'prop': 'coordinates|pageimages|pageprops|info', 'inprop': 'url',
                  'piprop': 'thumbnail', 'pithumbsize': 640, 'pilimit': 'max', 'colimit': 'max', 'ppprop': 'disambiguation|wikibase_item', 'titles': '|'.join(titles[i:i + 40])})['query']
        for n in j.get('normalized', []) + j.get('redirects', []): norm[n['from']] = n['to']
        for pg in j.get('pages', []): pages[pg['title']] = pg
    def res(t):
        seen = 0
        while t in norm and seen < 5: t = norm[t]; seen += 1
        return pages.get(t)
    out, qids = {}, {}
    for o in objs:
        r = {'url': '', 'site': '', 'img_src': ''}
        for t in cands[id(o)]:
            pg = res(t)
            if not pg or pg.get('missing') or 'disambiguation' in pg.get('pageprops', {}): continue
            c = (pg.get('coordinates') or [None])[0]
            if not c or _km(o['la'], o['lo'], c['lat'], c['lon']) > 60: continue
            r = {'url': pg.get('fullurl', ''), 'site': '', 'img_src': (pg.get('thumbnail') or {}).get('source', '')}
            q = pg.get('pageprops', {}).get('wikibase_item')
            if q: qids[q] = r
            break
        out[id(o)] = r
    ql = sorted(qids)
    for i in range(0, len(ql), 40):
        try:
            ents = _api({'action': 'wbgetentities', 'ids': '|'.join(ql[i:i + 40]), 'props': 'claims'}, host='www.wikidata.org')['entities']
            for q, ent in ents.items():
                try: qids[q]['site'] = ent['claims']['P856'][0]['mainsnak']['datavalue']['value']
                except Exception: pass
        except Exception as ex: print('wikidata failed', ex)
    return out
_online = True
try: _get('https://ru.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote('Владимир_(город)'))
except Exception as _ex: _online = False; print('wikipedia unreachable:', _ex)
os.makedirs(os.path.join(OUT, 'assets', 'cities'), exist_ok=True)
_fresh = {}
if _online:
    try: _fresh = _wiki_batch(list(_pts.values()))
    except Exception as _ex: print('wikipedia lookup failed:', _ex)
for _o in _pts.values():
    _key = f"{_o['n']}|{_o['la']}|{_o['lo']}"
    _info = _CI.get(_key)
    _new = _fresh.get(id(_o))
    if _new is not None and not _new.get('url') and _info and _info.get('url'): _new = None  # keep the cached article if lookup came back empty
    if _new is not None:
        try:
            if _new.get('img_src'):
                _fn = _hh.sha1(_key.encode()).hexdigest()[:12] + '.webp'
                if not (_info and _info.get('img_src') == _new['img_src'] and os.path.exists(os.path.join(OUT, 'assets', 'cities', _fn))):
                    from PIL import Image as _Img
                    _im = _Img.open(io.BytesIO(_get(_new['img_src'], raw=True))).convert('RGB')
                    _w, _h = _im.size; _r = max(520 / _w, 292 / _h)
                    _im = _im.resize((max(1, round(_w * _r)), max(1, round(_h * _r))), _Img.LANCZOS)
                    _l, _t = (_im.width - 520) // 2, (_im.height - 292) // 2
                    _im.crop((_l, _t, _l + 520, _t + 292)).save(os.path.join(OUT, 'assets', 'cities', _fn), 'WEBP', quality=72)
                _new['img'] = _fn
            _info = _new
        except Exception as _ex:
            print('city image failed', _o['n'], _ex)
            if _info is None: _info = dict(_new, img_src='')
    if _info:
        _CI[_key] = _info
        _o['wi'] = {k: _info.get(k, '') for k in ('img', 'url', 'site') if _info.get(k)}
json.dump(dict(sorted(_CI.items())), open(_CI_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('cities', len(_pts), 'with info', sum(1 for o in _pts.values() if o.get('wi')), 'online' if _online else 'offline (cache)')
for _c in {o['c'] for o in _pts.values() if o['c']}:
    shutil.copy(os.path.join(S, 'flags', _c + '.svg'), os.path.join(OUT, 'assets', 'flags', _c + '.svg'))
_cn_used = {o['c']: CNAME.get(o['c'], o['c']) for o in _pts.values() if o['c']}
# as .js (not .json) so the map also works when index.html is opened straight from disk (file://)
open(os.path.join(OUT, 'assets', 'map-world.js'), 'w', encoding='utf-8').write('window.__WW=' + open(os.path.join(S, 'world.json'), encoding='utf-8').read() + ';')
open(os.path.join(OUT, 'assets', 'map-data.js'), 'w', encoding='utf-8').write('window.__WM={cn:' + json.dumps(_cn_used, ensure_ascii=False) + ',c:' + json.dumps(list(_pts.values()), ensure_ascii=False, separators=(',', ':')) + ',k:' + open(os.path.join(S, 'countries.geojson'), encoding='utf-8').read() + '};')
print('trips', len(T), 'pages', len(paged), 'words', total_words)
