from pathlib import Path

ROOT = Path('.')

def read(rel): return (ROOT / rel).read_text(encoding='utf-8')
def write(rel, s): (ROOT / rel).write_text(s, encoding='utf-8')
def one(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'PATCH_FAIL {label}: expected 1 anchor, found {n}')
    return s.replace(old, new, 1)

p='app/build.gradle'; s=read(p)
s=one(s, 'versionCode 5', 'versionCode 6', 'versionCode')
s=one(s, "versionName '0.2.0'", "versionName '0.2.1'", 'versionName')
write(p,s)

p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
if '0.2.0' not in s:
    raise SystemExit('PATCH_FAIL MainActivity version anchor missing')
s=s.replace('0.2.0','0.2.1')
write(p,s)

p='app/src/main/assets/www/app.js'; s=read(p)
s=one(s, 'for(let i=0;i<49;i++){', 'for(let i=0;i<42;i++){', 'calendar-cell-count')
s=one(s, 'Kalendarz zmian · v0.2.0', 'Kalendarz zmian · v0.2.1', 'drawer-version')
write(p,s)

p='app/src/main/assets/www/styles.css'; s=read(p)
marker='/* v0.2.1 compact calendar UI */'
if marker in s:
    raise SystemExit('PATCH_FAIL compact CSS already present')
s += r'''

/* v0.2.1 compact calendar UI */
.appbar{
  height:82px;
  grid-template-columns:48px 1fr 60px;
  padding:0 10px;
  box-shadow:0 1px 5px rgba(0,0,0,.12);
}
.appbar-icon{width:42px;height:42px;padding:10px}
.appbar-copy{padding-left:4px}
.appbar-title{font-size:21px;font-weight:700;line-height:1.05}
.appbar-subtitle{font-size:12.5px;margin-top:4px;opacity:.78}
.today-action{height:42px;font-size:12.5px;font-weight:700;letter-spacing:.025em}
.calendar-main{min-height:calc(100vh - 82px)}
.month-head{
  height:52px;
  grid-template-columns:42px 1fr 42px;
}
.month-label{font-size:20px;font-weight:500;letter-spacing:-.01em}
.month-arrow{width:42px;height:42px;padding:12px}
.week-head{height:36px}
.week-head div{font-size:13.5px;font-weight:500}
.cal-day{
  height:64px;
  padding-top:5px;
}
.cal-day .day-number{font-size:14.5px;line-height:18px;font-weight:500}
.shift-dot{
  margin-top:4px;
  min-width:25px;
  width:25px;
  height:25px;
  padding:0;
  font-size:12px;
  font-weight:800;
}
.shift-dot.day{background:var(--day);color:#fff}
.shift-dot.night{background:#111;color:#fff}
.note-dot{bottom:3px;width:4px;height:4px}
.cal-day.adjacent{opacity:.27}
.cal-day.adjacent .shift-dot{filter:saturate(.55)}
.drawer-head{height:118px;padding:27px 20px 15px}
.drawer-app{font-size:20px}
.drawer-shift{font-size:13px;margin-top:3px}
'''
write(p,s)

print('V021_COMPACT_UI_PATCH_OK')
