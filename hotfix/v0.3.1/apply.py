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
s=one(s,'versionCode 15','versionCode 16','versionCode')
s=one(s,"versionName '0.3.0'","versionName '0.3.1'",'versionName')
write(p,s)

# UI version label
p='app/src/main/assets/www/app.js'; s=read(p)
s=one(s,'Kalendarz zmian · v0.3.0','Kalendarz zmian · v0.3.1','drawer-version')
write(p,s)

# Restore visible holiday styling in dark mode. v0.2.7's generic dark day-number rule
# had higher specificity than the base holiday rule and made holidays look like normal days.
p='app/src/main/assets/www/styles.css'; s=read(p)
marker='/* v0.3.1 dark holiday contrast */'
if marker in s: raise SystemExit('PATCH_FAIL v0.3.1 CSS already present')
s += r'''

/* v0.3.1 dark holiday contrast */
html[data-theme="dark"] .cal-day.holiday .day-number,
body.dark .cal-day.holiday .day-number{
  color:#ff6b6b;
  font-weight:750;
}
html[data-theme="dark"] .calendar-panel-current .cal-day.holiday.is-today .day-number,
body.dark .calendar-panel-current .cal-day.holiday.is-today .day-number{
  color:#ff7b7b;
}
html[data-theme="dark"] .cal-day.adjacent.holiday .day-number,
body.dark .cal-day.adjacent.holiday .day-number{
  color:#ff8585;
}
'''
write(p,s)

print('V031_DARK_HOLIDAY_CONTRAST_OK')
