from pathlib import Path

ROOT=Path('.')
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def write(p,s): (ROOT/p).write_text(s,encoding='utf-8')
def one(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'PATCH_FAIL {label}: expected 1 anchor, found {n}')
    return s.replace(old,new,1)

p='app/build.gradle'; s=read(p)
s=one(s,'versionCode 3','versionCode 4','versionCode')
s=one(s,"versionName '0.1.2'","versionName '0.1.3'",'versionName')
write(p,s)

p='app/src/main/java/pl/grafikzmian/app/MainActivity.java'; s=read(p)
s=s.replace('import android.app.BiometricPrompt;','import android.hardware.biometrics.BiometricPrompt;')
s=one(s,'private static final int REQ_SAVE = 4001, REQ_OPEN = 4002, REQ_NOTIF = 4003;', 'private static final int REQ_SAVE = 4001, REQ_OPEN = 4002, REQ_NOTIF = 4003, REQ_DAY_EDITOR = 4004;','request-code')
s=one(s,'    private boolean biometricInProgress = false;\n','    private boolean biometricInProgress = false;\n    private boolean nativeEditorInProgress = false;\n','editor-state')
s=one(s,'if (!biometricInProgress) pausedAt = System.currentTimeMillis();','if (!biometricInProgress && !nativeEditorInProgress) pausedAt = System.currentTimeMillis();','pause-guard')
s=one(s,'if (pageLoaded && !biometricInProgress && pausedAt > 0','if (pageLoaded && !biometricInProgress && !nativeEditorInProgress && pausedAt > 0','resume-guard')
s=s.replace('@JavascriptInterface public String getVersion() { return "0.1.2"; }','@JavascriptInterface public String getVersion() { return "0.1.3"; }')
anchor='        @JavascriptInterface public boolean canUseBiometrics() { return Build.VERSION.SDK_INT >= 28; }\n\n'
insert='''        @JavascriptInterface public boolean canUseBiometrics() { return Build.VERSION.SDK_INT >= 28; }\n\n        @JavascriptInterface public void openDayEditor(String dateKey, String dateLabel, String brigade, String shiftName, String shiftTime, String entryType, String note) {\n            runOnUiThread(() -> {\n                nativeEditorInProgress = true;\n                Intent i = new Intent(MainActivity.this, DayEditorActivity.class);\n                i.putExtra("dateKey", dateKey);\n                i.putExtra("dateLabel", dateLabel);\n                i.putExtra("brigade", brigade);\n                i.putExtra("shiftName", shiftName);\n                i.putExtra("shiftTime", shiftTime);\n                i.putExtra("entryType", entryType);\n                i.putExtra("note", note);\n                startActivityForResult(i, REQ_DAY_EDITOR);\n            });\n        }\n\n'''
s=one(s,anchor,insert,'editor-bridge')
old='''    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {\n        super.onActivityResult(requestCode, resultCode, data);\n        if (resultCode != RESULT_OK || data == null || data.getData() == null) return;\n        Uri uri = data.getData();\n        try {\n'''
new='''    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {\n        super.onActivityResult(requestCode, resultCode, data);\n        if (requestCode == REQ_DAY_EDITOR) {\n            nativeEditorInProgress = false;\n            if (resultCode == RESULT_OK && data != null) {\n                String key = data.getStringExtra("dateKey");\n                String type = data.getStringExtra("entryType");\n                String note = data.getStringExtra("note");\n                boolean deleted = data.getBooleanExtra("deleted", false);\n                js("window.onNativeDayEntrySaved&&window.onNativeDayEntrySaved("\n                        + JSONObject.quote(key == null ? "" : key) + ","\n                        + JSONObject.quote(type == null ? "plan" : type) + ","\n                        + JSONObject.quote(note == null ? "" : note) + ","\n                        + (deleted ? "true" : "false") + ")");\n            }\n            return;\n        }\n        if (resultCode != RESULT_OK || data == null || data.getData() == null) return;\n        Uri uri = data.getData();\n        try {\n'''
s=one(s,old,new,'activity-result')
write(p,s)

