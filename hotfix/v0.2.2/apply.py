from pathlib import Path

ROOT=Path('.')
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def write(p,s): (ROOT/p).write_text(s,encoding='utf-8')
def one(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'PATCH_FAIL {label}: expected 1 anchor, found {n}')
    return s.replace(old,new,1)

p='app/build.gradle'; s=read(p)
s=one(s,'versionCode 6','versionCode 7','versionCode')
s=one(s,"versionName '0.2.1'","versionName '0.2.2'",'versionName')
write(p,s)

p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
if '0.2.1' not in s: raise SystemExit('PATCH_FAIL MainActivity version anchor missing')
s=s.replace('0.2.1','0.2.2')
write(p,s)

p='app/src/main/assets/www/app.js'; s=read(p)
s=one(s,
'''  let toastTimer=0;\n  let locked=false;\n''',
'''  let toastTimer=0;\n  let locked=false;\n  let monthAnimating=false;\n  let suppressDayClickUntil=0;\n''','month-animation-state')

anchor='''  function entryMarker(type){return({vacation:'U',overtime:'+',swap:'Z',sick:'L4',training:'S'})[type]||'';}\n  function cap(s){return s.charAt(0).toUpperCase()+s.slice(1);}\n\n'''
insert='''  function entryMarker(type){return({vacation:'U',overtime:'+',swap:'Z',sick:'L4',training:'S'})[type]||'';}\n  function cap(s){return s.charAt(0).toUpperCase()+s.slice(1);}\n\n  function shiftedMonth(base,delta){return new Date(base.getFullYear(),base.getMonth()+delta,1);}\n  function enterMonthAnimated(delta){\n    const card=document.querySelector('.calendar-card');\n    if(!card){monthAnimating=false;return;}\n    const start=delta>0?'100%':'-100%';\n    card.style.transition='none';\n    card.style.transform=`translate3d(${start},0,0)`;\n    card.style.opacity='.68';\n    requestAnimationFrame(()=>requestAnimationFrame(()=>{\n      card.style.transition='transform 220ms cubic-bezier(.22,.61,.36,1), opacity 180ms ease-out';\n      card.style.transform='translate3d(0,0,0)';\n      card.style.opacity='1';\n      setTimeout(()=>{card.style.transition='';card.style.transform='';card.style.opacity='';monthAnimating=false;},230);\n    }));\n  }\n  function changeMonthAnimated(delta,fromPx=null){\n    if(!delta||monthAnimating)return;\n    const card=document.querySelector('.calendar-card');\n    if(!card){currentMonth=shiftedMonth(currentMonth,delta);render();return;}\n    monthAnimating=true;\n    const width=Math.max(1,card.getBoundingClientRect().width||window.innerWidth);\n    const exit=delta>0?-width:width;\n    if(fromPx!==null)card.style.transform=`translate3d(${fromPx}px,0,0)`;\n    card.style.transition='transform 190ms cubic-bezier(.4,0,.2,1), opacity 170ms ease-out';\n    requestAnimationFrame(()=>{card.style.transform=`translate3d(${exit}px,0,0)`;card.style.opacity='.62';});\n    setTimeout(()=>{currentMonth=shiftedMonth(currentMonth,delta);render();enterMonthAnimated(delta);},195);\n  }\n  function bindMonthSwipe(){\n    const grid=document.querySelector('.calendar-grid');\n    const card=document.querySelector('.calendar-card');\n    if(!grid||!card)return;\n    let pointerId=null,startX=0,startY=0,dx=0,dragging=false,rejected=false;\n    grid.addEventListener('pointerdown',e=>{\n      if(monthAnimating||(e.pointerType==='mouse'&&e.button!==0))return;\n      pointerId=e.pointerId;startX=e.clientX;startY=e.clientY;dx=0;dragging=false;rejected=false;\n      card.style.transition='none';\n    });\n    grid.addEventListener('pointermove',e=>{\n      if(e.pointerId!==pointerId||rejected||monthAnimating)return;\n      const mx=e.clientX-startX,my=e.clientY-startY;\n      if(!dragging){\n        if(Math.abs(mx)<7&&Math.abs(my)<7)return;\n        if(Math.abs(my)>Math.abs(mx)){rejected=true;card.style.transform='';card.style.opacity='';return;}\n        dragging=true;suppressDayClickUntil=Date.now()+500;\n        try{grid.setPointerCapture(pointerId);}catch{}\n      }\n      e.preventDefault();\n      const width=Math.max(1,card.getBoundingClientRect().width||window.innerWidth);\n      dx=Math.max(-width*.92,Math.min(width*.92,mx));\n      card.style.transform=`translate3d(${dx}px,0,0)`;\n      card.style.opacity=String(1-Math.min(Math.abs(dx)/width,1)*.20);\n    });\n    const finish=e=>{\n      if(e.pointerId!==pointerId)return;\n      if(dragging&&!monthAnimating){\n        suppressDayClickUntil=Date.now()+500;\n        const width=Math.max(1,card.getBoundingClientRect().width||window.innerWidth);\n        const threshold=Math.min(72,width*.18);\n        if(Math.abs(dx)>=threshold){changeMonthAnimated(dx<0?1:-1,dx);}\n        else{\n          card.style.transition='transform 170ms cubic-bezier(.22,.61,.36,1), opacity 150ms ease-out';\n          card.style.transform='translate3d(0,0,0)';card.style.opacity='1';\n          setTimeout(()=>{card.style.transition='';card.style.transform='';card.style.opacity='';},180);\n        }\n      }\n      pointerId=null;dragging=false;rejected=false;dx=0;\n    };\n    grid.addEventListener('pointerup',finish);\n    grid.addEventListener('pointercancel',finish);\n  }\n\n'''
s=one(s,anchor,insert,'month-animation-functions')

