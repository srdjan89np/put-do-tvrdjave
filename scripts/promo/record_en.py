"""ENGLESKA verzija promo klipa (za Google Play i YouTube). Snima kadrove u frames/.
Vitezom upravlja jednostavan automatski igrač: preskače šiljke, lavu i provalije,
a mačem zamahuje samo kad je neprijatelj na dometu. Sa `test` samo proverava (bez snimanja)."""
import base64, os, sys, json
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(HERE, 'frames'); os.makedirs(FR, exist_ok=True)
ONLY = sys.argv[1] if len(sys.argv) > 1 else None
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
src = open(os.path.join(ROOT, 'index.html')).read()
icon = base64.b64encode(open(os.path.join(ROOT, 'icon.png'), 'rb').read()).decode()

HOOK = r'''showTitle();
window.__S={hurts:0,swordKills:0,stompKills:0,shotKills:0,swings:0,hurtLog:[]};
hurt=function(){__S.hurts++;__S.hurtLog.push(lvl.name+' x='+Math.round(hero.x/T));};
die=function(){};
const _kill=killEnemy;killEnemy=function(e,st){__S.hurtLog.push('K '+e.type+(st?' stomp':hero.atk>0?' sword':' shot'));if(st)__S.stompKills++;else if(hero&&hero.atk>0)__S.swordKills++;else __S.shotKills++;return _kill(e,st);};
let aiOn=false,jumpHold=0,lastSwing=-99;
function aiStep(){
  const h=hero;if(!aiOn||!h||state!=='play')return;
  K.r=true;K.sp=false;
  const onG=h.ground;const fx=h.x+h.w;const feet=Math.floor((h.y+h.h+2)/T);
  let need=false,why='';
  // prepreke ispred: rupa, šiljci, lava, zid
  for(let d=4;d<=40;d+=4){const cx=Math.floor((fx+d)/T);
    if(!SOLID[tileAt(cx,feet)]&&tileAt(cx,feet)!==LAVA){let floor=-1;for(let cy=feet;cy<ROWS;cy++){const t=tileAt(cx,cy);if(SOLID[t]||t===SPIKE||t===LAVA){floor=t;break;}}if(d<=22&&(floor<0||floor===SPIKE||floor===LAVA)){need=true;why='pit'+d;}else if(d<=22&&floor>=0){for(let k=1;k<=6;k++){const cx2=cx+k;let f2=-1;for(let cy=feet;cy<ROWS;cy++){if(SOLID[tileAt(cx2,cy)]){f2=1;break;}}if(f2<0){need=true;why='droppit';break;}}}}
    for(let cy=feet-2;cy<=feet;cy++){const t=tileAt(cx,cy);if((t===SPIKE||t===LAVA)&&d<=36){need=true;why='spk'+d;}}
    for(let cy=feet-2;cy<feet;cy++){if(SOLID[tileAt(cx,cy)]&&d<=10){need=true;why='wall';}}}
  for(const s of lvl.saws){const dx=s.x-fx;if(dx>-10&&dx<70&&Math.abs(s.y-(h.y+h.h/2))<70)need=true;}
  // neprijatelji: mač kad je na dometu, inače preskoči ježa
  for(const e of lvl.enemies){if(e.dead||e.gone)continue;
    const dx=e.x-fx,vy=(e.y+e.h)>h.y-6&&e.y<h.y+h.h+10;
    if(dx>-6&&dx<20&&vy&&h.atkCool<=0&&tick-lastSwing>8){K.sp=true;lastSwing=tick;__S.swings++;__S.hurtLog.push('S '+e.type+' dx'+Math.round(dx)+' dy'+Math.round(e.y-h.y)+' g'+h.ground+' x'+(h.x/T).toFixed(1));}
    else if(e.type==='jez'&&dx>0&&dx<34&&vy&&h.atkCool>0&&h.atk<=0&&tick-lastSwing>16){need=true;why='jez';}}
  if(need&&onG&&jumpHold<=0){__S.hurtLog.push('J '+why+' x'+(h.x/T).toFixed(1)+' vx'+h.vx.toFixed(2));K.jp=true;K.j=true;jumpHold=15;}
  if(jumpHold>0){jumpHold--;if(jumpHold===0)K.j=false;}
}
window.__R={
  adv(n){for(let i=0;i<n;i++){aiStep();step();
      if(hero&&hero.y>H-40&&state==='play'){__S.hurts++;__S.hurtLog.push('pad '+lvl.name+' x'+(hero.x/T).toFixed(1));hero.y=-20;hero.vy=0;hero.x+=T*2;}}
    render();updHud();},
  pick(sel){choosePlayers(sel);},
  start(order){startGame({order});hideCard();state='play';},
  level(pi,lv,x){cur=pi;players[pi].level=lv;prepareTurn(pi,'level',pi);hideCard();state='play';hero.x=x*T+4;hero.vy=0;let gy=12;for(let cy=1;cy<ROWS;cy++){if(SOLID[lvl.g[cy][x]]&&!SOLID[lvl.g[cy-1][x]]){gy=cy;break;}}hero.y=gy*T-hero.h;hero.ground=true;},
  ai(on){aiOn=on;if(!on){K.r=false;K.j=false;K.sp=false;}},
  horse(){const p=P();p.horse=true;p.weapon=2;p.armor=true;const gy=hero.y+hero.h;setRide(true);hero.y=gy-hero.h;},
  ending(pi,t0,kind){cur=pi;startEnding(function(){},kind);endT=t0;hideCard();},
  diff(){chooseDifficulty([0]);},
  secret(){const L=lvl,h=hero;h.x=(L.secret-1)*T+6;let gy=12;h.y=gy*T-h.h;h.vy=0;h.face=1;h.inv=400;h.ground=true;},
  swing(){K.ap=true;},walk(on){K.r=on;},
  hideCard(){hideCard();},
  rz(z){window.__ZOOM=z;resize();},
  stats(){return __S;},hx(){return hero.x/T;},dbg(){const h=hero;const es=lvl.enemies.filter(e=>!e.dead&&!e.gone).map(e=>e.type+':'+Math.round(e.x-(h.x+h.w))+'/'+Math.round(e.y-h.y)+(e.active?'a':''));return Math.round(h.x/T*10)/10+' g'+h.ground+' atk'+h.atk+' cool'+h.atkCool+' '+es.filter(t=>Math.abs(parseInt(t.split(':')[1]))<200).join(',');},ev(f){return eval(f)},st(){return state+'/'+aiOn+'/'+lvl.name;}
};'''
zk='  scale=Math.min(aw/VW,ah/H);dpr=Math.min(2,window.devicePixelRatio||1);'
assert zk in src
src=src.replace(zk,zk+"if(window.__ZOOM){VW=window.__ZOOM*T;scale=aw/VW;}")
key = 'showTitle();dailyGift();\nrequestAnimationFrame(frame);'
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
<h1>Road to the King's Castle</h1><p>Vojin, Vukašin, Sanja and Srđan are waiting for you!</p><small>1–4 PLAYERS · 10 LEVELS · BLUETOOTH PLAY</small></div>'''

