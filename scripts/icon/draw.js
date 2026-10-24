// Crta ikonicu igrice (Vojin sa mačem ispred Kraljeve tvrđave) pomoću crteža iz same igre.
// Koristi je scripts/make-icons.py.
const D=window.__D;const {drawHero,drawRiding,HEROES,rr,circ}=D;
const S=1024;
function base(g,top,bot){
  g.clearRect(0,0,S,S);g.save();g.beginPath();g.roundRect(0,0,S,S,230);g.clip();
  const gr=g.createLinearGradient(0,0,0,S);gr.addColorStop(0,top);gr.addColorStop(1,bot);g.fillStyle=gr;g.fillRect(0,0,S,S);
}
function sun(g,x,y,r){const gr=g.createRadialGradient(x,y,r*0.2,x,y,r*2.2);gr.addColorStop(0,'rgba(255,240,180,.9)');gr.addColorStop(1,'rgba(255,240,180,0)');g.fillStyle=gr;g.fillRect(0,0,S,S);g.fillStyle='#fff3c4';circ(g,x,y,r);}
function hills(g,y,col,amp,ph){g.fillStyle=col;g.beginPath();g.moveTo(0,S);for(let x=0;x<=S;x+=16)g.lineTo(x,y+Math.sin(x/170+ph)*amp);g.lineTo(S,S);g.fill();}
function castle(g,cx,by,w,col,colD,flag){
  const h=w*0.55;g.fillStyle=col;
  g.fillRect(cx-w/2,by-h,w,h);
  const mw=w/9;for(let i=0;i<9;i+=2)g.fillRect(cx-w/2+i*mw,by-h-mw*0.8,mw,mw*0.8);
  const tw=w*0.26,th=h*1.65;
  for(const tx of [cx-w/2-tw*0.35,cx+w/2-tw*0.65,cx-tw/2]){
    const hh=tx===cx-tw/2?th*1.25:th;
    g.fillStyle=col;g.fillRect(tx,by-hh,tw,hh);
    const m=tw/5;for(let i=0;i<5;i+=2)g.fillRect(tx+i*m,by-hh-m,m,m);
    g.fillStyle=colD;g.fillRect(tx+tw/2-1.5,by-hh-m-tw*0.55,3,tw*0.55);
    g.fillStyle=flag;g.beginPath();g.moveTo(tx+tw/2+1.5,by-hh-m-tw*0.55);g.lineTo(tx+tw/2+tw*0.45,by-hh-m-tw*0.43);g.lineTo(tx+tw/2+1.5,by-hh-m-tw*0.3);g.fill();
    g.fillStyle='#ffd75e';rr(g,tx+tw/2-tw*0.12,by-hh*0.7,tw*0.24,tw*0.36,tw*0.12);g.fill();
  }
  g.fillStyle=colD;g.beginPath();const gw=w*0.2;g.moveTo(cx-gw/2,by);g.lineTo(cx-gw/2,by-gw*0.8);g.arc(cx,by-gw*0.8,gw/2,Math.PI,0);g.lineTo(cx+gw/2,by);g.fill();
}
function road(g,x0,x1,yTop,cx){ // kaldrma koja se sužava prema kapiji
  g.fillStyle='#c9b79a';g.beginPath();g.moveTo(x0,S);g.lineTo(cx-18,yTop);g.lineTo(cx+18,yTop);g.lineTo(x1,S);g.fill();
  g.strokeStyle='#a8957a';g.lineWidth=5;
  for(let i=1;i<9;i++){const t=i/9,y=yTop+(S-yTop)*t*t;const l=cx-18+(x0-cx+18)*t*t,r=cx+18+(x1-cx-18)*t*t;g.beginPath();g.moveTo(l,y);g.lineTo(r,y);g.stroke();}
}
function hero(g,c,cx,feet,sc,opt={}){
  g.save();g.translate(cx,feet);g.scale(sc,sc);
  drawHero(g,c,-11,-31,opt.face||1,opt.walk||0,!!opt.air,false,opt.weapon||0,!!opt.armor,opt.swing==null?null:opt.swing);
  g.restore();
}
function shadow(g,x,y,w){g.fillStyle='rgba(40,20,40,.25)';g.beginPath();g.ellipse(x,y,w,w*0.18,0,0,Math.PI*2);g.fill();}
function frame(g){g.restore();g.save();g.beginPath();g.roundRect(6,6,S-12,S-12,226);g.lineWidth=12;g.strokeStyle='rgba(255,255,255,.18)';g.stroke();g.restore();}

const icons={
  // Vojin izbliza, sa podignutim mačem, ispred tvrđave
 vitez(g){base(g,'#ffcf8a','#f39a8c');sun(g,760,250,90);
   castle(g,512,640,420,'#a98bc4','#7d61a0','#ff7ab8');
   hills(g,640,'#8fcf6a',18,0.5);hills(g,720,'#6fb456',14,2);
   road(g,330,700,640,512);
   shadow(g,500,930,170);
   hero(g,HEROES[0],500,935,17,{swing:0.55});
   frame(g);},
};
window.renderIcon=function(k,size){const c=document.createElement('canvas');c.width=c.height=S;const g=c.getContext('2d');icons[k](g);
  if(size&&size!==S){const o=document.createElement('canvas');o.width=o.height=size;const og=o.getContext('2d');og.imageSmoothingQuality='high';og.drawImage(c,0,0,size,size);return o.toDataURL('image/png');}
  return c.toDataURL('image/png');};
