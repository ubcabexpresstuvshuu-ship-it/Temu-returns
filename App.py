# -*- coding: utf-8 -*-
from flask import Flask, Response, request, redirect, url_for, session
import re, os, json, time

app = Flask(__name__)
app.secret_key = os.environ.get("TEMU_SECRET_KEY", "change_me_2025")

# -----------------------
# SIMPLE IN-MEMORY USERS
# -----------------------
# Админ ба жишээ жолооч. (Render free дээр email илгээхгүй тул reset-ийг form-оор шийднэ)
USERS = {
    "admin@ubcab.mn": {"role": "admin", "name": "Admin", "password": "temu2025"},
    "99112233": {"role": "driver", "name": "Demo Driver", "password": "1234", "district": "Хан-Уул"},
}

# Дүүргийн жагсаалт (Улаанбаатар + Алс дүүргүүд)
DISTRICTS = ['Баянзүрх','Баянгол','Хан-Уул','Сүхбаатар','Чингэлтэй','Сонгинохайрхан','Налайх','Багануур','Багахангай']

def is_phone(s): return re.fullmatch(r"\d{6,12}", str(s or "")) is not None

def login_required(fn):
    def w(*a, **k):
        if not session.get("user"):
            return redirect(url_for("login"))
        return fn(*a, **k)
    w.__name__ = fn.__name__
    return w

# ---------- Shared tabs ----------
def top_nav(active, role):
    def tab(label, href, key):
        cls = 'class="tab active"' if key == active else 'class="tab"'
        if role == "driver" and key == "admin":
            return f'<span {cls} title="Админ эрх шаардлагатай">{label}</span>'
        return f'<a {cls} href="{href}">{label}</a>'
    return f"""
    <div class="tabs">
      {tab("Жолооч", "/", "driver")}
      {tab("Админ", "/admin", "admin")}
    </div>
    """

def bottom_nav(active, role):
    def tab(label, href, key):
        cls = 'class="btab active"' if key == active else 'class="btab"'
        if role == "driver" and key == "admin":
            return f'<span {cls} title="Админ эрх шаардлагатай">{label}</span>'
        return f'<a {cls} href="{href}">{label}</a>'
    return f"""
    <div class="bottombar">
      {tab("Жолооч", "/", "driver")}
      {tab("Админ", "/admin", "admin")}
    </div>
    """

# ================= LOGIN / REGISTER / RESET =================
LOGIN_HTML = """<!doctype html><html lang="mn"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Тэмү Буцаалт — Нэвтрэх</title>
<style>
body{margin:0;background:#f8fafc;font-family:Inter,system-ui,Segoe UI,Roboto,Arial;color:#0f172a}
.wrap{min-height:100vh;display:grid;place-items:center}
.card{width:min(420px,92vw);background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:24px;box-shadow:0 10px 30px rgba(2,6,23,.06)}
h1{font-size:22px;margin:0 0 12px;font-weight:800}
label{display:block;margin:10px 0 4px;font-weight:600}
input{width:100%;border:1px solid #e5e7eb;border-radius:10px;padding:12px;font:inherit}
button{width:100%;margin-top:14px;background:#ff6a00;color:#fff;border:none;border-radius:10px;padding:12px;font:inherit;font-weight:700;cursor:pointer}
.muted{color:#64748b;font-size:12px;margin-top:10px}
.err{background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;padding:8px 10px;border-radius:8px;margin-bottom:10px}
a.link{display:inline-block;margin-top:8px}
</style></head><body>
<div class="wrap"><form class="card" method="post">
  <h1>Тэмү Буцаалт</h1>
  <div class="muted">Админ: email / Жолооч: утасны дугаар</div>
  {error}
  <label>Имэйл эсвэл утасны дугаар</label><input name="id" required placeholder="admin@ubcab.mn эсвэл 99112233">
  <label>Нууц үг</label><input name="password" type="password" required placeholder="temu2025 эсвэл 1234">
  <button type="submit">Нэвтрэх</button>
  <a class="link" href="/register">Жолооч бүртгүүлэх</a> ·
  <a class="link" href="/forgot">Нууц үг мартсан</a>
</form></div></body></html>"""

