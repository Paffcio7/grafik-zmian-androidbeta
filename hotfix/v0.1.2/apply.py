from pathlib import Path
import re

ROOT = Path('.')

def read(rel): return (ROOT / rel).read_text(encoding='utf-8')
def write(rel, s): (ROOT / rel).write_text(s, encoding='utf-8')
def one(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'PATCH_FAIL {label}: expected 1 anchor, found {n}')
    return s.replace(old, new, 1)

# Package identity.
rel='app/build.gradle'; s=read(rel)
s=one(s, 'versionCode 2', 'versionCode 3', 'versionCode')
s=one(s, "versionName '0.1.1'", "versionName '0.1.2'", 'versionName')
write(rel,s)

# Android WebView focus. This complements the v0.1.1 system-bar inset fix.
rel='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(rel)
s=s.replace('import android.app.BiometricPrompt;', 'import android.hardware.biometrics.BiometricPrompt;')
if 'webView.setFocusableInTouchMode(true);' not in s:
    s=one(s, '        webView = new WebView(this);\n',
          '        webView = new WebView(this);\n        webView.setFocusable(true);\n        webView.setFocusableInTouchMode(true);\n', 'webview-focusable')
if 'webView.setOnTouchListener' not in s:
    s=one(s, '        webView.addJavascriptInterface(new NativeBridge(), "AndroidApp");\n',
          '        webView.addJavascriptInterface(new NativeBridge(), "AndroidApp");\n        webView.setOnTouchListener((v, event) -> {\n            if (!v.hasFocus()) v.requestFocus();\n            return false;\n        });\n', 'webview-touch-focus')
if 'webView.requestFocus(View.FOCUS_DOWN);' not in s:
    if '        root.requestApplyInsets();\n' in s:
        s=one(s, '        root.requestApplyInsets();\n', '        root.requestApplyInsets();\n        webView.requestFocus(View.FOCUS_DOWN);\n', 'request-focus')
    else:
        s=one(s, '        webView.loadUrl("file:///android_asset/www/index.html");\n', '        webView.requestFocus(View.FOCUS_DOWN);\n        webView.loadUrl("file:///android_asset/www/index.html");\n', 'request-focus-fallback')
s=s.replace('@JavascriptInterface public String getVersion() { return "0.1.1"; }', '@JavascriptInterface public String getVersion() { return "0.1.2"; }')
write(rel,s)

# Use actual HTML radio inputs/labels on the day-details screen instead of custom-only click handlers.
rel='app/src/main/assets/www/app.js'; s=read(rel)
old = """    const options=Object.entries(ENTRY_TYPES).map(([k,v])=>`<button class=\"entry-option ${editingEntry.type===k?'selected':''}\" data-entry-type=\"${k}\"><div class=\"entry-symbol\">${v.symbol}</div><div class=\"entry-name\">${v.label}</div><span class=\"radio\"></span></button>`).join('');"""
new = """    const options=Object.entries(ENTRY_TYPES).map(([k,v])=>`<label class=\"entry-option ${editingEntry.type===k?'selected':''}\" data-entry-option for=\"entry-${k}\">\n        <input class=\"entry-input\" type=\"radio\" name=\"entry-type\" id=\"entry-${k}\" value=\"${k}\" ${editingEntry.type===k?'checked':''} />\n        <div class=\"entry-symbol\">${v.symbol}</div><div class=\"entry-name\">${v.label}</div><span class=\"radio\"></span>\n      </label>`).join('');"""
s=one(s, old, new, 'detail-options')
s=one(s,
      '<div class="note-box"><label>Notatka</label><textarea id="entry-note" placeholder="Dodaj informację do tego dnia…">${esc(editingEntry.note||\'\')}</textarea></div>',
      '<div class="note-box"><label for="entry-note">Notatka</label><textarea id="entry-note" placeholder="Dodaj informację do tego dnia…" autocomplete="off" autocapitalize="sentences"></textarea></div>',
      'detail-note')
