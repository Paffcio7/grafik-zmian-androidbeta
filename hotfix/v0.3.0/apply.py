from pathlib import Path

ROOT=Path('.')
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def write(p,s): (ROOT/p).write_text(s,encoding='utf-8')
def one(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'PATCH_FAIL {label}: expected 1 anchor, found {n}')
    return s.replace(old,new,1)

# Version
p='app/build.gradle'; s=read(p)
s=one(s,'versionCode 14','versionCode 15','versionCode')
s=one(s,"versionName '0.2.9'","versionName '0.3.0'",'versionName')
write(p,s)

# Responsive month carousel: shorter settling, lower threshold, velocity flick,
# and requestAnimationFrame-batched drag painting for smoother WebView motion.
p='app/src/main/assets/www/app.js'; s=read(p)
s=one(s,'Kalendarz zmian · v0.2.9','Kalendarz zmian · v0.3.0','drawer-version')
old_change='''  function changeMonthAnimated(delta,fromPx=0){
    if(!delta||monthAnimating)return;
    const viewport=document.querySelector('.calendar-viewport');
    const track=document.querySelector('.calendar-track');
    if(!viewport||!track){currentMonth=shiftedMonth(currentMonth,delta);render();return;}
    monthAnimating=true;
    const width=Math.max(1,viewport.getBoundingClientRect().width||window.innerWidth);
    const targetDx=delta>0?-width:width;
    setTrackDrag(track,Number.isFinite(fromPx)?fromPx:0);
    track.style.transition='transform 255ms cubic-bezier(.22,.61,.36,1)';
    let done=false;
    const finish=()=>{
      if(done)return; done=true;
      currentMonth=shiftedMonth(currentMonth,delta);
      monthAnimating=false;
      render();
    };
    track.addEventListener('transitionend',finish,{once:true});
    requestAnimationFrame(()=>setTrackDrag(track,targetDx));
    setTimeout(finish,330);
  }
'''
new_change='''  function changeMonthAnimated(delta,fromPx=0,velocity=0){
    if(!delta||monthAnimating)return;
    const viewport=document.querySelector('.calendar-viewport');
    const track=document.querySelector('.calendar-track');
    if(!viewport||!track){currentMonth=shiftedMonth(currentMonth,delta);render();return;}
    monthAnimating=true;
    const width=Math.max(1,viewport.getBoundingClientRect().width||window.innerWidth);
    const targetDx=delta>0?-width:width;
    const startDx=Number.isFinite(fromPx)?fromPx:0;
    const remaining=Math.max(0,Math.abs(targetDx-startDx));
    const velocityBoost=Math.min(55,Math.abs(Number(velocity)||0)*38);
    const distanceFactor=Math.min(25,(remaining/width)*20);
    const duration=Math.round(Math.max(125,Math.min(205,188+distanceFactor-velocityBoost)));
    setTrackDrag(track,startDx);
    track.style.transition=`transform ${duration}ms cubic-bezier(.2,.78,.24,1)`;
    let done=false;
    const finish=()=>{
      if(done)return; done=true;
      currentMonth=shiftedMonth(currentMonth,delta);
      monthAnimating=false;
      render();
    };
    track.addEventListener('transitionend',finish,{once:true});
    requestAnimationFrame(()=>setTrackDrag(track,targetDx));
    setTimeout(finish,duration+90);
  }
'''
s=one(s,old_change,new_change,'month-animation')
old_bind='''  function bindMonthSwipe(){
    const viewport=document.querySelector('.calendar-viewport');
    const track=document.querySelector('.calendar-track');
    if(!viewport||!track)return;
    let pointerId=null,startX=0,startY=0,dx=0,dragging=false,rejected=false;
    viewport.addEventListener('pointerdown',e=>{
      if(monthAnimating||(e.pointerType==='mouse'&&e.button!==0))return;
      pointerId=e.pointerId;startX=e.clientX;startY=e.clientY;dx=0;dragging=false;rejected=false;
      track.style.transition='none';
    });
    viewport.addEventListener('pointermove',e=>{
      if(e.pointerId!==pointerId||rejected||monthAnimating)return;
      const mx=e.clientX-startX,my=e.clientY-startY;
      if(!dragging){
        if(Math.abs(mx)<6&&Math.abs(my)<6)return;
        if(Math.abs(my)>Math.abs(mx)){rejected=true;setTrackDrag(track,0);return;}
        dragging=true;suppressDayClickUntil=Date.now()+500;
        try{viewport.setPointerCapture(pointerId);}catch{}
      }
      e.preventDefault();
      const width=Math.max(1,viewport.getBoundingClientRect().width||window.innerWidth);
      dx=Math.max(-width*.98,Math.min(width*.98,mx));
      setTrackDrag(track,dx);
    });
    const finish=e=>{
      if(e.pointerId!==pointerId)return;
      if(dragging&&!monthAnimating){
        suppressDayClickUntil=Date.now()+500;
        const width=Math.max(1,viewport.getBoundingClientRect().width||window.innerWidth);
        const threshold=Math.min(68,width*.17);
        if(Math.abs(dx)>=threshold){changeMonthAnimated(dx<0?1:-1,dx);}
        else{
          track.style.transition='transform 190ms cubic-bezier(.22,.61,.36,1)';
          setTrackDrag(track,0);
          setTimeout(()=>{if(!monthAnimating)track.style.transition='';},205);
        }
      }
      pointerId=null;dragging=false;rejected=false;dx=0;
    };
    viewport.addEventListener('pointerup',finish);
    viewport.addEventListener('pointercancel',finish);
  }
'''
new_bind='''  function bindMonthSwipe(){
    const viewport=document.querySelector('.calendar-viewport');
    const track=document.querySelector('.calendar-track');
    if(!viewport||!track)return;
    let pointerId=null,startX=0,startY=0,dx=0,dragging=false,rejected=false;
    let lastX=0,lastT=0,velocity=0,raf=0,pendingDx=0;
    const paint=()=>{raf=0;setTrackDrag(track,pendingDx);};
    viewport.addEventListener('pointerdown',e=>{
      if(monthAnimating||(e.pointerType==='mouse'&&e.button!==0))return;
      pointerId=e.pointerId;startX=e.clientX;startY=e.clientY;dx=0;dragging=false;rejected=false;
      lastX=e.clientX;lastT=performance.now();velocity=0;pendingDx=0;
      track.style.transition='none';
    });
    viewport.addEventListener('pointermove',e=>{
      if(e.pointerId!==pointerId||rejected||monthAnimating)return;
      const mx=e.clientX-startX,my=e.clientY-startY;
      if(!dragging){
        if(Math.abs(mx)<4&&Math.abs(my)<4)return;
        if(Math.abs(my)>Math.abs(mx)*1.08){rejected=true;setTrackDrag(track,0);return;}
        dragging=true;suppressDayClickUntil=Date.now()+350;
        try{viewport.setPointerCapture(pointerId);}catch{}
      }
      e.preventDefault();
      const now=performance.now();
      const dt=Math.max(8,now-lastT);
      const instant=(e.clientX-lastX)/dt;
      velocity=velocity*.62+instant*.38;
      lastX=e.clientX;lastT=now;
      const width=Math.max(1,viewport.getBoundingClientRect().width||window.innerWidth);
      dx=Math.max(-width*.995,Math.min(width*.995,mx));
      pendingDx=dx;
      if(!raf)raf=requestAnimationFrame(paint);
    });
    const finish=e=>{
      if(e.pointerId!==pointerId)return;
      if(raf){cancelAnimationFrame(raf);raf=0;setTrackDrag(track,pendingDx);}
      if(dragging&&!monthAnimating){
        suppressDayClickUntil=Date.now()+350;
        const width=Math.max(1,viewport.getBoundingClientRect().width||window.innerWidth);
        const threshold=Math.min(48,width*.12);
        const fastFlick=Math.abs(velocity)>=.48&&Math.abs(dx)>=18;
        if(Math.abs(dx)>=threshold||fastFlick){changeMonthAnimated(dx<0?1:-1,dx,velocity);}
        else{
          track.style.transition='transform 135ms cubic-bezier(.2,.78,.24,1)';
          setTrackDrag(track,0);
          setTimeout(()=>{if(!monthAnimating)track.style.transition='';},155);
        }
      }
      pointerId=null;dragging=false;rejected=false;dx=0;pendingDx=0;velocity=0;
    };
    viewport.addEventListener('pointerup',finish);
    viewport.addEventListener('pointercancel',finish);
  }
'''
s=one(s,old_bind,new_bind,'month-swipe')
write(p,s)

