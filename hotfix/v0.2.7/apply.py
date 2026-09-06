from pathlib import Path
import re

ROOT=Path('.')
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def write(p,s): (ROOT/p).write_text(s,encoding='utf-8')
def one(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'PATCH_FAIL {label}: expected 1 anchor, found {n}')
    return s.replace(old,new,1)

# Version
p='app/build.gradle'; s=read(p)
s=one(s,'versionCode 11','versionCode 12','versionCode')
s=one(s,"versionName '0.2.6'","versionName '0.2.7'",'versionName')
write(p,s)

# Native Android system bars: force status/navigation bars visible after every theme update.
p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
if '0.2.6' not in s: raise SystemExit('PATCH_FAIL MainActivity version anchor missing')
s=s.replace('0.2.6','0.2.7')
m=re.search(r'(private\s+void\s+setBars\s*\(\s*boolean\s+dark\s*\)\s*\{)',s)
if not m:
    m=re.search(r'(void\s+setBars\s*\(\s*boolean\s+dark\s*\)\s*\{)',s)
if not m: raise SystemExit('PATCH_FAIL setBars(boolean dark) not found')
start=m.end()-1
depth=0; end=None
for i in range(start,len(s)):
    if s[i]=='{': depth+=1
    elif s[i]=='}':
        depth-=1
        if depth==0:
            end=i; break
if end is None: raise SystemExit('PATCH_FAIL setBars body end not found')
native=r'''
        // v0.2.7: never run the app in fullscreen. Keep Android status icons visible.
        getWindow().clearFlags(android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN);
        android.view.View decor = getWindow().getDecorView();
        int flags = decor.getSystemUiVisibility();
        flags &= ~android.view.View.SYSTEM_UI_FLAG_FULLSCREEN;
        flags &= ~android.view.View.SYSTEM_UI_FLAG_IMMERSIVE;
        flags &= ~android.view.View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY;
        flags &= ~android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
        if (android.os.Build.VERSION.SDK_INT >= 26) {
            if (!dark) flags |= android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            else flags &= ~android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
        }
        decor.setSystemUiVisibility(flags);
        if (android.os.Build.VERSION.SDK_INT >= 30) {
            android.view.WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.show(android.view.WindowInsets.Type.statusBars() | android.view.WindowInsets.Type.navigationBars());
                controller.setSystemBarsAppearance(0, android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS);
                controller.setSystemBarsAppearance(
                    dark ? 0 : android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS,
                    android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
                );
            }
        }
        getWindow().setStatusBarColor(android.graphics.Color.parseColor("#164BB7"));
        getWindow().setNavigationBarColor(android.graphics.Color.parseColor(dark ? "#0B1118" : "#F4F7FA"));
'''
s=s[:end]+native+s[end:]
write(p,s)

# Web UI theme selector and system-following behavior.
p='app/src/main/assets/www/app.js'; s=read(p)
s=one(s,
"  const defaults={brigade:null,setupDone:false,weekNumbers:false,holidays:true,notifications:true,leadMin:60,hideNotif:true,lockMode:'none',pinHash:'',entries:{},version:2};",
"  const defaults={brigade:null,setupDone:false,theme:'system',weekNumbers:false,holidays:true,notifications:true,leadMin:60,hideNotif:true,lockMode:'none',pinHash:'',entries:{},version:2};",
'default-theme')
s=one(s,
"    return `${appBar()}<main class=\"main inner-page\"><div class=\"section-heading\">Ustawienia</div><div class=\"settings-list\">\n      ${toggleRow('holidays','Święta publiczne','Oznaczaj święta w Polsce')}",
"    return `${appBar()}<main class=\"main inner-page\"><div class=\"section-heading\">Ustawienia</div><div class=\"settings-list\">\n      <button class=\"setting-row\" data-theme-settings><span class=\"setting-icon\">${icon('gear')}</span><span><b>Motyw</b><small>${themeLabel()}</small></span><em>›</em></button>\n      ${toggleRow('holidays','Święta publiczne','Oznaczaj święta w Polsce')}",
'settings-theme-row')
s=one(s,
"    document.querySelector('[data-notif-time]')?.addEventListener('click',notificationSheet);",
"    document.querySelector('[data-theme-settings]')?.addEventListener('click',themeSheet);\n    document.querySelector('[data-notif-time]')?.addEventListener('click',notificationSheet);",
'theme-bind')
anchor="  function notificationSheet(){\n"
if s.count(anchor)!=1: raise SystemExit('PATCH_FAIL notificationSheet anchor')
theme_funcs=r'''  function themeLabel(){return state.theme==='dark'?'Ciemny':state.theme==='light'?'Jasny':'Systemowy';}
  function themeSheet(){
    const vals=[['system','Systemowy','Dopasuj do ustawień telefonu'],['light','Jasny','Zawsze jasny wygląd'],['dark','Ciemny','Zawsze ciemny wygląd']];
    showSheet('Motyw','Wybierz wygląd aplikacji.',vals.map(([v,l,d])=>`<button class="sheet-line theme-line" data-theme="${v}"><span><b>${l}</b><small>${d}</small></span><strong>${state.theme===v?'✓':''}</strong></button>`).join(''),root=>{
      root.querySelectorAll('[data-theme]').forEach(b=>b.onclick=()=>{state.theme=b.dataset.theme;save();closeSheet();render();});
    });
  }
'''
s=s.replace(anchor,theme_funcs+anchor,1)
s=one(s,'Kalendarz zmian · v0.2.6','Kalendarz zmian · v0.2.7','drawer-version')
old="  function setSystemBars(){try{AndroidApp.setSystemBars(false);}catch{}}"
new=r'''  function systemPrefersDark(){try{return window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;}catch{return false;}}
  function resolvedDark(){return state.theme==='dark'||(state.theme==='system'&&systemPrefersDark());}
  function applyTheme(){
    const dark=resolvedDark();
    document.documentElement.dataset.theme=dark?'dark':'light';
    document.body.classList.toggle('dark',dark);
    try{AndroidApp.setSystemBars(dark);}catch{}
  }
  function setSystemBars(){applyTheme();}'''
