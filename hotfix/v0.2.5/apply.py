from pathlib import Path

ROOT=Path('.')
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def write(p,s): (ROOT/p).write_text(s,encoding='utf-8')
def one(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'PATCH_FAIL {label}: expected 1 anchor, found {n}')
    return s.replace(old,new,1)

p='app/build.gradle'; s=read(p)
s=one(s,'versionCode 9','versionCode 10','versionCode')
s=one(s,"versionName '0.2.4'","versionName '0.2.5'",'versionName')
write(p,s)

p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
if '0.2.4' not in s: raise SystemExit('PATCH_FAIL MainActivity version anchor missing')
s=s.replace('0.2.4','0.2.5')
write(p,s)

p='app/src/main/assets/www/app.js'; s=read(p)
s=one(s,'Kalendarz zmian · v0.2.4','Kalendarz zmian · v0.2.5','drawer-version')
write(p,s)

p='app/src/main/assets/www/styles.css'; s=read(p)
marker='/* v0.2.5 soft yellow today highlight */'
if marker in s: raise SystemExit('PATCH_FAIL v0.2.5 CSS already present')
s += r'''

/* v0.2.5 soft yellow today highlight */
.calendar-panel-current .cal-day.is-today{
  box-shadow:none;
  background:rgba(255,220,72,.30);
  border-radius:11px;
}
.calendar-panel-current .cal-day.is-today .day-number{
  color:var(--text);
  font-weight:800;
}
.calendar-panel-current .cal-day.is-today:active{
  background:rgba(255,220,72,.42);
}
html[data-theme="dark"] .calendar-panel-current .cal-day.is-today,
body.dark .calendar-panel-current .cal-day.is-today{
  background:rgba(255,220,72,.20);
}
'''
write(p,s)
print('V025_SOFT_YELLOW_TODAY_HIGHLIGHT_OK')