REGISTER_HTML = """<!doctype html><html lang="mn"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Жолооч бүртгэл</title>
<style>
body{margin:0;background:#f8fafc;font-family:Inter,system-ui,Segoe UI,Roboto,Arial;color:#0f172a}
.wrap{min-height:100vh;display:grid;place-items:center}
.card{width:min(460px,92vw);background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:24px;box-shadow:0 10px 30px rgba(2,6,23,.06)}
h1{font-size:22px;margin:0 0 12px;font-weight:800}
label{display:block;margin:10px 0 4px;font-weight:600}
input,select{width:100%;border:1px solid #e5e7eb;border-radius:10px;padding:12px;font:inherit}
button{width:100%;margin-top:14px;background:#0f172a;color:#fff;border:none;border-radius:10px;padding:12px;font:inherit;font-weight:700;cursor:pointer}
.err{background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;padding:8px 10px;border-radius:8px;margin-bottom:10px}
.ok{background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;padding:8px 10px;border-radius:8px;margin-bottom:10px}
a{display:inline-block;margin-top:8px}
</style></head><body>
<div class="wrap"><form class="card" method="post">
  <h1>Жолооч бүртгэл</h1>
  {error}{ok}
  <label>Нэр</label><input name="name" required>
  <label>Утасны дугаар</label><input name="phone" required pattern="\\d{6,12}">
  <label>Нууц үг</label><input name="password" type="password" required>
  <label>Дүүрэг</label>
  <select name="district" required>{opts}</select>
  <button type="submit">Бүртгүүлэх</button>
  <a href="/login">Буцах (нэвтрэх)</a>
</form></div></body></html>"""

FORGOT_HTML = """<!doctype html><html lang="mn"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Нууц үг сэргээх</title>
<style>
body{margin:0;background:#f8fafc;font-family:Inter,system-ui,Segoe UI,Roboto,Arial;color:#0f172a}
.wrap{min-height:100vh;display:grid;place-items:center}
.card{width:min(420px,92vw);background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:24px;box-shadow:0 10px 30px rgba(2,6,23,.06)}
label{display:block;margin:10px 0 4px;font-weight:600}
input,button{width:100%;border:1px solid #e5e7eb;border-radius:10px;padding:12px;font:inherit}
button{margin-top:12px;background:#ff6a00;color:#fff;border:none;font-weight:700;cursor:pointer}
.err{background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;padding:8px 10px;border-radius:8px;margin-bottom:10px}
.ok{background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;padding:8px 10px;border-radius:8px;margin-bottom:10px}
</style></head><body>
<div class="wrap"><form class="card" method="post">
  <h2>Нууц үг сэргээх (Жолооч)</h2>
  {error}{ok}
  <label>Таны бүртгэсэн утасны дугаар</label>
  <input name="phone" required pattern="\\d{6,12}" placeholder="99112233">
  <label>Шинэ нууц үг</label><input name="password1" type="password" required>
  <label>Шинэ нууц үг (давт)</label><input name="password2" type="password" required>
  <button type="submit">Сэргээх</button>
  <a style="display:inline-block;margin-top:8px" href="/login">Буцах (нэвтрэх)</a>
</form></div></body></html>"""

