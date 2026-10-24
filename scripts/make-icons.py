"""Crta ikonicu igrice i snima je u sve potrebne veličine.

Ikonica se crta crtežima iz same igre (index.html), u pregledaču (Playwright + Chromium):
Vojin sa podignutim mačem ispred Kraljeve tvrđave. Crtež je u scripts/icon/draw.js.

Pokretanje iz korena repozitorijuma:  python3 scripts/make-icons.py
"""
import base64, io, os
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def render_master():
    src = open(os.path.join(ROOT, 'index.html')).read()
    key = 'showTitle();\nrequestAnimationFrame(frame);'
    assert key in src, 'index.html se promenio: nema početka igre'
    src = src.replace(key, 'window.__D={drawHero,drawRiding,HEROES,rr,circ};')
    doc = '<!doctype html><html><head><meta charset="utf-8"></head><body>' + src + '</body></html>'
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.route('http://g.local/**', lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=doc))
        pg.goto('http://g.local/')
        pg.add_script_tag(path=os.path.join(HERE, 'icon', 'draw.js'))
        data = pg.evaluate("()=>renderIcon('vitez',1024)")
        b.close()
    return Image.open(io.BytesIO(base64.b64decode(data.split(',')[1]))).convert('RGBA')


def main():
    icon = render_master()
    os.chdir(ROOT)
    os.makedirs('docs', exist_ok=True)
    icon.resize((512, 512), Image.LANCZOS).save('icon.png')
    icon.resize((512, 512), Image.LANCZOS).save('docs/icon-512.png')
    sizes = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
    for name, size in sizes.items():
        folder = f'android/app/src/main/res/mipmap-{name}'
        os.makedirs(folder, exist_ok=True)
        icon.resize((size, size), Image.LANCZOS).save(f'{folder}/ic_launcher.png')
    print('Ikonice su napravljene.')


if __name__ == '__main__':
    main()
