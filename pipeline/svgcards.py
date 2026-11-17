"""Kumi post illustrations as SVG (1080x1350), in the style of the published W46 posts.

Usage: python3 svgcards.py weeks/<week>/week.json   -> writes <slug>.svg next to week.json,
       then: node svg2png.js weeks/<week>            -> <slug>.png for publishing (IG/Threads need PNG/JPEG).

Each SVG is self-contained: text stays live (editable in Figma/Illustrator) and the fonts it uses
(Rubik 500/700, Marck Script) are embedded as subset WOFF2 so it renders the same everywhere.

Each post in week.json has "layout" and "card" fields; layouts: swap, versus, pair, quiz, list.
Lines are given pre-broken (lists of strings), because SVG does not wrap text.
"""
import base64, io, json, os, pathlib, sys
from xml.sax.saxutils import escape as esc
from fontTools.ttLib import TTFont
from fontTools import subset as ftsubset

HERE = pathlib.Path(__file__).parent
FONTS = HERE / 'fonts'
W, H = 1080, 1350
INK = '#1E1A16'; CREAM = '#FFFAEE'; RED = '#DE5B45'; GREEN = '#3E8A5A'; MUTED = '#4A3F36'
YELLOW = '#FFD91A'; BLUE = '#3B55F0'; SKY = '#B4EAF6'

FACES = [  # family, weight, files
    ('Rubik', 500, ['rubik-latin-500-normal.woff2', 'rubik-cyrillic-500-normal.woff2']),
    ('Rubik', 700, ['rubik-latin-700-normal.woff2', 'rubik-cyrillic-700-normal.woff2']),
    ('Marck Script', 400, ['marck-script-latin-400-normal.woff2', 'marck-script-cyrillic-400-normal.woff2']),
]

def font_css(text):
    chars = set(text) | set('0123456789 ')
    out = []
    for fam, wt, files in FACES:
        for fn in files:
            f = TTFont(FONTS / fn)
            cmap = f.getBestCmap()
            cps = sorted(ord(c) for c in chars if ord(c) in cmap)
            if not cps: continue
            opts = ftsubset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['*']
            s = ftsubset.Subsetter(opts); s.populate(unicodes=cps); s.subset(f)
            buf = io.BytesIO(); f.flavor = 'woff2'; f.save(buf)
            rng = ','.join('U+%04X' % c for c in cps)
            out.append("@font-face{font-family:'%s';font-weight:%d;src:url(data:font/woff2;base64,%s) format('woff2');unicode-range:%s}"
                       % (fam, wt, base64.b64encode(buf.getvalue()).decode(), rng))
    return '\n'.join(out)

# ---------- primitives ----------
def T(x, y, s, size, fam='Rubik', wt=700, fill=INK, anchor='start', extra=''):
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-weight="{wt}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" {extra}>{esc(s)}</text>')

def lines(x, y, arr, size, lh, **kw):
    return ''.join(T(x, y + i * lh, s, size, **kw) for i, s in enumerate(arr))

def hand(x, y, s, size=56, fill=MUTED, **kw):
    return T(x, y, s, size, fam='Marck Script', wt=400, fill=fill, **kw)

def card(x, y, w, h, fill=CREAM, rot=0, r=44, sw=7):
    cx, cy = x + w / 2, y + h / 2
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{INK}" stroke-width="{sw}" '
            f'transform="rotate({rot} {cx} {cy})"/>')

def strike(x, y, w, color=RED, sw=9):
    return f'<line x1="{x - 8}" y1="{y}" x2="{x + w + 8}" y2="{y - 4}" stroke="{color}" stroke-width="{sw}" stroke-linecap="round"/>'

def logo(x=56, y=52):
    return (f'<g transform="translate({x} {y})">'
            f'<rect width="262" height="104" rx="52" fill="{CREAM}" stroke="{INK}" stroke-width="6"/>'
            f'<g transform="translate(30 20) rotate(-6 32 32)">'
            f'<rect x="0" y="0" width="46" height="46" rx="10" fill="{CREAM}" stroke="{INK}" stroke-width="5"/>'
            f'<rect x="18" y="16" width="46" height="46" rx="10" fill="{SKY}" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M18 26 a10 10 0 0 1 10 -10 H46 V36 a10 10 0 0 1 -10 10 H18 Z" fill="{YELLOW}" stroke="{INK}" stroke-width="5"/>'
            f'<circle cx="29" cy="27" r="4" fill="{BLUE}"/><circle cx="38" cy="25" r="2.6" fill="{BLUE}"/>'
            f'<circle cx="33" cy="36" r="3.4" fill="{BLUE}"/><circle cx="25" cy="38" r="2.4" fill="{BLUE}"/></g>'
            f'{T(124, 68, "Kumi", 46, wt=700)}</g>')

