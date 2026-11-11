"""Render post cards for a week.
Usage: python3 render.py week.json OUT_DIR
week.json: {"week":"2026-W47","posts":[{"slug","hook","bad","good","ru","ex","exru","why","pattern_bg","pattern_line","caption","threads_text","publish_at"}]}
"""
import json, sys, os, subprocess, pathlib
HERE = pathlib.Path(__file__).parent
PALETTE = [("#9FD3CF", "#3A6FD0"), ("#F6D35B", "#7FA7F0"), ("#F7C6B0", "#EE8A52"), ("#D9C8F2", "#C77DD8"), ("#BFE3B4", "#2F7D4F")]

def waves(c):
    c = c.replace('#', '%23')
    return ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='28'%3E"
            f"%3Cpath d='M0 14 Q15 2 30 14 T60 14' fill='none' stroke='{c}' stroke-width='5'/%3E%3C/svg%3E\")")

def main(week_path, out):
    week = json.load(open(week_path)); os.makedirs(out, exist_ok=True)
    tpl = (HERE / 'templates/card.html').read_text()
    names = []
    for i, p in enumerate(week['posts']):
        col, pat = PALETTE[i % len(PALETTE)]
        h = tpl
        for k in ('hook', 'bad', 'good', 'ru', 'ex', 'exru', 'why'):
            h = h.replace('{{%s}}' % k, p[k])
        h = h.replace('FONTS_CSS', (HERE / 'fonts.css').resolve().as_uri())
        h = h.replace('{{col}}', col).replace('{{waves}}', waves(pat))
        h = h.replace('{{gsize}}', '92' if len(p['good']) <= 12 else ('80' if len(p['good']) <= 16 else '68'))
        f = os.path.join(out, p['slug'] + '.html'); open(f, 'w').write(h); names.append(p['slug'])
    subprocess.run(['node', str(HERE / 'shot.js'), out, *names], check=True)
    print('rendered', len(names))

if __name__ == '__main__':
    main(*sys.argv[1:3])