# Dark-mode visual polish.
p='app/src/main/assets/www/styles.css'; s=read(p)
marker='/* v0.3.0 dark polish + responsive month swipe */'
if marker in s: raise SystemExit('PATCH_FAIL v0.3.0 CSS already present')
s += r'''

/* v0.3.0 dark polish + responsive month swipe */
html[data-theme="dark"] .shift-dot.night,body.dark .shift-dot.night{
  background:#080a0d;
  border:1px solid #39424c;
  box-shadow:0 2px 7px rgba(0,0,0,.22);
  box-sizing:border-box;
}
html[data-theme="dark"] .calendar-panel-current .cal-day.is-today,
body.dark .calendar-panel-current .cal-day.is-today{background:rgba(255,214,64,.16)}
html[data-theme="dark"] .calendar-panel-current .cal-day.is-today:active,
body.dark .calendar-panel-current .cal-day.is-today:active{background:rgba(255,214,64,.24)}
html[data-theme="dark"] .cal-day.adjacent,body.dark .cal-day.adjacent{opacity:.40}
html[data-theme="dark"] .cal-day.adjacent .shift-dot,
body.dark .cal-day.adjacent .shift-dot{filter:saturate(.70) brightness(.94)}
.calendar-track{transform-style:preserve-3d}
'''
write(p,s)

print('V030_DARK_POLISH_AND_RESPONSIVE_SWIPE_OK')