def tag(s, x, y, w, fill='#CDB8F8', rot=2):
    return (f'<g transform="rotate({rot} {x + w / 2} {y + 40})"><rect x="{x}" y="{y}" width="{w}" height="80" rx="30" fill="{fill}" '
            f'stroke="{INK}" stroke-width="6"/>{T(x + w / 2, y + 52, s, 36, wt=500, anchor="middle")}</g>')

def lattice(bg, line):
    p = ''.join(f'<path d="M{x} -20 L{x + 760} 1370 M{x} 1370 L{x + 760} -20" />' for x in range(-760, 1100, 120))
    return f'<rect width="{W}" height="{H}" fill="{bg}"/><g stroke="{line}" stroke-width="7" fill="none">{p}</g>'

def dots(bg, color, seed=7):
    import random
    rnd = random.Random(seed); c = ''
    for _ in range(26):
        c += f'<circle cx="{rnd.randint(0, W)}" cy="{rnd.randint(0, H)}" r="{rnd.choice([10, 16, 24, 34])}" fill="{color}" opacity=".9"/>'
    return f'<rect width="{W}" height="{H}" fill="{bg}"/>{c}'

def waves(y, color, n=3):
    out = ''
    for k in range(n):
        yy = y + k * 76
        d = f'M-20 {yy} ' + ' '.join(f'q 30 -30 60 0' for _ in range(20))
        out += f'<path d="{d}" fill="none" stroke="{color}" stroke-width="14" stroke-linecap="round"/>'
    return out

def stars(bg, color):
    import random
    rnd = random.Random(3); c = ''
    for _ in range(40):
        x, y, r = rnd.randint(0, W), rnd.randint(0, H), rnd.choice([3, 4, 6])
        c += f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>'
    return f'<rect width="{W}" height="{H}" fill="{bg}"/>{c}'

# ---------- layouts ----------
def L_swap(c):
    # like post 1: background lattice, tilted cream card, handwritten right word above the crossed-out wrong one
    s = lattice(c.get('bg', '#FFCB3D'), c.get('line', '#F29A1F')) + logo() + tag(c['tag'], 690, 62, 330)
    s += card(110, 330, 860, 720, rot=-3)
    s += f'<g transform="rotate(-3 540 690)">'
    s += hand(c.get('right_x', 250), 520, c['right'], 150, fill=GREEN)
    s += T(180, 680, c['pre'], 140) + T(c.get('wrong_x', 300), 680, c['wrong'], 140, fill=RED)
    s += strike(c.get('wrong_x', 300), 640, c.get('wrong_w', 300), color='#B23A2A', sw=12)
    s += T(180, 840, c['post'], 140)
    s += T(190, 970, c['ru'], 44, wt=500, fill=MUTED) + '</g>'
    return s

def L_versus(c):
    # like post 3: two overlapping cards with a yellow "≠" square between them
    s = f'<rect width="{W}" height="{H}" fill="{c.get("bg", "#BFE8CF")}"/>' + logo()
    s += hand(1020, 120, c['kicker'], 56, anchor='end') + T(1020, 205, c['kicker2'], 58, anchor='end')
    s += card(60, 310, 560, 580, rot=-6) + card(470, 640, 540, 560, fill=c.get('fill2', '#F9DCCB'), rot=-6)
    s += '<g transform="rotate(-6 540 750)">'
    s += hand(120, 430, c['a_note'], 52) + lines(120, 530, c['a'], 84, 92)
    s += hand(540, 950, c['b_note'], 52) + lines(540, 1050, c['b'], 84, 92)
    s += f'<rect x="440" y="650" width="210" height="210" rx="40" fill="{YELLOW}" stroke="{INK}" stroke-width="7"/>'
    s += T(545, 810, '≠', 170, anchor='middle') + '</g>'
    s += T(540, 1290, c['foot'], 38, wt=500, anchor='middle')
    return s