s=one(s,old,new,'theme-system-bars')
# Listen for live Android theme changes when Systemowy is selected.
needle="  render();scheduleReminders();setTimeout(()=>{if(state.lockMode!=='none')lockNow();},400);"
repl="  try{window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if(state.theme==='system')applyTheme();});}catch{}\n  applyTheme();\n  render();scheduleReminders();setTimeout(()=>{if(state.lockMode!=='none')lockNow();},400);"
s=one(s,needle,repl,'system-theme-listener')
write(p,s)

# Dark theme overrides.
p='app/src/main/assets/www/styles.css'; s=read(p)
marker='/* v0.2.7 visible system bars + full theme selector */'
if marker in s: raise SystemExit('PATCH_FAIL v0.2.7 CSS already present')
s += r'''

/* v0.2.7 visible system bars + full theme selector */
html[data-theme="dark"]{
  --bg:#0b1118;--surface:#121a24;--text:#f2f5f8;--muted:#93a0ae;--line:#26313d;
  --blue-soft:#102b3c;--shadow:0 10px 28px rgba(0,0,0,.32);
}
html[data-theme="dark"],html[data-theme="dark"] body{background:var(--bg);color:var(--text)}
html[data-theme="dark"] .calendar-main,
html[data-theme="dark"] .calendar-card,
html[data-theme="dark"] .calendar-grid,
html[data-theme="dark"] .cal-day{background:var(--surface)}
html[data-theme="dark"] .month-head,
html[data-theme="dark"] .week-head,
html[data-theme="dark"] .cal-day{border-color:var(--line)}
html[data-theme="dark"] .cal-day .day-number{color:var(--text)}
html[data-theme="dark"] .week-head div,
html[data-theme="dark"] .month-arrow{color:#9aa6b3}
html[data-theme="dark"] .drawer,
html[data-theme="dark"] .settings-list,
html[data-theme="dark"] .panel,
html[data-theme="dark"] .stats div,
html[data-theme="dark"] .sheet,
html[data-theme="dark"] .date-picker-card{background:var(--surface);border-color:var(--line);color:var(--text)}
html[data-theme="dark"] .setting-row,
html[data-theme="dark"] .sheet-line{border-color:var(--line);color:var(--text)}
html[data-theme="dark"] .setting-row small,
html[data-theme="dark"] .panel p,
html[data-theme="dark"] .sheet>p,
html[data-theme="dark"] .drawer-item small{color:var(--muted)}
html[data-theme="dark"] .drawer-item>span{color:#9ba7b3}
html[data-theme="dark"] .drawer-item.active{background:#102b3c;color:#55b8ee}
html[data-theme="dark"] .drawer-item.active>span{color:#55b8ee}
html[data-theme="dark"] .drawer-sep{background:var(--line)}
html[data-theme="dark"] .date-picker-title,
html[data-theme="dark"] .picker-day span{color:var(--text)}
html[data-theme="dark"] .picker-week-head div,
html[data-theme="dark"] .picker-nav-btn{color:#9ca8b4}
html[data-theme="dark"] .date-picker-cancel,
html[data-theme="dark"] .sheet-cancel{background:#202a35;color:#e7edf3}
html[data-theme="dark"] .pin{background:#0f1720;border-color:var(--line);color:var(--text)}
html[data-theme="dark"] .lock-screen{background:var(--bg);color:var(--text)}
html[data-theme="dark"] .onboarding{background:linear-gradient(160deg,#082e70 0%,#0b648f 45%,#0b1118 45.1%)}
html[data-theme="dark"] .onboard-card{background:var(--surface);color:var(--text)}
html[data-theme="dark"] .onboard-card p{color:var(--muted)}
html[data-theme="dark"] .brigade-choose button{background:#0f1720;border-color:var(--line)}
html[data-theme="dark"] .theme-line>span{display:flex;flex-direction:column;align-items:flex-start}
.theme-line small{display:block;font-size:11px;color:var(--muted);margin-top:2px}
.theme-line strong{color:var(--primary);font-size:18px}
'''
write(p,s)

print('V027_STATUS_BAR_AND_THEME_OK')