# ================ ADMIN ================
# Admin тал нь өгөгдлийг ДҮҮРГЭЭР ТУС ТУСАД НЬ хадгалдаг (localStorage key: ret_data__<district>)
ADMIN_HTML = """<!doctype html><html lang="mn"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Буцаалтын Захиалгууд — Админ</title>
<style>
:root{--brand:#ff6a00;--line:#e5e7eb}
*{box-sizing:border-box}
body{font-family:Inter,system-ui;background:#f8fafc;margin:0;color:#0f172a}
header{background:var(--brand);color:#fff;padding:12px 16px;display:flex;justify-content:center;align-items:center}
header a{color:#fff;text-decoration:underline;margin-left:8px}
main{max-width:1200px;margin:0 auto;padding:14px}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px;margin:10px 0}
input,select,button,textarea{border:1px solid var(--line);border-radius:10px;padding:10px;font:inherit}
.btn{background:var(--brand);border-color:transparent;color:#fff;font-weight:700;cursor:pointer}
table{width:100%;border-collapse:collapse;margin-top:8px}
th,td{border:1px solid #e5e7eb;padding:8px;text-align:left;vertical-align:top}
th{background:#f8fafc}
.tabs{display:flex;gap:8px;justify-content:center;background:#fff5ee;border-bottom:1px solid #ffd8bf}
.tab{padding:8px 14px;border-radius:999px}
.tab.active{background:#ff6a00;color:#fff}
.tab:not(.active){color:#0f172a}
.bottombar{position:sticky;bottom:0;background:#fff;display:flex;gap:8px;justify-content:center;padding:8px;border-top:1px solid #e5e7eb}
.btab{padding:10px 16px;border:1px solid #e5e7eb;border-radius:12px;background:#fff}
.btab.active{background:#ff6a00;border-color:#ff6a00;color:#fff}
.mini{font-size:12px;color:#64748b}
</style></head><body>
<header>Админ — <a href="/logout">Гарах</a></header>
{tabs_top}
<main>

<div class="card">
  <h3>Лист импорт</h3>
  <p>Copy-Paste эсвэл Excel (.xlsx). Баганууд: <b>Tracking, Утас, Хаяг, Хаяг2, Авсан(0/1), Татгалзсан(0/1), Дүүрэг</b></p>
  <div style="display:flex;gap:8px;flex-wrap:wrap">
    <input type="file" id="xlsxInput" accept=".xlsx">
    <select id="districtAssign"><option value="">→ Импортод оноох дүүрэг (заавал)</option></select>
    <select id="districtFilter"><option value="">Харагдахыг шүүх (бүгд)</option></select>
    <button class="btn" id="clearDoneAll" style="background:#dc2626">Бүх “Авсан”-г устгах</button>
    <button class="btn" id="wipeActive" style="background:#0f172a">Идэвхтэй листийг бүрэн устгах</button>
  </div>
  <textarea id="pasteBox" placeholder="UBC123, 99112233, Хаяг1, Хаяг2, 0, 0" style="margin-top:8px;min-height:120px;width:100%"></textarea>
  <div style="display:flex;gap:8px;margin-top:8px">
    <button class="btn" id="importPaste">Copy-Paste импорт</button>
    <button id="purgeNow">⏳ Одоо 48 цагийн шалгалт</button>
  </div>
  <div class="mini">Импорт хийсэн мөр бүр <b>48 цагийн дараа</b> автоматаар “Автоматаар устсан” хэсэгт шилжинэ.</div>
</div>

<div class="card">
  <h3>Идэвхтэй жагсаалт</h3>
  <table><thead>
    <tr><th>#</th><th>Tracking</th><th>Утас</th><th>Хаяг</th><th>Хаяг 2</th><th>Дүүрэг</th><th>Авсан</th><th>Татгалзсан</th><th>Жолооч</th><th>Оруулсан</th></tr>
  </thead><tbody id="rowsActive"></tbody></table>
</div>

<div class="card">
  <h3>Автоматаар устсан (48 цаг)</h3>
  <table><thead>
    <tr><th>#</th><th>Tracking</th><th>Утас</th><th>Хаяг</th><th>Хаяг 2</th><th>Дүүрэг</th><th>Жолооч</th><th>Оруулсан</th><th>Устсан</th></tr>
  </thead><tbody id="rowsExpired"></tbody></table>
</div>

</main>
{tabs_bottom}
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
<script>
const $=s=>document.querySelector(s);
// -------------- ТҮЛХҮҮР: дүүрэг тус бүр тусдаа storage --------------
const LS={ DATA_PREFIX:'ret_data__', EXPIRED_PREFIX:'ret_expired__', DONE_PREFIX:'ret_done__', REF_PREFIX:'ret_ref__' };
const DISTRICTS={list: %DISTLIST%};
const DAY48=48*60*60*1000;

function keyForData(d){ return LS.DATA_PREFIX + d; }
function keyForExpired(d){ return LS.EXPIRED_PREFIX + d; }

function load(d){ return JSON.parse(localStorage.getItem(keyForData(d))||'[]'); }
function save(d,rows){ localStorage.setItem(keyForData(d), JSON.stringify(rows)); window.dispatchEvent(new Event('storage')); }
function loadExpired(d){ return JSON.parse(localStorage.getItem(keyForExpired(d))||'[]'); }
function saveExpired(d,rows){ localStorage.setItem(keyForExpired(d), JSON.stringify(rows)); window.dispatchEvent(new Event('storage')); }

function optDistrictSelects(){
  const opts = '<option value=\"\">→ Импортод оноох дүүрэг (заавал)</option>'+DISTRICTS.list.map(d=>`<option>${d}</option>`).join('');
  $('#districtAssign').innerHTML = opts;
  $('#districtFilter').innerHTML = '<option value=\"\">Харагдахыг шүүх (бүгд)</option>'+DISTRICTS.list.map(d=>`<option>${d}</option>`).join('');
}

function onlyDigits(s){ return String(s||'').replace(/\\D/g,''); }
function looksPhone(s){ const d=onlyDigits(s); return d.length>=6 && d.length<=12; }

function normalizeParts(parts) {
  parts = parts.map(s=>{
    s = (s||'').trim();
    if (s.startsWith('\"') && s.endsWith('\"')) s = s.slice(1, -1).replace(/\"\"/g, '\"');
    return s;
  });

  if (parts.length > 7) {
    const last3 = parts.slice(-3);
    const head  = parts.slice(0, parts.length - 3);
    const id = (head.shift()||'').trim();

    let phone = '';
    let pIdx = head.findIndex(x=>looksPhone(x));
    if (pIdx >= 0) phone = head.splice(pIdx, 1)[0];

    const addrJoin = head.join(', ').trim();
    let addr1 = addrJoin, addr2 = '';
    if (addrJoin.length > 60) {
      const mid = Math.floor(addrJoin.length/2);
      const cut = addrJoin.indexOf(' ', mid);
      if (cut > 0) {
        addr1 = addrJoin.slice(0, cut).trim();
        addr2 = addrJoin.slice(cut).trim();
      }
    }
    parts = [id, phone, addr1, addr2, ...last3];
  }
  while (parts.length < 7) parts.push('');
  return parts.slice(0,7);
}

function parsePaste(text){
  return text.split(/\\r?\\n/).map(line=>{
    if (!line.trim()) return null;
    let parts = line.split('\\t');
    if (parts.length < 7) {
      parts = line.match(/(\"([^\"]|\"\")*\"|[^,]+)/g) || [line];
    }
    return normalizeParts(parts);
  }).filter(Boolean);
}

function importXlsx(file, assign){
  const fr=new FileReader();
  fr.onload=e=>{
    const wb=XLSX.read(new Uint8Array(e.target.result),{type:'array'});
    const ws=wb.Sheets[wb.SheetNames[0]];
    const raw=XLSX.utils.sheet_to_json(ws,{header:1,defval:''});
    const rows = raw.filter(r=>r && (r[0]||'').toString().trim() !== '')
                    .map(r=>normalizeParts(r));
    importRows(rows, assign);
  };
  fr.readAsArrayBuffer(file);
}

function normRow(a){
  const arr = Array.isArray(a) ? a : [];
  const id   = (arr[0]||'').toString().trim();
  let   phone= (arr[1]||'').toString().trim();
  if (!looksPhone(phone)) phone = onlyDigits(phone);
  const addr1= (arr[2]||'').toString().trim();
  const addr2= (arr[3]||'').toString().trim();
  const picked = String(arr[4]||'0').trim();
  const refused= String(arr[5]||'0').trim();
  return {
    id, phone, address: addr1, address2: addr2,
    picked: (picked=='1' || picked.toLowerCase()=='true'),
    refused:(refused=='1' || refused.toLowerCase()=='true'),
    driverPhone:'', created: Date.now(), deletedAt:0
  };
}

function importRows(rows, assign){
  if(!assign){ alert('Импорт хийхийн өмнө “→ Импортод оноох дүүрэг”-ээ сонгоно уу.'); return; }
  const now = Date.now();
  const cur = load(assign);
  rows.forEach(r=>{
    const o = normRow(r);
    o.created = now;
    cur.push(o);
  });
  save(assign, cur);
  render();
}

function purge48h(assign){
  const now=Date.now(); let rows=load(assign); let expired=loadExpired(assign); const keep=[];
  rows.forEach(r=>{
    if(now - (r.created || now) >= DAY48){ r.deletedAt = now; expired.push(r); }
    else keep.push(r);
  });
  save(assign, keep); saveExpired(assign, expired);
}

function wipeActiveAll(assign){
  if(!assign){alert('Шилжүүлэх дүүргээ сонгоно.'); return;}
  if(!confirm('Идэвхтэй бүх мөрийг “Автоматаар устсан” руу шилжүүлэх үү?')) return;
  const now=Date.now(); let rows=load(assign); let expired=loadExpired(assign);
  rows.forEach(r=>{ r.deletedAt=now; expired.push(r); });
  save(assign, []); saveExpired(assign, expired); render();
}
function fmt(ts){ return new Date(ts || Date.now()).toLocaleString(); }

function render(){
  optDistrictSelects();
  const f=($('#districtFilter').value||'').trim();
  const show = f || DISTRICTS.list[0];

  purge48h(show);

  const active = load(show);
  const ex = loadExpired(show);

  const A=$('#rowsActive'); A.innerHTML='';
  active.forEach((r,i)=>{
    A.innerHTML += `<tr><td>${i+1}</td><td>${r.id}</td><td>${r.phone}</td><td>${r.address}</td><td>${r.address2||''}</td>
    <td>${show}</td><td>${r.picked?'✓':''}</td><td>${r.refused?'✓':''}</td>
    <td>${r.driverPhone||''}</td><td>${fmt(r.created)}</td></tr>`;
  });

  const B=$('#rowsExpired'); B.innerHTML='';
  ex.forEach((r,i)=>{
    B.innerHTML += `<tr><td>${i+1}</td><td>${r.id}</td><td>${r.phone}</td><td>${r.address}</td><td>${r.address2||''}</td>
    <td>${show}</td><td>${r.driverPhone||''}</td><td>${fmt(r.created)}</td><td>${fmt(r.deletedAt)}</td></tr>`;
  });
}

document.addEventListener('DOMContentLoaded',()=>{
  render();
  $('#importPaste').onclick=()=>{ const t=$('#pasteBox').value.trim(); const assign=$('#districtAssign').value.trim(); if(!t){alert('Paste хоосон'); return;} importRows(parsePaste(t), assign); };
  $('#xlsxInput').onchange=e=>{ const f=e.target.files[0]; const assign=$('#districtAssign').value.trim(); if(f) importXlsx(f, assign); };
  $('#districtFilter').onchange=render;
  $('#purgeNow').onclick=()=>{ const d=$('#districtFilter').value.trim()||DISTRICTS.list[0]; purge48h(d); render(); };
  $('#clearDoneAll').onclick=()=>{
    if(!confirm('Бүх жолоочийн “Авсан/Татгалзсан” тэмдэглэлийг устгах уу?')) return;
    Object.keys(localStorage).forEach(k=>{ if(k.startsWith(LS.DONE_PREFIX) || k.startsWith(LS.REF_PREFIX)) localStorage.removeItem(k); });
    alert('“Авсан/Татгалзсан” тэмдэглэлүүд устлаа.');
  };
  $('#wipeActive').onclick=()=>{ const d=$('#districtFilter').value.trim()||DISTRICTS.list[0]; wipeActiveAll(d); };
});

window.addEventListener('storage', render);
</script></body></html>
"""

