"""Snima promo klip igre kadar po kadar (30 fps) u folder frames/."""
import base64, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(HERE, 'frames')
os.makedirs(FR, exist_ok=True)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
src = open(os.path.join(ROOT, 'index.html')).read()
icon = base64.b64encode(open(os.path.join(ROOT, 'icon.png'), 'rb').read()).decode()

HOOK = r'''showTitle();
window.__R={
  adv(n){for(let i=0;i<n;i++){step();
      if(hero&&hero.y>H-40&&state==='play'){hero.y=-20;hero.vy=0;hero.x+=T*2;}
    }
    render();updHud();},
  title(){showTitle();},
  pick(sel){choosePlayers(sel);},
  start(order){startGame({order});hideCard();state='play';die=function(){};hurt=function(){};},
  level(pi,lv,x){cur=pi;players[pi].level=lv;prepareTurn(pi,'level',pi);hideCard();state='play';hero.x=x*T;hero.y=0;hero.vy=0;},
  keys(o){Object.assign(K,o);},
  get hero(){return hero},get P(){return P()},
  horse(){const p=P();p.horse=true;p.weapon=2;p.armor=true;setRide(true);},
  ending(pi,t0){cur=pi;startEnding(function(){});endT=t0;hideCard();},
  hideCard(){hideCard();},
  rz(z){window.__ZOOM=z;resize();}
};'''
zk='  scale=Math.min(aw/VW,ah/H);dpr=Math.min(2,window.devicePixelRatio||1);'
assert zk in src
src=src.replace(zk,zk+"if(window.__ZOOM){VW=window.__ZOOM*T;scale=aw/VW;}")
key = 'showTitle();\nrequestAnimationFrame(frame);'
assert key in src
src = src.replace(key, HOOK)

OVER = '''<style>
#stage{overflow:hidden}#c{position:absolute;left:0;bottom:0}
#cap.top{bottom:auto;top:96px}
#cap{position:fixed;left:50%;bottom:34px;transform:translateX(-50%);z-index:50;max-width:86%;text-align:center;
 font:700 34px/1.25 "DejaVu Sans",sans-serif;color:#fff;background:rgba(19,24,51,.88);border:3px solid #ffc62b;border-radius:18px;
 padding:14px 28px;box-shadow:0 10px 30px rgba(0,0,0,.35);opacity:0;white-space:nowrap}
#cap b{color:#ffc62b}
#endc{position:fixed;inset:0;z-index:60;display:none;flex-direction:column;align-items:center;justify-content:center;gap:18px;
 background:radial-gradient(circle at 50% 40%,#283163,#131833 70%);color:#fff;font-family:"DejaVu Sans",sans-serif;text-align:center}
#endc img{width:180px;height:180px;border-radius:40px;box-shadow:0 12px 40px rgba(0,0,0,.5)}
#endc h1{margin:0;font:700 64px/1.1 "DejaVu Sans",sans-serif;color:#ffc62b;text-shadow:0 4px 0 #b58300}
#endc p{margin:0;font:700 30px/1.3 "DejaVu Sans",sans-serif;color:#f5f2ff}
#endc small{font:700 22px "DejaVu Sans",sans-serif;color:#a7aedb;letter-spacing:2px}
</style>
<div id="cap"></div>
<div id="endc"><img src="data:image/png;base64,''' + icon + '''" alt="">
<h1>Пут до Краљеве тврђаве</h1><p>Војин, Вукашин, Сања и Срђан те чекају!</p><small>ИГРАЈ НА ТЕЛЕФОНУ И РАЧУНАРУ</small></div>'''

doc = ('<!doctype html><script>window.__ZOOM=19</script><html lang="sr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
       '<style>html,body{margin:0}[hidden]{display:none!important}body{font-size:14px}</style></head><body>' + src + OVER + '</body></html>')

FPS = 30
frame = [0]

def shot(pg):
    pg.screenshot(path=os.path.join(FR, f'f{frame[0]:05d}.jpg'), type='jpeg', quality=92)
    frame[0] += 1