p='app/src/main/assets/www/app.js'; s=read(p)
anchor='  function entryFor(date){ return state.entries[keyOf(date)] || null; }\n\n'
insert='''  function entryFor(date){ return state.entries[keyOf(date)] || null; }\n  function openNativeDayEditor(date){\n    try {\n      if (typeof AndroidApp==='undefined' || typeof AndroidApp.openDayEditor!=='function') return false;\n      const sm=shiftMeta(shiftFor(date));\n      const en=entryFor(date)||{type:'plan',note:''};\n      const dateLabel=`${date.getDate()} ${MONTHS_GEN[date.getMonth()]} ${date.getFullYear()} · ${DAYS[date.getDay()]}`;\n      AndroidApp.openDayEditor(keyOf(date), dateLabel, state.brigade, sm.name, sm.time, en.type||'plan', en.note||'');\n      return true;\n    } catch { return false; }\n  }\n\n'''
s=one(s,anchor,insert,'js-native-open')
s=one(s,"document.querySelectorAll('[data-date]').forEach(b=>b.onclick=()=>{selectedDate=dateFromKey(b.dataset.date);screen='details';render();});", "document.querySelectorAll('[data-date]').forEach(b=>b.onclick=()=>{const d=dateFromKey(b.dataset.date);if(!openNativeDayEditor(d)){selectedDate=d;screen='details';render();}});",'js-date-bind')
anchor="  window.nativeBackupSaved=ok=>toast(ok?'Kopia zapisana':'Nie udało się zapisać kopii');\n"
insert='''  window.nativeBackupSaved=ok=>toast(ok?'Kopia zapisana':'Nie udało się zapisać kopii');\n  window.onNativeDayEntrySaved=(key,type,note,deleted)=>{\n    const cleanNote=String(note||'').trim();\n    if(deleted || (type==='plan' && !cleanNote)) delete state.entries[key];\n    else state.entries[key]={type:type||'plan',note:cleanNote};\n    save();\n    screen='calendar';\n    render();\n    toast(deleted?'Usunięto własny wpis':'Zapisano zmiany');\n  };\n'''
s=one(s,anchor,insert,'js-save-callback')
write(p,s)

p='app/src/main/AndroidManifest.xml'; s=read(p)
anchor='        <receiver android:name=".ReminderReceiver" android:exported="false" />\n'
insert='''        <activity\n            android:name=".DayEditorActivity"\n            android:exported="false"\n            android:screenOrientation="portrait"\n            android:windowSoftInputMode="adjustResize" />\n        <receiver android:name=".ReminderReceiver" android:exported="false" />\n'''
s=one(s,anchor,insert,'manifest-editor')
write(p,s)