def L_pair(c):
    # like post 2: two bands, big phrase on top with handwritten note, second phrase below, round badge
    s = dots(c.get('bg', '#FFE1D2'), c.get('dot', '#F6A47A'), seed=c.get('seed', 5))
    s += f'<path d="M0 700 L{W} 640 L{W} {H} L0 {H} Z" fill="{c.get("bg2", "#F6C9B2")}" stroke="{INK}" stroke-width="7"/>'
    s += logo()
    s += hand(80, 300, c['note1'], 62) + T(70, 440, c['big1'], c.get('size1', 150))
    s += T(80, 530, c['ru1'], 50, wt=500, fill=MUTED)
    if c.get('wrong1'):
        x, y = c.get('wrong1_x', 520), c.get('wrong1_y', 530)
        s += T(x, y, c['wrong1'], 50, wt=700, fill=RED) + strike(x, y - 17, c.get('wrong1_w', 300), sw=6)
    s += hand(80, 870, c['note2'], 62) + T(70, 1010, c['big2'], c.get('size2', 150))
    s += T(80, 1100, c['ru2'], 50, wt=500, fill=MUTED)
    s += f'<g transform="rotate(8 860 730)"><circle cx="860" cy="730" r="170" fill="{YELLOW}" stroke="{INK}" stroke-width="7"/>'
    s += hand(860, 670, c['badge_note'], 46, fill=MUTED, anchor='middle') + lines(860, 740, c['badge'], 60, 66, anchor='middle') + '</g>'
    s += waves(1230, c.get('wave', '#E2683A'), 2)
    return s

def L_quiz(c):
    # question + two answer buttons; answer goes in the caption
    s = lattice(c.get('bg', '#B4EAF6'), c.get('line', '#7FCBE0')) + logo() + tag('Квиз', 800, 62, 210, fill=YELLOW, rot=-3)
    s += card(80, 250, 920, 360, rot=2)
    s += f'<g transform="rotate(2 540 430)">' + hand(140, 360, c['note'], 60) + lines(140, 470, c['q'], 92, 100) + '</g>'
    y = 700
    for letter, opt in zip('AB', c['options']):
        s += card(110, y, 860, 170, fill='#FFFFFF', rot=-1, r=36)
        s += f'<g transform="rotate(-1 540 {y + 85})"><circle cx="200" cy="{y + 85}" r="50" fill="{BLUE}" stroke="{INK}" stroke-width="6"/>'
        s += T(200, y + 104, letter, 56, fill='#FFFFFF', anchor='middle') + T(290, y + 108, opt, 70) + '</g>'
        y += 220
    s += hand(540, 1250, c['foot'], 60, fill=INK, anchor='middle')
    return s

def L_list(c):
    # night sky: title, crossed-out calque, three stacked phrase cards
    s = stars(c.get('bg', '#26306B'), '#FFE58A') + logo()
    s += f'<circle cx="930" cy="150" r="80" fill="{YELLOW}" stroke="{INK}" stroke-width="7"/><circle cx="970" cy="120" r="70" fill="{c.get("bg", "#26306B")}"/>'
    s += hand(80, 290, c['note'], 60, fill='#FFE58A') + lines(80, 380, c['title'], 74, 84, fill='#FFFFFF')
    yb = 380 + 84 * (len(c['title']) - 1) + 80
    s += T(80, yb, c['wrong'], 52, fill='#FF8A7A') + strike(80, yb - 17, c.get('wrong_w', 300), color='#FF8A7A', sw=6)
    s += T(80 + c.get('wrong_w', 300) + 40, yb, c['wrong_note'], 40, wt=500, fill='#D9DCF5')
    y = yb + 70; fills = ['#FFFAEE', '#FFE58A', '#B4EAF6']
    for i, (en, ru) in enumerate(c['items']):
        rot = [-2, 1.5, -1][i % 3]
        s += card(70, y, 940, 190, fill=fills[i % 3], rot=rot, r=36)
        s += f'<g transform="rotate({rot} 540 {y + 95})">' + T(120, y + 92, en, 72) + T(120, y + 152, ru, 42, wt=500, fill=MUTED) + '</g>'
        y += 225
    return s

LAYOUTS = {'swap': L_swap, 'versus': L_versus, 'pair': L_pair, 'quiz': L_quiz, 'list': L_list}

def collect_text(c):
    if isinstance(c, str): return c
    if isinstance(c, (list, tuple)): return ''.join(collect_text(x) for x in c)
    if isinstance(c, dict): return ''.join(collect_text(v) for v in c.values())
    return ''

def build(post):
    c = post['card']
    body = LAYOUTS[post['layout']](c)
    css = font_css(collect_text(c) + 'Kumi≠ABКвиз')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<title>{esc(post["slug"])}</title><style>{css}</style>{body}</svg>')

def main(week_path):
    week = json.load(open(week_path)); out = pathlib.Path(week_path).parent
    for p in week['posts']:
        (out / (p['slug'] + '.svg')).write_text(build(p))
        print('svg', p['slug'])

if __name__ == '__main__':
    main(sys.argv[1])