def cap(pg, html, a, top=False):
    pg.evaluate("([h,a,t])=>{const c=document.getElementById('cap');if(h!==null)c.innerHTML=h;c.style.opacity=a;c.classList.toggle('top',t);}", [html, a, top])

def run(pg, n, steps=2, caption=None, keyfn=None, fade=8, top=False):
    """n kadrova; caption se pojavi i nestane postepeno."""
    for i in range(n):
        if keyfn: keyfn(i)
        pg.evaluate(f"()=>__R.adv({steps})")
        if caption is not None:
            a = min(1, i / fade, (n - 1 - i) / fade)
            cap(pg, caption if i == 0 else None, max(0, a), top)
        shot(pg)
    cap(pg, '', 0)

def runner(jump_every=46, hit_every=None, offset=0):
    def k(i):
        st = {'r': True}
        j = (i + offset) % jump_every
        if j == 0: st.update({'jp': True, 'j': True})
        if j == 14: st['j'] = False
        if hit_every and (i + offset) % hit_every == 7: st['sp'] = True
        return st
    return k

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1280, 'height': 720}, device_scale_factor=1)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('http://g.local/**', lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=doc))
    pg.goto('http://g.local/'); pg.wait_for_timeout(500)

    def keys(fn):
        return lambda i: pg.evaluate("(o)=>__R.keys(o)", {**{'r': False, 'j': False, 'jp': False, 'sp': False}, **fn(i)})

    # 1) naslovni ekran (3 s)
    run(pg, 90)
    # 2) prvi nivo: trčanje, skokovi, mač (6 s)
    pg.evaluate("()=>__R.start([0,1,2,3])")
    run(pg, 180, caption='Помози <b>малим витезовима</b> да стигну до тврђаве!', keyfn=keys(runner(46, 34)))
    # 3) izbor igrača (3 s)
    pg.evaluate("()=>{__R.keys({r:false,j:false});__R.pick([0,1,2,3]);}")
    run(pg, 90, caption='Играј сам или са друштвом: <b>до 4 играча</b>', top=True)
    pg.evaluate("()=>__R.hideCard()")
    # 4) montaža nivoa (4 x 1.8 s)
    lv_caption = '<b>10 нивоа</b>: облаци, пустиња, снег, тврђаве…'
    montage = [(1, 2, 76), (2, 3, 27), (3, 4, 24), (0, 5, 50)]
    pg.evaluate("()=>__R.start([0,1,2,3])")
    for k, (pi, lv, x) in enumerate(montage):
        pg.evaluate(f"()=>__R.level({pi},{lv},{x})")
        n = 54
        for i in range(n):
            keys(runner(40, 30, offset=k * 7))(i)
            pg.evaluate("()=>__R.adv(2)")
            t = k * n + i; tot = n * len(montage)
            cap(pg, lv_caption if i == 0 and k == 0 else None, max(0, min(1, t / 8, (tot - 1 - t) / 8)))
            shot(pg)
    cap(pg, '', 0)
    # 5) konj i super praćka (4 s)
    pg.evaluate("()=>{__R.level(1,0,66);__R.horse();}")
    run(pg, 120, caption='Мач, праћка, оклоп и <b>коњ</b>!', keyfn=keys(runner(44, 18)))
    # 6) završna scena (4 s)
    pg.evaluate("()=>{__R.keys({r:false,j:false,sp:false});__R.rz(0);__R.ending(2,150);}")
    run(pg, 120)
    # 7) završna kartica (2.5 s)
    pg.evaluate("()=>{document.getElementById('endc').style.display='flex';}")
    for i in range(75):
        pg.evaluate(f"()=>{{const e=document.getElementById('endc');e.style.opacity={min(1, i / 10)};e.querySelector('img').style.transform='scale({1 + 0.04 * min(1, i / 20)})';}}")
        shot(pg)
    print('frames', frame[0], 'errors', errs)
    b.close()