java=ROOT/'app/src/main/java/pl/grafikzmian/app/DayEditorActivity.java'
java.write_text(r'''package pl.grafikzmian.app;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.ScrollView;
import android.widget.Space;
import android.widget.TextView;

public class DayEditorActivity extends Activity {
 private static final int BG=Color.rgb(246,249,252),SURFACE=Color.WHITE,TEXT=Color.rgb(7,17,41),MUTED=Color.rgb(96,112,143),LINE=Color.rgb(220,230,241),BLUE=Color.rgb(10,132,255),BLUE_SOFT=Color.rgb(231,242,255);
 private static final String[] TYPES={"plan","vacation","overtime","swap","sick","training"};
 private static final String[] LABELS={"Zgodnie z\ngrafikiem","Urlop","Nadgodziny","Zamiana","L4","Szkolenie"};
 private static final String[] SYMBOLS={"✓","☂","◷","⇄","✚","◇"};
 private String dateKey,selectedType,initialType,initialNote; private EditText note;
 private final LinearLayout[] cards=new LinearLayout[TYPES.length]; private final RadioButton[] radios=new RadioButton[TYPES.length];
 @Override protected void onCreate(Bundle state){super.onCreate(state);getWindow().setStatusBarColor(BG);getWindow().setNavigationBarColor(BG);if(Build.VERSION.SDK_INT>=23){int flags=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;if(Build.VERSION.SDK_INT>=26)flags|=View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;getWindow().getDecorView().setSystemUiVisibility(flags);}Intent in=getIntent();dateKey=value(in,"dateKey","");String dateLabel=value(in,"dateLabel","");String brigade=value(in,"brigade","A"),shiftName=value(in,"shiftName","Wolne"),shiftTime=value(in,"shiftTime","Dzień wolny");initialType=value(in,"entryType","plan");initialNote=value(in,"note","");selectedType=initialType;
  FrameLayout root=new FrameLayout(this);root.setBackgroundColor(BG);ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(dp(18),dp(16),dp(18),dp(28));scroll.addView(content,new ScrollView.LayoutParams(-1,-2));root.addView(scroll,new FrameLayout.LayoutParams(-1,-1));setContentView(root);root.setOnApplyWindowInsetsListener((v,ins)->{int l=0,t=0,r=0,b=0;if(Build.VERSION.SDK_INT>=30){android.graphics.Insets x=ins.getInsets(WindowInsets.Type.systemBars());l=x.left;t=x.top;r=x.right;b=x.bottom;}else{l=ins.getSystemWindowInsetLeft();t=ins.getSystemWindowInsetTop();r=ins.getSystemWindowInsetRight();b=ins.getSystemWindowInsetBottom();}root.setPadding(l,t,r,b);return ins;});root.requestApplyInsets();
  LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);Button back=new Button(this);back.setText("‹");back.setTextSize(34);back.setTextColor(MUTED);back.setAllCaps(false);back.setBackground(round(SURFACE,LINE,16,1));header.addView(back,new LinearLayout.LayoutParams(dp(48),dp(48)));TextView title=text("Szczegóły dnia",24,TEXT,true);title.setGravity(Gravity.CENTER);header.addView(title,new LinearLayout.LayoutParams(0,dp(48),1));header.addView(new Space(this),new LinearLayout.LayoutParams(dp(48),dp(48)));content.addView(header);back.setOnClickListener(v->finish());TextView date=text(dateLabel,15,MUTED,false);date.setGravity(Gravity.CENTER);LinearLayout.LayoutParams dl=new LinearLayout.LayoutParams(-1,-2);dl.topMargin=dp(12);dl.bottomMargin=dp(18);content.addView(date,dl);
  LinearLayout shift=new LinearLayout(this);shift.setOrientation(LinearLayout.VERTICAL);shift.setPadding(dp(20),dp(18),dp(20),dp(18));shift.setBackground(round(SURFACE,LINE,18,1));shift.addView(text("Brygada "+brigade+" · grafik bazowy",14,MUTED,false));shift.addView(text(shiftName,28,TEXT,true));shift.addView(text(shiftTime,19,TEXT,false));content.addView(shift,new LinearLayout.LayoutParams(-1,-2));TextView sec=text("Twój wpis",22,TEXT,true);LinearLayout.LayoutParams sl=new LinearLayout.LayoutParams(-1,-2);sl.topMargin=dp(22);sl.bottomMargin=dp(10);content.addView(sec,sl);
  GridLayout grid=new GridLayout(this);grid.setColumnCount(2);for(int i=0;i<TYPES.length;i++){final int idx=i;LinearLayout card=new LinearLayout(this);card.setGravity(Gravity.CENTER_VERTICAL);card.setPadding(dp(13),dp(12),dp(10),dp(12));TextView sym=text(SYMBOLS[i],25,TEXT,true);sym.setGravity(Gravity.CENTER);card.addView(sym,new LinearLayout.LayoutParams(dp(36),-1));TextView lab=text(LABELS[i],15,TEXT,true);card.addView(lab,new LinearLayout.LayoutParams(0,-2,1));RadioButton rb=new RadioButton(this);rb.setClickable(false);rb.setFocusable(false);card.addView(rb,new LinearLayout.LayoutParams(dp(40),dp(40)));cards[i]=card;radios[i]=rb;card.setOnClickListener(v->select(idx));GridLayout.LayoutParams gp=new GridLayout.LayoutParams();gp.width=0;gp.height=dp(82);gp.columnSpec=GridLayout.spec(GridLayout.UNDEFINED,1f);gp.setMargins(dp(4),dp(4),dp(4),dp(4));grid.addView(card,gp);}content.addView(grid,new LinearLayout.LayoutParams(-1,-2));select(indexOf(initialType));
  LinearLayout nc=new LinearLayout(this);nc.setOrientation(LinearLayout.VERTICAL);nc.setPadding(dp(14),dp(13),dp(14),dp(14));nc.setBackground(round(SURFACE,LINE,16,1));nc.addView(text("Notatka",15,TEXT,true));note=new EditText(this);note.setText(initialNote);note.setTextSize(16);note.setTextColor(TEXT);note.setHintTextColor(Color.rgb(130,140,155));note.setHint("Dodaj informację do tego dnia…");note.setGravity(Gravity.TOP|Gravity.START);note.setPadding(dp(12),dp(12),dp(12),dp(12));note.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_CAP_SENTENCES|InputType.TYPE_TEXT_FLAG_MULTI_LINE);note.setSingleLine(false);note.setMinLines(4);note.setBackground(round(Color.rgb(248,251,255),LINE,12,1));LinearLayout.LayoutParams nl=new LinearLayout.LayoutParams(-1,dp(120));nl.topMargin=dp(9);nc.addView(note,nl);LinearLayout.LayoutParams ncl=new LinearLayout.LayoutParams(-1,-2);ncl.topMargin=dp(14);content.addView(nc,ncl);
  Button save=new Button(this);save.setText("Zapisz zmiany");save.setTextColor(Color.WHITE);save.setTextSize(17);save.setTypeface(Typeface.DEFAULT,Typeface.BOLD);save.setAllCaps(false);save.setBackground(round(BLUE,BLUE,14,0));LinearLayout.LayoutParams sv=new LinearLayout.LayoutParams(-1,dp(54));sv.topMargin=dp(16);content.addView(save,sv);save.setOnClickListener(v->finishResult(false));if(!"plan".equals(initialType)||!initialNote.trim().isEmpty()){Button del=new Button(this);del.setText("Usuń własny wpis");del.setTextColor(BLUE);del.setTextSize(15);del.setAllCaps(false);del.setBackground(round(BLUE_SOFT,BLUE_SOFT,14,0));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(48));lp.topMargin=dp(9);content.addView(del,lp);del.setOnClickListener(v->finishResult(true));}}
 private void select(int idx){if(idx<0)idx=0;selectedType=TYPES[idx];for(int i=0;i<TYPES.length;i++){boolean on=i==idx;radios[i].setChecked(on);cards[i].setBackground(round(on?BLUE_SOFT:SURFACE,on?BLUE:LINE,14,on?2:1));}}
 private int indexOf(String type){for(int i=0;i<TYPES.length;i++)if(TYPES[i].equals(type))return i;return 0;}
 private void finishResult(boolean deleted){Intent out=new Intent();out.putExtra("dateKey",dateKey);out.putExtra("entryType",deleted?"plan":selectedType);out.putExtra("note",deleted?"":note.getText().toString());out.putExtra("deleted",deleted);setResult(RESULT_OK,out);finish();}
 private String value(Intent i,String k,String d){String v=i.getStringExtra(k);return v==null?d:v;} private int dp(int x){return Math.round(x*getResources().getDisplayMetrics().density);} private TextView text(String s,int sp,int c,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextSize(sp);t.setTextColor(c);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;} private GradientDrawable round(int fill,int stroke,int radius,int width){GradientDrawable g=new GradientDrawable();g.setColor(fill);g.setCornerRadius(dp(radius));if(width>0)g.setStroke(dp(width),stroke);return g;}
}
''',encoding='utf-8')

print('V013_NATIVE_EDITOR_PATCH_OK')
