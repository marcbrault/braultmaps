#!/usr/bin/env python3
"""Genera les miniatures de les targetes a partir d'una captura real de cada eina.

Ús:  python3 scripts/miniatures.py            (cal playwright i Pillow; serveix el repo en local)
Escriu img/mini/<nom>.webp. Torna'l a executar quan canviï l'aspecte d'una eina
o quan n'afegeixis una (afegeix-la a MINIS).
"""
import functools, http.server, io, os, threading
from PIL import Image, ImageOps
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'img', 'mini')
PORT = 8799
# nom: (pàgina, selector de l'element a capturar o None per al més gran, proporció, espera en ms, JS previ)
MINIS = {
    'comarques':         ('recursos/comarques.html', None, 4/3, 1500, "document.getElementById('btn-start').click()"),
    'municipis':         ('recursos/municipis.html', '#selmap', 4/3, 2500, "document.querySelectorAll('.sel-hint').forEach(e=>e.style.display='none')"),
    'projeccions':       ('recursos/projeccions.html', None, 4/3, 2500, None),
    'fronteres':         ('recursos/fronteres.html', None, 4/3, 2000, None),
    'catalunya-fisica':  ('recursos/catalunya-fisica.html', None, 4/3, 2000, None),
    'poblacio':          ('recursos/poblacio.html', None, 4/3, 2500, None),
    'cims100':           ('recursos/cims100.html', None, 4/3, 2500, None),
    'vic':               ('repositori/vic.html', '#stage', 4/3, 1500,
                          "document.getElementById('t').value=48;document.getElementById('t').dispatchEvent(new Event('input'));document.getElementById('year').style.display='none'"),
    'pirineu3d':         ('mapes/pirineu3d.html', 'canvas', 16/9, 7000,
                          "document.querySelectorAll('body *').forEach(e=>{if(e.tagName!=='CANVAS'&&!e.querySelector('canvas')&&e.tagName!=='SCRIPT')e.style.visibility='hidden'})"),
    'llemena3d':         ('projectes/llemena3d/visor.html', '#scene', 16/9, 8000,
                          "document.querySelectorAll('.panel,.probe,.back,.loading,.toggle').forEach(e=>e.style.display='none')"),
}
CLARS = {'comarques', 'municipis'}   # mapes de línia fina sobre fosc: se'n puja el contrast
BIGGEST = """() => { let best=null, a=0;
  for (const e of document.querySelectorAll('main svg, main canvas, canvas, svg')) {
    const r=e.getBoundingClientRect(); if (r.width<300||r.height<200) continue;
    if (r.width*r.height>a) { a=r.width*r.height; best=e; } }
  if (!best) return false; best.setAttribute('data-mini','1'); return true; }"""

def main():
    os.makedirs(OUT, exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for name, (page, sel, ratio, wait, js) in MINIS.items():
            pg = b.new_page(viewport={'width': 1280, 'height': 900})
            pg.goto(f'http://127.0.0.1:{PORT}/{page}', wait_until='domcontentloaded', timeout=60000)
            pg.wait_for_timeout(wait)
            if js: pg.evaluate(js); pg.wait_for_timeout(600)
            if sel is None:
                if not pg.evaluate(BIGGEST): print('SENSE ELEMENT', name); continue
                sel = '[data-mini]'
            im = Image.open(io.BytesIO(pg.locator(sel).first.screenshot())).convert('RGB')
            w, h = im.size                                   # retall centrat a la proporció de la targeta
            if w / h > ratio: nw = int(h * ratio); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
            else: nh = int(w / ratio); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
            im = im.resize((640, round(640 / ratio)), Image.LANCZOS)
            if name in CLARS:                                # línia clara sobre el fons del lloc
                g = ImageOps.autocontrast(im.convert('L'), cutoff=(40, 0.5))
                im = ImageOps.colorize(g, '#1a1918', '#d8d4cc')
            out = os.path.join(OUT, name + '.webp'); im.save(out, 'WEBP', quality=80, method=6)
            print(f'{name}: {os.path.getsize(out)//1024} KB'); pg.close()
    srv.shutdown()

if __name__ == '__main__':
    main()
