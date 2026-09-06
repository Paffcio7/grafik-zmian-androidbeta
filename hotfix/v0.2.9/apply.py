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
s=one(s,'versionCode 13','versionCode 14','versionCode')
s=one(s,"versionName '0.2.8'","versionName '0.2.9'",'versionName')
write(p,s)

# Android 15/16 edge-to-edge can ignore statusBarColor and expose the root surface
# behind the transparent status bar. Keep that underlying surface in sync with theme.
p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
if '0.2.8' not in s: raise SystemExit('PATCH_FAIL MainActivity version anchor missing')
s=s.replace('0.2.8','0.2.9')
s=one(s,
'        getWindow().setStatusBarColor(Color.parseColor(dark ? "#0B1118" : "#F4F7FA"));',
'''        int systemSurface=Color.parseColor(dark ? "#0B1118" : "#F4F7FA");
        getWindow().setStatusBarColor(systemSurface);
        getWindow().getDecorView().setBackgroundColor(systemSurface);
        if(webView!=null){
            webView.setBackgroundColor(systemSurface);
            android.view.ViewParent parent=webView.getParent();
            if(parent instanceof android.view.View){
                ((android.view.View)parent).setBackgroundColor(systemSurface);
            }
        }''',
'edge-to-edge-root-surface')
write(p,s)

# Date picker year selector.
p='app/src/main/assets/www/app.js'; s=read(p)
s=one(s,'Kalendarz zmian · v0.2.8','Kalendarz zmian · v0.2.9','drawer-version')
s=one(s,
'  let pickerSelected=null;',
'  let pickerSelected=null;\n  let pickerYearMode=false;',
'picker-year-state')
s=one(s,
'    pickerMonth=base;\n    const today=today0();',
'    pickerMonth=base;\n    pickerYearMode=false;\n    const today=today0();',
'picker-year-reset-open')
s=one(s,
'''<div class="date-picker-head"><div class="date-picker-title">${cap(MONTHS[pickerMonth.getMonth()])} ${pickerMonth.getFullYear()}</div><div class="date-picker-nav">''',
'''<div class="date-picker-head"><div class="date-picker-title">${cap(MONTHS[pickerMonth.getMonth()])} <button class="picker-year-toggle" data-picker-year-toggle>${pickerMonth.getFullYear()}</button></div><div class="date-picker-nav">''',
'picker-year-toggle-markup')
s=one(s,
"    root.querySelectorAll('[data-close-date-picker]').forEach(b=>b.onclick=closeDatePicker);",
"    root.querySelector('[data-picker-year-toggle]')?.addEventListener('click',renderDatePickerYears);\n    root.querySelectorAll('[data-close-date-picker]').forEach(b=>b.onclick=closeDatePicker);",
'picker-year-toggle-bind')
anchor="  function closeDatePicker(){pickerMonth=null;pickerSelected=null;document.getElementById('sheet-root').innerHTML='';}\n"
year_func=r'''  function renderDatePickerYears(){
    pickerYearMode=true;
    const root=document.getElementById('sheet-root');
    const current=pickerMonth.getFullYear();
    let years='';
    for(let year=current-40;year<=current+40;year++){
      years+=`<button class="picker-year ${year===current?'selected':''}" data-picker-year="${year}">${year}</button>`;
    }
    root.innerHTML=`<div class="date-picker-overlay"><button class="sheet-scrim" data-close-date-picker aria-label="Anuluj"></button><div class="date-picker-card year-picker-card"><div class="date-picker-head"><div><div class="year-picker-caption">Wybierz rok</div><div class="date-picker-title">${cap(MONTHS[pickerMonth.getMonth()])} <span>${current}</span></div></div><button class="picker-year-close" data-picker-year-back aria-label="Wróć">×</button></div><div class="picker-year-list">${years}</div><div class="date-picker-actions"><button class="date-picker-cancel" data-close-date-picker>Anuluj</button></div></div></div>`;
    root.querySelectorAll('[data-close-date-picker]').forEach(b=>b.onclick=closeDatePicker);
    root.querySelector('[data-picker-year-back]')?.addEventListener('click',()=>{pickerYearMode=false;renderDatePicker();});
    root.querySelectorAll('[data-picker-year]').forEach(b=>b.onclick=()=>{
      const year=Number(b.dataset.pickerYear);
      const month=pickerMonth.getMonth();
      const oldDay=pickerSelected?.getDate()||1;
      const maxDay=new Date(year,month+1,0).getDate();
      pickerMonth=new Date(year,month,1);
      pickerSelected=new Date(year,month,Math.min(oldDay,maxDay));
      pickerYearMode=false;
      renderDatePicker();
    });
    requestAnimationFrame(()=>{
      const list=root.querySelector('.picker-year-list');
      const selected=root.querySelector('.picker-year.selected');
      if(list&&selected) list.scrollTop=selected.offsetTop-list.clientHeight/2+selected.clientHeight/2;
    });
  }

'''
if s.count(anchor)!=1: raise SystemExit('PATCH_FAIL closeDatePicker anchor')
s=s.replace(anchor,year_func+"  function closeDatePicker(){pickerMonth=null;pickerSelected=null;pickerYearMode=false;document.getElementById('sheet-root').innerHTML='';}\n",1)
write(p,s)

# Year picker UI, including dark theme.
p='app/src/main/assets/www/styles.css'; s=read(p)
marker='/* v0.2.9 dark system surface + year picker */'
if marker in s: raise SystemExit('PATCH_FAIL v0.2.9 CSS already present')
s += r'''

/* v0.2.9 dark system surface + year picker */
.picker-year-toggle{display:inline-flex;align-items:center;padding:2px 4px;margin:-2px -4px;border-radius:7px;color:inherit;font:inherit;font-weight:inherit}
.picker-year-toggle:active{background:rgba(22,136,201,.10)}
.year-picker-card{max-height:min(78vh,620px);display:flex;flex-direction:column}
.year-picker-caption{font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px}
.picker-year-close{width:36px;height:36px;border-radius:50%;font-size:25px;line-height:1;color:#687381;background:transparent}
.picker-year-list{min-height:260px;max-height:430px;overflow-y:auto;overscroll-behavior:contain;padding:8px 0;scrollbar-width:none}
.picker-year-list::-webkit-scrollbar{display:none}
.picker-year{width:100%;height:54px;display:flex;align-items:center;justify-content:center;border-radius:12px;font-size:20px;font-weight:500;color:#26303a;background:transparent}
.picker-year.selected{color:var(--primary);font-size:27px;font-weight:750;background:rgba(22,136,201,.08)}
html[data-theme="dark"] .picker-year{color:#e8edf2}
html[data-theme="dark"] .picker-year.selected{color:#58bcec;background:rgba(88,188,236,.12)}
html[data-theme="dark"] .picker-year-close{color:#a9b5c1}
'''
write(p,s)

print('V029_DARK_SYSTEM_SURFACE_AND_YEAR_PICKER_OK')
