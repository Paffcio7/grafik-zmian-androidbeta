from pathlib import Path

ROOT=Path('.')
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def write(p,s): (ROOT/p).write_text(s,encoding='utf-8')
def one(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'PATCH_FAIL {label}: expected 1 anchor, found {n}')
    return s.replace(old,new,1)
def block(s,start,end,new,label):
    a=s.find(start); b=s.find(end,a+len(start))
    if a<0 or b<0: raise SystemExit(f'PATCH_FAIL {label}')
    return s[:a]+new+s[b:]

p='app/build.gradle'; s=read(p)
s=one(s,'versionCode 7','versionCode 8','versionCode')
s=one(s,"versionName '0.2.2'","versionName '0.2.3'",'versionName')
write(p,s)

p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
if '0.2.2' not in s: raise SystemExit('PATCH_FAIL MainActivity version anchor missing')
s=s.replace('0.2.2','0.2.3')
write(p,s)

p='app/src/main/assets/www/app.js'; s=read(p)
month_block=r'''  function monthPanel(baseMonth,role='current'){
    const y=baseMonth.getFullYear(),m=baseMonth.getMonth();
    const first=new Date(y,m,1);
    const offset=(first.getDay()+6)%7;
    const start=addDays(first,-offset);
    const today=today0();
    let cells='';
    for(let i=0;i<42;i++){
      const date=addDays(start,i);
      const inMonth=date.getMonth()===m;
      const isToday=keyOf(date)===keyOf(today);
      const code=shiftFor(date);
      const en=entryFor(date);
      const marker=en&&en.type&&en.type!=='plan'?entryMarker(en.type):code;
      const markerClass=marker==='D'?'day':marker==='N'?'night':marker&&marker!=='O'?'custom':'';
      const holiday=state.holidays?holidayName(date):'';
      cells+=`<button class="cal-day ${inMonth?'':'adjacent'} ${isToday?'is-today':''} ${holiday?'holiday':''}" data-date="${keyOf(date)}" data-current="${inMonth?'1':'0'}">
        <span class="day-number">${date.getDate()}</span>
        <span class="shift-dot ${markerClass}">${marker==='O'?'':esc(marker)}</span>
        ${en?.note?'<span class="note-dot"></span>':''}
      </button>`;
    }
    const nav=role==='current'
      ? `<button class="month-arrow" data-month="-1">${icon('left')}</button><div class="month-label">${cap(MONTHS[m])} ${y}</div><button class="month-arrow" data-month="1">${icon('right')}</button>`
      : `<span class="month-arrow month-arrow-placeholder"></span><div class="month-label">${cap(MONTHS[m])} ${y}</div><span class="month-arrow month-arrow-placeholder"></span>`;
    return `<section class="calendar-card calendar-panel calendar-panel-${role}" data-panel="${role}"><div class="month-head">${nav}</div><div class="week-head">${['Pn','Wt','Śr','Cz','Pt','So','Nd'].map(x=>`<div>${x}</div>`).join('')}</div><div class="calendar-grid">${cells}</div></section>`;
  }

  function monthCalendar(){
    const prev=shiftedMonth(currentMonth,-1),next=shiftedMonth(currentMonth,1);
    return `<div class="calendar-viewport"><div class="calendar-track">${monthPanel(prev,'prev')}${monthPanel(currentMonth,'current')}${monthPanel(next,'next')}</div></div>`;
  }

'''
s=block(s,'  function monthCalendar(){','  function entryMarker',month_block,'month-carousel-render')

anim_block=r'''  function shiftedMonth(base,delta){return new Date(base.getFullYear(),base.getMonth()+delta,1);}
  function setTrackDrag(track,dx){track.style.transform=`translate3d(calc(-33.333333% + ${dx}px),0,0)`;}
  function changeMonthAnimated(delta,fromPx=0){
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
  function bindMonthSwipe(){
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
s=block(s,'  function shiftedMonth(base,delta){','  function renderCalendar(){',anim_block,'month-carousel-motion')
s=one(s,'Kalendarz zmian · v0.2.2','Kalendarz zmian · v0.2.3','drawer-version')
write(p,s)

p='app/src/main/assets/www/styles.css'; s=read(p)
marker='/* v0.2.3 live adjacent-month carousel */'
if marker in s: raise SystemExit('PATCH_FAIL v0.2.3 CSS already present')
s += r'''

/* v0.2.3 live adjacent-month carousel */
.calendar-main{overflow:hidden}
.calendar-viewport{width:100%;overflow:hidden;touch-action:pan-y;overscroll-behavior-x:none}
.calendar-track{
  display:flex;
  width:300%;
  transform:translate3d(-33.333333%,0,0);
  will-change:transform;
  backface-visibility:hidden;
}
.calendar-panel{
  flex:0 0 33.333333%;
  width:33.333333%;
  min-width:0;
  transform:none!important;
  opacity:1!important;
}
.calendar-panel-prev,.calendar-panel-next{pointer-events:none}
.calendar-panel-current{pointer-events:auto}
.month-arrow-placeholder{display:block}
.calendar-grid{touch-action:pan-y}
@media (prefers-reduced-motion: reduce){.calendar-track{transition-duration:0ms!important}}
'''
write(p,s)
print('V023_LIVE_ADJACENT_MONTH_PATCH_OK')
