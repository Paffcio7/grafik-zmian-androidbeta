from pathlib import Path
import re

ROOT=Path('.')
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def write(p,s): (ROOT/p).write_text(s,encoding='utf-8')
def one(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'PATCH_FAIL {label}: expected 1 anchor, found {n}')
    return s.replace(old,new,1)

p='app/build.gradle'; s=read(p)
s=one(s,'versionCode 11','versionCode 12','versionCode')
s=one(s,"versionName '0.2.6'","versionName '0.2.7'",'versionName')
write(p,s)

p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
if '0.2.6' not in s: raise SystemExit('PATCH_FAIL MainActivity version anchor missing')
s=s.replace('0.2.6','0.2.7')
# Diagnostic: locate the real system-bar/native bridge implementation in the frozen source.
candidates=list(re.finditer(r'\b(?:void|boolean|String)\s+([A-Za-z0-9_]*(?:Bar|bar|System|system|Theme|theme)[A-Za-z0-9_]*)\s*\(',s))
print('V027_NATIVE_CANDIDATES_START')
for mm in candidates:
    a=max(0,s.rfind('\n',0,mm.start())-180); b=min(len(s),s.find('\n',mm.end())+220)
    print(s[a:b].replace('\n','\\n'))
print('V027_NATIVE_CANDIDATES_END')
m=re.search(r'((?:public|private|protected)?\s*void\s+setSystemBars\s*\(\s*boolean\s+dark\s*\)\s*\{)',s)
if not m: raise SystemExit('PATCH_FAIL setSystemBars(boolean dark) bridge not found')