s=one(s,
      "    document.querySelectorAll('[data-entry-type]').forEach(b=>b.onclick=()=>{editingEntry.type=b.dataset.entryType;document.querySelectorAll('[data-entry-type]').forEach(x=>x.classList.toggle('selected',x.dataset.entryType===editingEntry.type));});\n",
      "    const noteEl=document.getElementById('entry-note');\n    if(noteEl && editingEntry) noteEl.value=editingEntry.note||'';\n    document.querySelectorAll('.entry-input').forEach(input=>{\n      input.addEventListener('change',()=>{\n        editingEntry.type=input.value;\n        document.querySelectorAll('[data-entry-option]').forEach(x=>{\n          const radio=x.querySelector('.entry-input');\n          x.classList.toggle('selected',!!radio?.checked);\n        });\n      });\n    });\n",
      'detail-bind')
s=one(s,
      "  function saveEntry(){\n    const key=keyOf(selectedDate); editingEntry.note=document.getElementById('entry-note')?.value.trim()||'';\n",
      "  function saveEntry(){\n    const key=keyOf(selectedDate);\n    const checked=document.querySelector('input[name=\"entry-type\"]:checked');\n    editingEntry.type=checked?.value || editingEntry.type || 'plan';\n    editingEntry.note=(document.getElementById('entry-note')?.value || '').trim();\n",
      'save-entry')
write(rel,s)

# Touch-safe visual radio controls and editable textarea.
rel='app/src/main/assets/www/styles.css'; s=read(rel)
old='.entry-option{min-height:75px;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px;display:flex;align-items:center;gap:10px;position:relative}.entry-option.selected{border:2px solid var(--blue);padding:11px;background:var(--blue-soft)}.entry-option .entry-symbol{font-size:25px;width:31px;text-align:center}.entry-option .entry-name{font-size:14px;font-weight:720}.radio{margin-left:auto;width:20px;height:20px;border-radius:50%;border:1.5px solid var(--muted);display:grid;place-items:center}.selected .radio{border-color:var(--blue);background:var(--blue)}.selected .radio::after{content:"✓";color:white;font-size:12px;font-weight:900}'
new='.entry-option{min-height:75px;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px;display:flex;align-items:center;gap:10px;position:relative;cursor:pointer;touch-action:manipulation;-webkit-user-select:none;user-select:none}.entry-option.selected{border:2px solid var(--blue);padding:11px;background:var(--blue-soft)}.entry-option .entry-symbol{font-size:25px;width:31px;text-align:center}.entry-option .entry-name{font-size:14px;font-weight:720}.entry-input{position:absolute;opacity:0;pointer-events:none;width:1px;height:1px}.radio{margin-left:auto;width:20px;height:20px;border-radius:50%;border:1.5px solid var(--muted);display:grid;place-items:center;flex:0 0 auto}.selected .radio{border-color:var(--blue);background:var(--blue)}.selected .radio::after{content:"✓";color:white;font-size:12px;font-weight:900}'
s=one(s, old, new, 'entry-css')
s=one(s,
      '.note-box textarea{width:100%;height:84px;resize:none;border:1px solid var(--line);background:var(--surface2);border-radius:11px;padding:11px;outline:none}.note-box textarea:focus{border-color:var(--blue)}',
      '.note-box textarea{width:100%;height:84px;resize:none;border:1px solid var(--line);background:var(--surface2);border-radius:11px;padding:11px;outline:none;-webkit-user-select:text;user-select:text;pointer-events:auto}.note-box textarea:focus{border-color:var(--blue);background:var(--surface)}',
      'note-css')
write(rel,s)

# Keyboard must resize the activity, not cover the textarea/actions.
rel='app/src/main/AndroidManifest.xml'; s=read(rel)
if 'android:windowSoftInputMode="adjustResize"' not in s:
    s=one(s, 'android:screenOrientation="portrait">', 'android:screenOrientation="portrait"\n            android:windowSoftInputMode="adjustResize">', 'adjustResize')
write(rel,s)

print('V012_PATCH_OK')
