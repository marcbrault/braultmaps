#!/usr/bin/env python3
"""Comprovació de la web sense model: enllaços interns, sitemap, duplicats i pes.

Ús:  python3 scripts/check.py        (des de l'arrel del repo)
Surt amb codi 1 si troba enllaços trencats, pàgines fora del sitemap o duplicats.
"""
import hashlib, os, re, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SKIP_DIRS = {'.git', 'scripts', '.agents'}
DUP_OK = ('repositori/vic3d/creixement/',)  # dècades sense edificis nous: fotogrames idèntics
NO_SITEMAP = {'404.html', 'mapes/BraultMaps_Index_de_Gini.html'}  # error i iframe

files = []
for d, dirs, fs in os.walk('.'):
    dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
    files += [os.path.join(d, f)[2:] for f in fs]
pages = sorted(f for f in files if f.endswith('.html'))
problems = 0

# 1. Enllaços i recursos interns
for f in pages:
    s = open(f, encoding='utf8', errors='ignore').read()
    for m in set(re.findall(r'(?:href|src)=["\']([^"\'#?]+)', s)):
        if re.match(r'(https?:|mailto:|tel:|data:|javascript:|//)', m) or '${' in m or '+' in m:
            continue
        p = m[1:] if m.startswith('/') else os.path.normpath(os.path.join(os.path.dirname(f), m))
        if p in ('', '.'):
            p = 'index.html'
        if os.path.isdir(p):
            if m.endswith('/') and not os.path.exists(os.path.join(p, 'index.html')):
                continue  # prefix de ruta dins de JavaScript ('carpeta/' + nom)
            p = os.path.join(p, 'index.html')
        if not os.path.exists(p):
            print(f'ENLLAÇ TRENCAT  {f} -> {m}'); problems += 1

# 2. Sitemap
sm = open('sitemap.xml', encoding='utf8').read() if os.path.exists('sitemap.xml') else ''
locs = set(re.findall(r'<loc>https://braultmaps\.com/(.*?)</loc>', sm))
for f in pages:
    if f in NO_SITEMAP or f == 'index.html':
        continue
    if f not in locs:
        print(f'FORA DEL SITEMAP  {f}'); problems += 1
for l in locs:
    if l and not os.path.exists(l):
        print(f'SITEMAP APUNTA A RES  {l}'); problems += 1

# 3. Duplicats exactes
h = defaultdict(list)
for f in files:
    if f.startswith(DUP_OK):
        continue
    h[hashlib.md5(open(f, 'rb').read()).hexdigest()].append(f)
for v in h.values():
    if len(v) > 1:
        print(f'DUPLICAT  {" = ".join(v)}'); problems += 1

# 4. Pes
total = sum(os.path.getsize(f) for f in files)
print(f'\n{len(files)} fitxers · {len(pages)} pàgines · {total/1e6:.1f} MB')
for f in sorted(files, key=os.path.getsize, reverse=True)[:3]:
    print(f'  {os.path.getsize(f)/1e6:.2f} MB  {f}')
print('TOT CORRECTE' if not problems else f'{problems} PROBLEMES')
sys.exit(1 if problems else 0)
