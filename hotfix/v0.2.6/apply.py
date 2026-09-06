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
s=one(s,'versionCode 10','versionCode 11','versionCode')
s=one(s,"versionName '0.2.5'","versionName '0.2.6'",'versionName')
write(p,s)

p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
if '0.2.5' not in s: raise SystemExit('PATCH_FAIL MainActivity version anchor missing')
s=s.replace('0.2.5','0.2.6')
write(p,s)

p='app/src/main/assets/www/app.js'; s=read(p)
# B and C were swapped in the previous mapping. Preserve A/D and exchange only B/C.
s=one(s,
"  const BRIGADE_OFFSET={A:0,B:7,C:14,D:21};",
"  const BRIGADE_OFFSET={A:0,B:14,C:7,D:21};",
'brigade-offsets')

s=one(s,
"  let suppressDayClickUntil=0;",
"  let suppressDayClickUntil=0;\n  let pickerMonth=null;\n  let pickerSelected=null;",
'picker-state')

s=one(s,
'''    return `<header class="appbar"><button class="appbar-icon" data-menu aria-label="Menu">${icon('menu')}</button><div class="appbar-copy"><div class="appbar-title">Zmiana ${state.brigade||'?'}</div><div class="appbar-subtitle">PepsiCo, Środa Śląska</div></div><button class="today-action" data-today>DZIŚ</button></header>`;''',
'''    return `<header class="appbar"><button class="appbar-icon" data-menu aria-label="Menu">${icon('menu')}</button><div class="appbar-copy"><div class="appbar-title">Zmiana ${state.brigade||'?'}</div><div class="appbar-subtitle">PepsiCo, Środa Śląska</div></div><div class="appbar-actions"><button class="appbar-mini-icon" data-open-date-picker aria-label="Wybierz datę">${icon('cal')}</button><button class="today-action" data-today>DZIŚ</button></div></header>`;''',
'appbar-date-picker')

s=one(s,
"    document.querySelector('[data-today]')?.addEventListener('click',()=>{const n=new Date();currentMonth=new Date(n.getFullYear(),n.getMonth(),1);screen='calendar';drawerOpen=false;render();});\n",
"    document.querySelector('[data-today]')?.addEventListener('click',()=>{const n=new Date();currentMonth=new Date(n.getFullYear(),n.getMonth(),1);screen='calendar';drawerOpen=false;render();});\n    document.querySelector('[data-open-date-picker]')?.addEventListener('click',openDatePicker);\n",
'picker-bind')