# ================ DRIVER =================
# Жолооч бүр зөвхөн өөрийн дүүргийн листийг харна (storage key нь ret_data__<district>)
DRIVER_HTML = """<!doctype html><html lang="mn"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Тэмү Буцаалт — Жолооч</title>
<style>
:root{--brand:#ff6a00;--line:#e5e7eb;--alert:#fee2e2;--alertText:#991b1b}
*{box-sizing:border-box}
body{font-family:Inter,system-ui;background:#f8fafc;margin:0;color:#0f172a}
header{background:var(--brand);color:#fff;padding:12px 16px;display:flex;justify-content:center;align-items:center}
header a{color:#fff;text-decoration:underline;margin-left:8px}
main{max-width:1100px;margin:0 auto;padding:14px}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px;margin:10px 0}
.row{display:flex;gap:8px;flex-wrap:wrap}
input,select{border:1px solid var(--line);border-radius:10px;padding:10px;font:inherit}
table{width:100%;border-collapse:collapse;margin-top:8px}
th,td{border:1px solid #e5e7eb;padding:8px;text-align:left}
th{background:#f8fafc}
.overdue{background:var(--alert)!important;color:var(--alertText)}
.badge{display:inline-block;padding:2px 6px;border-radius:999px;background:#fee2e2;color:#b91c1c;font-size:11px;margin-left:6px}
.tabs{display:flex;gap:8px;justify-content:center;background:#fff5ee;border-bottom:1px solid #ffd8bf}
.tab{padding:8px 14px;border-radius:999px}
.tab.active{background:#ff6a00;color:#fff}
.tab:not(.active){color:#0f172a}
.bottombar{position:sticky;bottom:0;background:#fff;display:flex;gap:8px;justify-content:center;padding:8px;border-top:1px solid #e5e7eb}
.btab{padding:10px 16px;border:1px solid #e5e7eb;border-radius:12px;background:#fff}
.btab.active{background:#ff6a00;border-color:#ff6a00;color:#fff}
</style></head><body>
<header>Жолооч — <a href="/logout">Гарах</a></header>
{tabs_top}
<main>

<div class="card">
  <div class="row">
    <div style="padding:10px 0">Миний дүүрэг: <b id="mydist"></b></div>
    <input id="phoneSearch" placeholder="Утасны дугаараар хайх (тоогоор)">
    <label style="display:flex;align-items:center;gap:6px"><input type="checkbox" id="onlyMine"> Зөвхөн миний авсан</label>
  </div>
</div>

<div class="card">
<table><thead><tr>
<th>#</th><th>Tracking</th><th>Утас</th><th>Хаяг</th><th>Хаяг 2</th><th>Дүүрэг</th><th>Авсан</th><th>Татгалзсан</th><th>Үлдсэн цаг</th>
</tr></thead><tbody id="rows"></tbody></table>
</div>

</main>
{tabs_bottom}
<script>
const USER="__USER__";
const MYDIST="__DIST__";
const LS={DATA:'ret_data__'+MYDIST,EXPIRED:'ret_expired__'+MYDIST,DONE:key('ret_done'),REF:key('ret_ref'),ALERT:key('ret_alert')};
function key(k){return k+'__'+USER;}
const $=s=>document.querySelector(s);
const DAY=24*60*60*1000;

function load(){ return JSON.parse(localStorage.getItem(LS.DATA)||'[]'); }
function save(rows){ localStorage.setItem(LS.DATA, JSON.stringify(rows)); }
let done=JSON.parse(localStorage.getItem(LS.DONE)||'{}');
let ref =JSON.parse(localStorage.getItem(LS.REF)||'{}');
let alerted=JSON.parse(localStorage.getItem(LS.ALERT)||'{}');

function remainMs(t){return DAY-(Date.now()-(t||Date.now()));}
function fmtLeft(ms){ if(ms<=0)return '0ц'; const h=(ms/3600000)|0; const m=((ms%3600000)/60000)|0; return h+'ц '+m+'м'; }
function digits(s){return String(s||'').replace(/\\D/g,'');}

function setPick(id,val){
  const rows=load();
  const r=rows.find(x=>x.id===id); if(!r) return;
  if(val){ done[id]=Date.now(); r.picked=true; r.driverPhone=USER; }
  else { delete done[id]; r.picked=false; r.driverPhone=''; }
  localStorage.setItem(LS.DONE,JSON.stringify(done));
  save(rows);
  render();
}
function setRef(id,val){
  const rows=load(); const r=rows.find(x=>x.id===id); if(!r) return;
  if(val){ ref[id]=Date.now(); r.refused=true; } else { delete ref[id]; r.refused=false; }
  localStorage.setItem(LS.REF,JSON.stringify(ref));
  save(rows);
  render();
}
function alertOnce(id){
  if(alerted[id])return;
  alerted[id]=Date.now();
  if(navigator.vibrate)navigator.vibrate([150,80,150]);
  alert('⚠ 24 цаг дууссан: '+id);
  localStorage.setItem(LS.ALERT,JSON.stringify(alerted));
}
function tick(){
  const rows=load();
  rows.forEach(r=>{
    if(!done[r.id] || r.refused) return;
    const left=remainMs(done[r.id]);
    if(left<=0) alertOnce(r.id);
  });
}
setInterval(tick,60000);

function rowHtml(i,r){
  const id=r.id, phone=r.phone, addr=r.address, addr2=r.address2||'', dist=MYDIST;
  const picked=!!done[id], refused=!!ref[id];
  const left=picked?remainMs(done[id]):null;
  const overdue=picked && left<=0 && !refused;
  const badge=overdue?'<span class="badge">Хоцорсон</span>':'';
  const cls=overdue?' class="overdue"':'';
  const leftTxt=picked?fmtLeft(left):'-';
  return `<tr${cls}><td>${i+1}</td><td><b>${id}</b> ${badge}</td><td><a href="tel:${phone}">${phone}</a></td>
  <td>${addr}</td><td>${addr2}</td><td>${dist}</td>
  <td><input type="checkbox" ${picked?'checked':''} onchange='setPick("${id}",this.checked)'></td>
  <td><input type="checkbox" ${refused?'checked':''} onchange='setRef("${id}",this.checked)'></td>
  <td>${leftTxt}</td></tr>`;
}

function render(){
  document.getElementById('mydist').textContent = MYDIST;
  const q=digits($('#phoneSearch').value||'');
  const onlyMine=$('#onlyMine').checked;

  const rows=load().filter(r=>{
    if(q && !digits(r.phone).includes(q)) return false;
    if(onlyMine && r.driverPhone!==USER) return false;
    return true;
  });

  const tb=$('#rows'); tb.innerHTML='';
  let i=0; rows.forEach(r=> tb.innerHTML+=rowHtml(i++,r));
}

document.addEventListener('DOMContentLoaded', ()=>{
  ['phoneSearch','onlyMine'].forEach(id=> document.getElementById(id).addEventListener('input',render));
  render();
  window.addEventListener('storage', ()=>render());
});
</script>
</body></html>
"""