doc = ('<!doctype html><script>window.__ZOOM=19;localStorage.setItem("ptv-jezik",JSON.stringify("en"));localStorage.setItem("ptv-dan",JSON.stringify({d:"x",s:1}));</script><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
       '<style>html,body{margin:0}[hidden]{display:none!important}body{font-size:14px}</style></head><body>' + src + OVER + '</body></html>')

FPS = 30
frame = [0]

def shot(pg):
    if ONLY == 'test': frame[0] += 1; return
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

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1280, 'height': 720}, device_scale_factor=1)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('http://g.local/**', lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=doc))
    pg.goto('http://g.local/'); pg.wait_for_timeout(500)
    seg = {}
    def mark(name):
        s = pg.evaluate("()=>JSON.parse(JSON.stringify(__R.stats()))")
        seg[name] = {k: v for k, v in s.items() if k != 'hurtLog'}
        seg[name]['log'] = [h for h in s['hurtLog'] if not h.startswith('J')]

    # 1) naslovni ekran (3 s)
    run(pg, 90)
    # 2) prvi nivo: trčanje, skokovi, mač (6 s)
    pg.evaluate("()=>{__R.start([0,1,2,3]);__R.ai(true);}")
    run(pg, 180, caption='Help the <b>little knights</b> reach the castle!')
    mark('nivo1')
    # 3) izbor igrača (3 s)
    pg.evaluate("()=>{__R.ai(false);__R.pick([0,1,2,3]);}")
    run(pg, 90, caption='Play alone or with friends: <b>up to 4 players</b>', top=True)
    pg.evaluate("()=>__R.hideCard()")
    # 4) montaža nivoa (4 x 1.8 s)
    lv_caption = '<b>10 levels</b>: clouds, desert, snow, castles…'
    montage = [(1, 2, 76), (2, 3, 30), (3, 4, 24), (0, 5, 50)]
    pg.evaluate("()=>__R.start([0,1,2,3])")
    for k, (pi, lv, x) in enumerate(montage):
        pg.evaluate(f"()=>{{__R.level({pi},{lv},{x});__R.ai(true);}}")
        n = 54
        for i in range(n):
            pg.evaluate("()=>__R.adv(2)")
            t = k * n + i; tot = n * len(montage)
            cap(pg, lv_caption if i == 0 and k == 0 else None, max(0, min(1, t / 8, (tot - 1 - t) / 8)))
            shot(pg)
        mark(f'montaza{k}')
    cap(pg, '', 0)
    # 5) konj i super praćka (4 s)
    pg.evaluate("()=>{__R.level(1,0,100);__R.horse();__R.ai(true);}")
    run(pg, 120, caption='Sword, slingshot, armor and a <b>horse</b>!')
    mark('konj')
    # 6) težina (2.5 s)
    pg.evaluate("()=>{__R.ai(false);__R.diff();}")
    run(pg, 75, caption='From <b>Easy</b> with a shield to <b>Knightly</b>', top=True)
    pg.evaluate("()=>__R.hideCard()")
    # 7) tajna soba (3.5 s)
    pg.evaluate("()=>{__R.level(0,1,10);__R.ai(false);__R.secret();}")
    def sk(i):
        if i == 20: pg.evaluate("()=>__R.swing()")
        if i == 45: pg.evaluate("()=>__R.walk(true)")
        if i == 85: pg.evaluate("()=>__R.walk(false)")
    run(pg, 105, caption='Break cracked walls and find <b>secret rooms</b>', keyfn=sk)
    # 8) princeza (4 s)
    pg.evaluate("()=>{__R.walk(false);__R.rz(0);__R.ending(0,60,'princess');}")
    run(pg, 120, caption='Defeat the dragon and save the <b>princess</b>!')
    # 9) proglašenje za viteza i vatromet (6 s)
    pg.evaluate("()=>{__R.ending(2,90,'final');}")
    run(pg, 180, caption='The prince makes you a <b>true knight</b>!', top=True)
    # 7) završna kartica (2.5 s)
    pg.evaluate("()=>{document.getElementById('endc').style.display='flex';}")
    for i in range(75):
        pg.evaluate(f"()=>{{const e=document.getElementById('endc');e.style.opacity={min(1, i / 10)};e.querySelector('img').style.transform='scale({1 + 0.04 * min(1, i / 20)})';}}")
        shot(pg)
    print('frames', frame[0], 'errors', errs)
    print(json.dumps(seg, ensure_ascii=False))
    b.close()
