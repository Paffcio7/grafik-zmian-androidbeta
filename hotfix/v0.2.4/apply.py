from pathlib import Path

ROOT=Path('.')
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def write(p,s): (ROOT/p).write_text(s,encoding='utf-8')
def one(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'PATCH_FAIL {label}: expected 1 anchor, found {n}')
    return s.replace(old,new,1)

p='app/build.gradle'; s=read(p)
s=one(s,'versionCode 8','versionCode 9','versionCode')
s=one(s,"versionName '0.2.3'","versionName '0.2.4'",'versionName')
write(p,s)

p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
if '0.2.3' not in s: raise SystemExit('PATCH_FAIL MainActivity version anchor missing')
s=s.replace('0.2.3','0.2.4')
write(p,s)

p='app/src/main/assets/www/app.js'; s=read(p)
s=one(s,'Kalendarz zmian · v0.2.3','Kalendarz zmian · v0.2.4','drawer-version')
if "${isToday?'is-today':''}" not in s:
    raise SystemExit('PATCH_FAIL today class anchor missing')
write(p,s)

p='app/src/main/assets/www/styles.css'; s=read(p)
marker='/* v0.2.4 current-day highlight */'
if marker in s: raise SystemExit('PATCH_FAIL v0.2.4 CSS already present')
s += r'''

/* v0.2.4 current-day highlight */
.calendar-panel-current .cal-day.is-today{
  position:relative;
  border-radius:12px;
  box-shadow:inset 0 0 0 2px var(--blue);
  background:color-mix(in srgb,var(--blue) 5%, transparent);
}
.calendar-panel-current .cal-day.is-today .day-number{
  color:var(--blue);
  font-weight:800;
}
.calendar-panel-current .cal-day.is-today:active{
  background:color-mix(in srgb,var(--blue) 10%, transparent);
}
'''
write(p,s)
print('V024_CURRENT_DAY_HIGHLIGHT_OK')