# ================= ROUTES =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        uid = (request.form.get("id") or "").strip()
        pw  = (request.form.get("password") or "")
        u = USERS.get(uid)
        if u and u["password"] == pw:
            session["user"] = uid
            session["role"] = u["role"]
            session["name"] = u["name"]
            session["district"] = u.get("district","")
            return redirect(url_for("admin" if u["role"]=="admin" else "home"))
        return LOGIN_HTML.replace("{error}", '<div class="err">Нэвтрэх мэдээлэл буруу.</div>')
    return LOGIN_HTML.replace("{error}", "")

@app.route("/register", methods=["GET","POST"])
def register():
    opts = "".join([f"<option>{d}</option>" for d in DISTRICTS])
    html = REGISTER_HTML.replace("{error}","").replace("{ok}","").replace("{opts}",opts)
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        phone= (request.form.get("phone") or "").strip()
        pw   = (request.form.get("password") or "").strip()
        dist = (request.form.get("district") or "").strip()
        if not (name and phone and pw and phone.isdigit() and dist):
            return REGISTER_HTML.replace("{ok}","").replace("{error}",'<div class="err">Талбаруудыг зөв бөглөнө үү.</div>').replace("{opts}",opts)
        if phone in USERS:
            return REGISTER_HTML.replace("{ok}","").replace("{error}",'<div class="err">Энэ дугаар бүртгэлтэй байна.</div>').replace("{opts}",opts)
        USERS[phone] = {"role":"driver","name":name,"password":pw,"district":dist}
        return REGISTER_HTML.replace("{error}","").replace("{ok}",'<div class="ok">Амжилттай! Одоо нэвтэрнэ үү.</div>').replace("{opts}",opts)
    return html