anchor='''  function fallbackDaySheet(date,sm,en,label){\n    showSheet('Szczegóły dnia',label,`<p><b>Zmiana ${state.brigade}</b> · ${sm.name} · ${sm.time}</p><p>Edytor wpisu jest dostępny w aplikacji Android.</p>`,()=>{});\n  }\n\n'''
if s.count(anchor)!=1: raise SystemExit('PATCH_FAIL date-picker insertion anchor')
picker=r'''  function openDatePicker(){
    const base=new Date(currentMonth.getFullYear(),currentMonth.getMonth(),1);
    pickerMonth=base;
    const today=today0();
    pickerSelected=(today.getFullYear()===base.getFullYear()&&today.getMonth()===base.getMonth())?today:new Date(base.getFullYear(),base.getMonth(),1);
    renderDatePicker();
  }

  function renderDatePicker(){
    const root=document.getElementById('sheet-root');
    const first=new Date(pickerMonth.getFullYear(),pickerMonth.getMonth(),1);
    const offset=(first.getDay()+6)%7;
    const start=addDays(first,-offset);
    let cells='';
    const todayKey=keyOf(today0());
    const selectedKey=pickerSelected?keyOf(pickerSelected):'';
    for(let i=0;i<42;i++){
      const date=addDays(start,i), key=keyOf(date);
      const inMonth=date.getMonth()===pickerMonth.getMonth()&&date.getFullYear()===pickerMonth.getFullYear();
      cells+=`<button class="picker-day ${inMonth?'':'adjacent'} ${key===selectedKey?'selected':''} ${key===todayKey?'today':''}" data-picker-day="${key}"><span>${date.getDate()}</span></button>`;
    }
    root.innerHTML=`<div class="date-picker-overlay"><button class="sheet-scrim" data-close-date-picker aria-label="Anuluj"></button><div class="date-picker-card"><div class="date-picker-head"><div class="date-picker-title">${cap(MONTHS[pickerMonth.getMonth()])} ${pickerMonth.getFullYear()}</div><div class="date-picker-nav"><button class="picker-nav-btn" data-picker-month="-1" aria-label="Poprzedni miesiąc">${icon('left')}</button><button class="picker-nav-btn" data-picker-month="1" aria-label="Następny miesiąc">${icon('right')}</button></div></div><div class="picker-week-head">${['Pn','Wt','Śr','Cz','Pt','So','Nd'].map(x=>`<div>${x}</div>`).join('')}</div><div class="picker-grid">${cells}</div><div class="date-picker-actions"><button class="date-picker-cancel" data-close-date-picker>Anuluj</button><button class="date-picker-ok" data-apply-date-picker>OK</button></div></div></div>`;
    root.querySelectorAll('[data-close-date-picker]').forEach(b=>b.onclick=closeDatePicker);
    root.querySelectorAll('[data-picker-month]').forEach(b=>b.onclick=()=>{pickerMonth=shiftedMonth(pickerMonth,Number(b.dataset.pickerMonth));renderDatePicker();});
    root.querySelectorAll('[data-picker-day]').forEach(b=>b.onclick=()=>{const d=dateFromKey(b.dataset.pickerDay);pickerSelected=d;if(d.getMonth()!==pickerMonth.getMonth()||d.getFullYear()!==pickerMonth.getFullYear())pickerMonth=new Date(d.getFullYear(),d.getMonth(),1);renderDatePicker();});
    root.querySelector('[data-apply-date-picker]').onclick=()=>{const d=pickerSelected||today0();currentMonth=new Date(d.getFullYear(),d.getMonth(),1);closeDatePicker();screen='calendar';render();};
  }
  function closeDatePicker(){pickerMonth=null;pickerSelected=null;document.getElementById('sheet-root').innerHTML='';}

'''
s=s.replace(anchor,anchor+picker,1)
s=one(s,'Kalendarz zmian · v0.2.5','Kalendarz zmian · v0.2.6','drawer-version')
write(p,s)

p='app/src/main/assets/www/styles.css'; s=read(p)
marker='/* v0.2.6 brigade B/C fix + top date picker */'
if marker in s: raise SystemExit('PATCH_FAIL v0.2.6 CSS already present')
s += r'''

/* v0.2.6 brigade B/C fix + top date picker */
.appbar{grid-template-columns:40px 1fr auto}
.appbar-actions{display:flex;align-items:center;gap:2px}
.appbar-mini-icon{width:32px;height:32px;padding:7px;color:#fff;opacity:.96}
.today-action{padding:0 6px}
.date-picker-overlay{position:fixed;z-index:120;inset:0;display:grid;place-items:center;padding:18px}
.date-picker-card{position:relative;width:min(100%,420px);background:#fff;border-radius:20px;box-shadow:0 28px 70px rgba(0,0,0,.28);padding:18px 16px 14px}
.date-picker-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px}
.date-picker-title{font-size:21px;font-weight:700;color:#1b2430}
.date-picker-nav{display:flex;gap:4px}
.picker-nav-btn{width:36px;height:36px;padding:9px;color:#5f6975}
.picker-week-head,.picker-grid{display:grid;grid-template-columns:repeat(7,1fr)}
.picker-week-head{margin-top:8px}
.picker-week-head div{text-align:center;font-size:12px;color:#788391;font-weight:600;padding:4px 0 8px}
.picker-grid{gap:4px}
.picker-day{height:42px;border-radius:12px;display:grid;place-items:center;background:transparent}
.picker-day span{font-size:15px;font-weight:500;color:#202833}
.picker-day.adjacent span{opacity:.28}
.picker-day.today{background:rgba(255,220,72,.22)}
.picker-day.selected{background:var(--primary);box-shadow:0 8px 20px rgba(22,136,201,.23)}
.picker-day.selected span{color:#fff;font-weight:700}
.date-picker-actions{display:flex;justify-content:flex-end;gap:10px;padding-top:12px}
.date-picker-cancel,.date-picker-ok{height:40px;padding:0 16px;border-radius:10px;font-weight:700}
.date-picker-cancel{background:#f0f3f6;color:#425061}
.date-picker-ok{background:var(--primary);color:#fff}
'''
write(p,s)

p='app/src/main/assets/www/index.html'; s=read(p)
s=s.replace('<title>Twój grafik</title>','<title>Kalendarz zmian</title>')
write(p,s)

print('V026_PROPER_BUILD_PATCH_OK')
