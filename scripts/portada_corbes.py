#!/usr/bin/env python3
"""Genera les corbes de nivell de la portada a partir del relleu de mapes/pirineu3d.html.

Ús:  python3 scripts/portada_corbes.py     (cal numpy, scipy i contourpy)
Escriu el bloc SVG entre <!-- CORBES:INICI --> i <!-- CORBES:FI --> d'index.html.
No cal tornar-lo a executar si no canvia el relleu o el disseny de la portada.
"""
import base64, json, os, re
import numpy as np
from scipy.ndimage import gaussian_filter, zoom
from contourpy import contour_generator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VW, VH = 1600, 900          # viewBox de la portada
EQUI, MESTRA = 100, 500     # equidistància i corbes mestres (m)
ROW0 = 0.255                # on comença el retall: evita el forat del NE i la franja del sud del relleu
MAX_CIMS, DIST_CIMS = 6, 130  # cims etiquetats i separació mínima entre ells (px)

src = open(os.path.join(ROOT, 'mapes/pirineu3d.html'), encoding='utf8').read()
i, j = src.index('const META'), src.index('const HEIGHTS_B64')
meta = json.loads(re.search(r'const META\s*=\s*(\{.*\})\s*;', src[i:j], re.S).group(1))
a = src.index('"', j) + 1
GW, GH = meta['grid']
h = np.frombuffer(base64.b64decode(src[a:src.index('"', a)]), dtype='<u2').reshape(GH, GW).astype(float)

rows = int(round(GW * VH / VW))            # retall 16:9 a tota l'amplada
r0 = int(ROW0 * GH)
hc = gaussian_filter(h[r0:r0 + rows], 1.6)
sx, sy = VW / (GW - 1), VH / (rows - 1)
x0, y0, x1, y1 = meta['extent']
km_px = (x1 - x0) / 1000 / VW

def simplify(p, tol):
    """Douglas-Peucker iteratiu."""
    keep = np.zeros(len(p), bool); keep[[0, -1]] = True
    stack = [(0, len(p) - 1)]
    while stack:
        s, e = stack.pop()
        if e <= s + 1: continue
        d = p[e] - p[s]; n = np.hypot(*d)
        seg = p[s + 1:e] - p[s]
        dist = np.abs(seg[:, 0] * d[1] - seg[:, 1] * d[0]) / n if n else np.hypot(seg[:, 0], seg[:, 1])
        k = int(dist.argmax())
        if dist[k] > tol:
            keep[s + 1 + k] = True; stack += [(s, s + 1 + k), (s + 1 + k, e)]
    return p[keep]

def path(lines):
    out = []
    for ln in lines:
        p = ln * [sx, sy]
        if len(p) < 6: continue
        if np.ptp(p[:, 0]) + np.ptp(p[:, 1]) < 14: continue   # treu illots minúsculs
        p = simplify(p, 0.9)
        out.append('M' + 'L'.join(f'{x:.1f} {y:.1f}'.replace('.0 ', ' ').rstrip('0').rstrip('.') for x, y in p))
    return ''.join(out)

cg = contour_generator(z=hc)
lo = int(np.ceil(hc.min() / EQUI) * EQUI)
fines, mestres, labels = [], [], []
for lev in range(lo, int(hc.max()), EQUI):
    lines = cg.lines(lev)
    d = path(lines)
    if not d: continue
    if lev % MESTRA == 0:
        mestres.append(f'<path class="cm" style="--i:{(lev-lo)//EQUI}" d="{d}"/>')
        big = max(lines, key=len) * [sx, sy]          # una etiqueta per corba mestra, a la meitat dreta
        cand = big[(big[:, 0] > VW * .5) & (big[:, 0] < VW * .96) & (big[:, 1] > 60) & (big[:, 1] < VH - 90)]
        if len(cand):
            x, y = cand[len(cand) // 2]
            labels.append(f'<text class="cl" x="{x:.0f}" y="{y:.0f}">{lev:,}</text>'.replace(',', ' '))
    else:
        fines.append(f'<path class="cf" style="--i:{(lev-lo)//EQUI}" d="{d}"/>')

cims, pos = [], []
for pk in sorted(meta['peaks'], key=lambda p: -p['a']):
    x, y = pk['u'] * VW, (pk['v'] * (GH - 1) - r0) * sy
    if pk['t'] != 'cim' or not (VW * .52 < x < VW - 40 and 50 < y < VH - 120): continue
    if any(np.hypot(x - px, y - py) < DIST_CIMS for px, py in pos) or len(pos) >= MAX_CIMS: continue
    pos.append((x, y))
    left = x > VW - 220
    tx, anc = (x - 12, 'end') if left else (x + 12, 'start')
    cims.append(f'<g class="cim"><path d="M{x-6:.0f} {y+5:.0f}L{x:.0f} {y-6:.0f}L{x+6:.0f} {y+5:.0f}Z"/>'
                f'<text x="{tx:.0f}" y="{y-1:.0f}" text-anchor="{anc}">{pk["n"]}</text>'
                f'<text class="alt" x="{tx:.0f}" y="{y+11:.0f}" text-anchor="{anc}">{pk["a"]:,} m</text></g>'.replace(',', '\u2009'))
labels = [l for l in labels if all(np.hypot(float(re.search(r'x="(\d+)"', l).group(1)) - px,
                                            float(re.search(r'y="(\d+)"', l).group(1)) - py) > 90 for px, py in pos)]

# graella petita d'altituds per a la lectura de cota sota el cursor (1 byte = 10 m)
g = zoom(hc, (72 / hc.shape[0], 128 / hc.shape[1]), order=1)
grid = base64.b64encode(np.clip(np.round(g / 10), 0, 255).astype('u1').tobytes()).decode()

svg = (f'<svg class="hero-art" viewBox="0 0 {VW} {VH}" preserveAspectRatio="xMidYMid slice" aria-hidden="true" '
       f'data-grid="{grid}" data-gw="128" data-gh="72" data-kmpx="{km_px:.5f}">\n'
       + '\n'.join(fines) + '\n' + '\n'.join(mestres) + '\n' + '\n'.join(labels) + '\n' + '\n'.join(cims) + '\n</svg>')

f = os.path.join(ROOT, 'index.html')
page = open(f, encoding='utf8').read()
a, b = page.index('<!-- CORBES:INICI -->'), page.index('<!-- CORBES:FI -->')
open(f, 'w', encoding='utf8').write(page[:a] + '<!-- CORBES:INICI -->\n' + svg + '\n' + page[b:])
print(f'{len(fines)} corbes, {len(mestres)} mestres, {len(cims)} cims, {len(svg)/1024:.0f} KB, {km_px*1000:.1f} m/px, retall {rows*75/1000:.1f} km N-S')