@app.route("/forgot", methods=["GET","POST"])
def forgot():
    html = FORGOT_HTML.replace("{error}","").replace("{ok}","")
    if request.method=="POST":
        phone = (request.form.get("phone") or "").strip()
        p1    = (request.form.get("password1") or "").strip()
        p2    = (request.form.get("password2") or "").strip()
        u = USERS.get(phone)
        if not (phone and p1 and p2):
            return FORGOT_HTML.replace("{ok}","").replace("{error}",'<div class="err">Бүгдийг бөглөнө үү.</div>')
        if p1 != p2:
            return FORGOT_HTML.replace("{ok}","").replace("{error}",'<div class="err">Нууц үг таарахгүй байна.</div>')
        if not u or u.get("role")!="driver":
            return FORGOT_HTML.replace("{ok}","").replace("{error}",'<div class="err">Энэ дугаарт жолооч бүртгэлгүй байна.</div>')
        u["password"] = p1
        return FORGOT_HTML.replace("{error}","").replace("{ok}",'<div class="ok">Шинэ нууц үг идэвхжлээ. Одоо нэвтэрнэ үү.</div>')
    return html

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    user = session["user"]
    role = session.get("role","driver")
    dist = session.get("district","")
    html = DRIVER_HTML.replace("{tabs_top}", top_nav('driver', role)) \
                      .replace("{tabs_bottom}", bottom_nav('driver', role)) \
                      .replace("%DISTLIST%", str(DISTRICTS)) \
                      .replace("__USER__", user) \
                      .replace("__DIST__", dist or DISTRICTS[0])
    return Response(html, mimetype="text/html")

@app.route("/admin")
@login_required
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("home"))
    html = ADMIN_HTML.replace("{tabs_top}", top_nav('admin','admin')) \
                     .replace("{tabs_bottom}", bottom_nav('admin','admin')) \
                     .replace("%DISTLIST%", str(DISTRICTS))
    return Response(html, mimetype="text/html")

@app.route("/health")
def health():
    return {"ok": True, "ts": int(time.time())}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
