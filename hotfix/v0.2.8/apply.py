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
s=one(s,'versionCode 12','versionCode 13','versionCode')
s=one(s,"versionName '0.2.7'","versionName '0.2.8'",'versionName')
write(p,s)

# Android system bar readability. On Samsung/Android 16 the status-bar surface can stay
# light even if setStatusBarColor is ignored by edge-to-edge enforcement, so icon
# appearance must follow the actual app theme instead of being forced white.
p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
if '0.2.7' not in s: raise SystemExit('PATCH_FAIL MainActivity version anchor missing')
s=s.replace('0.2.7','0.2.8')
s=one(s,
'        getWindow().setStatusBarColor(Color.parseColor("#164BB7"));',
'        getWindow().setStatusBarColor(Color.parseColor(dark ? "#0B1118" : "#F4F7FA"));',
'status-bar-color')
s=one(s,
'        flags &= ~android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;',
'''        if(!dark) flags |= android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
        else flags &= ~android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;''',
'legacy-status-icon-appearance')
s=one(s,
'                controller.setSystemBarsAppearance(0,android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS);',
'''                controller.setSystemBarsAppearance(
                    dark ? 0 : android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS,
                    android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
                );''',
'api30-status-icon-appearance')
write(p,s)

p='app/src/main/assets/www/app.js'; s=read(p)
s=one(s,'Kalendarz zmian · v0.2.7','Kalendarz zmian · v0.2.8','drawer-version')
write(p,s)

print('V028_READABLE_STATUS_BAR_OK')