s=one(s,
"    document.querySelectorAll('[data-month]').forEach(b=>b.onclick=()=>{currentMonth=new Date(currentMonth.getFullYear(),currentMonth.getMonth()+Number(b.dataset.month),1);render();});\n",
"    document.querySelectorAll('[data-month]').forEach(b=>b.onclick=()=>changeMonthAnimated(Number(b.dataset.month)));\n",'month-arrows')
s=one(s,
"    document.querySelectorAll('[data-date]').forEach(b=>b.onclick=()=>{const d=dateFromKey(b.dataset.date);if(b.dataset.current!=='1'){currentMonth=new Date(d.getFullYear(),d.getMonth(),1);render();return;}openDay(d);});\n",
"    document.querySelectorAll('[data-date]').forEach(b=>b.onclick=e=>{if(Date.now()<suppressDayClickUntil){e.preventDefault();return;}const d=dateFromKey(b.dataset.date);if(b.dataset.current!=='1'){changeMonthAnimated(d<currentMonth?-1:1);return;}openDay(d);});\n",'day-click-suppress')
old="""    const grid=document.querySelector('.calendar-grid');\n    if(grid){let x=0;grid.addEventListener('touchstart',e=>{x=e.touches[0].clientX},{passive:true});grid.addEventListener('touchend',e=>{const dx=e.changedTouches[0].clientX-x;if(Math.abs(dx)>65){currentMonth=new Date(currentMonth.getFullYear(),currentMonth.getMonth()+(dx<0?1:-1),1);render();}},{passive:true});}\n"""
s=one(s,old,"    bindMonthSwipe();\n",'swipe-handler')
s=one(s,'Kalendarz zmian · v0.2.1','Kalendarz zmian · v0.2.2','drawer-version')
write(p,s)

p='app/src/main/assets/www/styles.css'; s=read(p)
marker='/* v0.2.2 swipe + tighter chrome */'
if marker in s: raise SystemExit('PATCH_FAIL v0.2.2 CSS already present')
s += r'''

/* v0.2.2 swipe + tighter chrome */
.appbar{
  height:64px;
  grid-template-columns:40px 1fr 52px;
  padding:0 8px;
  box-shadow:0 1px 3px rgba(0,0,0,.11);
}
.appbar-icon{width:34px;height:34px;padding:8px}
.appbar-copy{padding-left:2px}
.appbar-title{font-size:18px;line-height:1;font-weight:700}
.appbar-subtitle{font-size:10.8px;line-height:1.05;margin-top:2px;opacity:.80}
.today-action{height:34px;font-size:11px;line-height:1;font-weight:700;letter-spacing:.02em}
.calendar-main{min-height:calc(100vh - 64px);overflow:hidden}
.calendar-card{will-change:transform;backface-visibility:hidden;transform:translateZ(0)}
.month-head{height:42px;grid-template-columns:36px 1fr 36px}
.month-label{font-size:18px;font-weight:500;letter-spacing:-.01em}
.month-arrow{width:36px;height:36px;padding:10px}
.week-head{height:32px}
.week-head div{font-size:13px}
.calendar-grid{touch-action:pan-y;overscroll-behavior-x:none}
@media (prefers-reduced-motion: reduce){.calendar-card{transition-duration:0ms!important}}
'''
write(p,s)
print('V022_SWIPE_COMPACT_PATCH_OK')
