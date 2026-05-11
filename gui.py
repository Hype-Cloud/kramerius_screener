#!/usr/bin/env python3
"""Knihovna Scraper GUI"""

import threading
import webbrowser
import subprocess
import sys
import os
import signal
import re
import urllib.request
import json as _json
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, Response
import queue

app = Flask(__name__)
MEDIA_DIR = Path(__file__).parent / 'media'
log_queue = queue.Queue()
running = False
current_proc = None

HTML = """
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/png" href="/media/favicon.png">
<title>Kramerius Screener</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0f0f0f; --surface: #1a1a1a; --border: #2a2a2a;
    --accent: #e8d5a3; --accent2: #a3c4e8; --text: #e0e0e0;
    --muted: #666; --green: #4caf6e; --red: #e05555;
  }
  body { background: var(--bg); color: var(--text); font-family: 'IBM Plex Sans', sans-serif; min-height: 100vh; padding: 2rem; }
  #terminator-flash {
    display: none;
    position: fixed;
    inset: 0;
    background-image: url('/media/background.jpg');
    background-size: cover;
    background-position: center;
    z-index: -1;
    opacity: 0;
    pointer-events: none;
  }
  .container { width: 100%; max-width: 680px; }
  header { margin-bottom: 2.5rem; }
  header h1 { font-family: 'IBM Plex Mono', monospace; font-size: 1.1rem; font-weight: 600; color: var(--accent); letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.4rem; }
  header p { color: var(--muted); font-size: 0.85rem; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 4px; padding: 1.5rem; margin-bottom: 1rem; }
  label { display: block; font-size: 0.75rem; font-family: 'IBM Plex Mono', monospace; color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.6rem; }
  textarea { width: 100%; background: var(--bg); border: 1px solid var(--border); border-radius: 3px; color: var(--text); font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; padding: 0.75rem; resize: vertical; min-height: 100px; outline: none; transition: border-color 0.2s; line-height: 1.6; }
  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--muted); }
  .hint { font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem; }
  .controls { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
  .btn { display: inline-flex; align-items: center; gap: 0.5rem; background: var(--accent); color: #0f0f0f; border: none; border-radius: 3px; padding: 0.7rem 1.4rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; font-weight: 600; letter-spacing: 0.05em; cursor: pointer; transition: opacity 0.2s; text-transform: uppercase; }
  .btn:hover { opacity: 0.85; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-stop { background: transparent; color: var(--red); border: 1px solid var(--red); }
  .btn-stop:hover { background: var(--red); color: white; opacity: 1; }
  .check-label { display: flex; align-items: center; gap: 0.4rem; cursor: pointer; font-size: 0.78rem; font-family: 'IBM Plex Mono', monospace; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }
  .check-label input { accent-color: var(--accent); width: 14px; height: 14px; cursor: pointer; }
  #log { background: var(--bg); border: 1px solid var(--border); border-radius: 3px; padding: 1rem; height: 300px; overflow-y: auto; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; line-height: 1.7; color: var(--muted); }
  .log-line { margin-bottom: 0.1rem; }
  .log-line.ok { color: var(--green); }
  .log-line.err { color: var(--red); }
  .log-line.info { color: var(--accent2); }
  .log-line.head { color: var(--accent); }
  .status { display: flex; align-items: center; gap: 0.75rem; margin-top: 0.75rem; font-size: 0.78rem; color: var(--muted); font-family: 'IBM Plex Mono', monospace; }
  .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); animation: pulse 1.2s ease-in-out infinite; }
  .dot.idle { background: var(--muted); animation: none; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
  [data-tooltip] { position: relative; }
  [data-tooltip]:hover::after { content: attr(data-tooltip); position: absolute; bottom: 130%; left: 50%; transform: translateX(-50%); background: var(--surface); border: 1px solid var(--border); color: var(--accent); font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; padding: 0.4rem 0.6rem; border-radius: 3px; white-space: nowrap; z-index: 999; pointer-events: none; }
  .navbar { position:fixed; top:0; left:0; right:0; height:3.2rem; background:var(--bg); border-bottom:1px solid var(--border); display:flex; align-items:center; padding:0 1.5rem; z-index:200; gap:1rem; }
  .navbar h1 { font-family:'IBM Plex Mono',monospace; font-size:0.9rem; font-weight:600; color:var(--accent); letter-spacing:0.05em; text-transform:uppercase; margin:0; white-space:nowrap; }
  .navbar-center { flex:1; display:flex; justify-content:center; }
  .navbar-right { white-space:nowrap; text-align:right; }
  .navbar-btn { background:none; border:1px solid var(--border); border-radius:3px; color:var(--muted); font-family:'IBM Plex Mono',monospace; font-size:0.72rem; letter-spacing:0.08em; text-transform:uppercase; padding:0.35rem 0.9rem; cursor:pointer; }
  .navbar-btn:hover { border-color:var(--accent); color:var(--accent); }
  #bookList { margin-top: 0.75rem; }
  .book-item { display: flex; gap: 0.5rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; margin-bottom: 0.2rem; }
  .book-num { color: var(--muted); min-width: 1.2rem; }
  .book-title { color: var(--accent); }
  .book-muted { color: var(--muted); font-style: italic; }
</style>
</head>
<body>
<nav class="navbar" style="height:auto; padding:0.75rem 1.5rem;">
  <div>
    <h1>Kramerius Screener</h1>
    <p style="font-size:0.72rem; color:var(--muted); margin-top:0.2rem;">Screenování knih z digitalnikni<span style="color:#8B4513;">hovna</span>.cz</p>
  </div>
  <div class="navbar-center">
    <a href="#jak-pouzivat" class="navbar-btn" style="color:var(--accent); border-color:var(--accent); text-decoration:none; font-family:'IBM Plex Mono',monospace; font-size:0.72rem; letter-spacing:0.08em; text-transform:uppercase; padding:0.35rem 0.9rem; border-radius:3px; border:1px solid; transition:opacity 0.2s;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">Jak používat</a>
  </div>
  <div class="navbar-right" style="padding-top:0.3rem;">
    <button class="btn" onclick="loginToLibrary()" id="btnLogin" style="padding:0.4rem 0.9rem; font-size:0.72rem;">Přihlásit se do knihovny</button>
    <div style="font-size:0.65rem; font-family:'IBM Plex Mono',monospace; color:var(--muted); margin-top:0.2rem;">pouze při prvním použití</div>
  </div>
</nav>
<div id="terminator-flash"></div>
<button id="scrollTop" onclick="window.scrollTo({top:0,behavior:'smooth'})" style="display:none; position:fixed; bottom:2rem; right:2rem; background:var(--accent); color:#0f0f0f; border:none; border-radius:3px; padding:0.6rem 0.9rem; font-family:'IBM Plex Mono',monospace; font-size:0.8rem; font-weight:600; cursor:pointer; z-index:100; opacity:0.85;">↑</button>
<div class="container" style="margin-top:4.5rem; max-width:680px; margin-left:auto; margin-right:auto;">


  <div class="card">
    <label>Výstupní složka</label>
    <div style="display:flex; gap:0.5rem; align-items:center;">
      <input type="text" id="outputDir" placeholder="Výchozí: ~/Downloads" style="flex:1; background:var(--bg); border:1px solid var(--border); border-radius:3px; color:var(--text); font-family:'IBM Plex Mono',monospace; font-size:0.82rem; padding:0.75rem; outline:none;">
      <button class="btn" style="padding:0.7rem 1rem; white-space:nowrap;" onclick="pickFolder()" id="btnPick">📁 Vybrat</button>
    </div>
    <p class="hint">Nech prázdné pro výchozí složku Downloads.</p>
  </div>

  <div class="card">
    <label>URL knih</label>
    <textarea id="urls" placeholder="https://www.digitalniknihovna.cz/mzk/view/uuid:...&#10;https://www.digitalniknihovna.cz/mzk/view/uuid:...&#10;&#10;Každá kniha na nový řádek." onblur="lookupTitles()"></textarea>
    <p class="hint">Každá URL na samostatný řádek. Stahování probíhá postupně.</p>
    <div id="bookList"></div>
  </div>

  <div class="controls">
    <button class="btn" id="btnStart" onclick="start()">▶ Spustit</button>
    <button class="btn" id="btnPause" onclick="togglePause()" style="display:none; background:transparent; color:var(--accent); border:1px solid var(--accent); min-width:160px;">❚❚ Pauza</button>
    <button class="btn btn-stop" id="btnStop" onclick="stop()" style="display:none">■ Zastavit</button>
    <label class="check-label" data-tooltip="Pouze pro rychlé připojení – může být méně spolehlivé. Lze přepínat v průběhu.">
      <input type="checkbox" id="chkFast" onchange="fetch('/toggle-fast',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fast:this.checked})})">
      ⚡ Rychlý režim
    </label>
    <label class="check-label">
      <input type="checkbox" id="chkTest">
      Test (2 stránky)
    </label>
  </div>

  <div class="card" style="padding:0;">
    <div id="log"><span style="color:var(--muted)">Čeká na spuštění...</span></div>
  </div>

  <div class="status">
    <div class="dot idle" id="dot"></div>
    <span id="statusText">Připraveno</span>
  </div>

  <div id="jak-pouzivat" style="margin-top:1.5rem; padding:1rem 1.25rem; border:1px solid var(--border); border-radius:4px;">
    <p style="font-size:0.75rem; font-family:'IBM Plex Mono',monospace; color:var(--accent); letter-spacing:0.08em; text-transform:uppercase; margin-bottom:0.6rem;">Jak používat</p>
    <ul style="font-size:0.72rem; font-family:'IBM Plex Mono',monospace; color:var(--muted); line-height:2; letter-spacing:0.03em; list-style:none; padding:0;">
      <li style="display:flex; gap:0.5rem;"><span>—</span><span>Tato stránka musí být otevřená v prohlížeči Google Chrome</span></li>
      <li style="display:flex; gap:0.5rem;"><span>—</span><span>Tento program slouží pouze pro uživatele s přístupem do digitalnikni<span style="color:#8B4513;">hovna</span>.cz</span></li>
      <li style="display:flex; gap:0.5rem;"><span>—</span><span>Program nestahuje žádný obsah – pouze pořizuje screenshoty obsahu, ke kterému máte povolený přístup</span></li>
      <li style="display:flex; gap:0.5rem;"><span>—</span><span>Program otevře další okno prohlížeče – může být minimalizované na pozadí</span></li>
      <li style="display:flex; gap:0.5rem;"><span>—</span><span>Při prvním spuštění se v tomto okně budete muset přihlásit do digitalnikni<span style="color:#8B4513;">hovna</span>.cz – přihlášení z vašeho Chrome se nepřenáší. Program nemá přístup k vašim přihlašovacím údajům, přihlášení probíhá přímo v okně prohlížeče. Po prvním přihlášení si program přihlášení zapamatuje.</span></li>
      <li style="display:flex; gap:0.5rem;"><span>—</span><span>Neměňte velikost tohoto okna a na nic v něm neklikejte (kromě přihlášení při prvním spuštění)</span></li>
      <li style="display:flex; gap:0.5rem;"><span>—</span><span>Tlačítkem Spustit program automaticky deaktivuje spořič obrazovky a režim spánku – pro větší spolehlivost doporučujeme deaktivovat je i ručně</span></li>
      <li style="display:flex; gap:0.5rem;"><span>—</span><span>Okno kde probíhá screenshotování se samo zavře po dokončení – nezavírejte ho ručně</span></li>
      <li style="display:flex; gap:0.5rem;"><span>—</span><span>Tuto stránku zavřete až po dokončení screenshotování – zavřením se ukončí celý proces</span></li>
      <li style="display:flex; gap:0.5rem;"><span>—</span><span>Vždy si zkontrolujte výsledné PDF – pokud se stránka načítala příliš dlouho, program mohl vyfotit načítací kolečko místo obsahu</span></li>
    </ul>
    <p style="font-size:0.72rem; font-family:'IBM Plex Mono',monospace; color:var(--muted); line-height:2; letter-spacing:0.03em; margin-top:1rem; font-style:italic;">Tento projekt vznikl z frustrace při psaní 2 seminárních prací s obskurní tematikou na poslední chvíli.</p>
    <ul style="display:none">
    </ul>
  </div>
</div>

<script>
let evtSource = null;

async function loginToLibrary() {
  const btn = document.getElementById('btnLogin');
  btn.disabled = true;
  try { await fetch('/open-login', {method: 'POST'}); } catch(e) {}
  setTimeout(() => { btn.disabled = false; }, 3000);
}

window.addEventListener('scroll', function() {
  const btn = document.getElementById('scrollTop');
  btn.style.display = window.scrollY > window.innerHeight / 2 ? 'block' : 'none';
});

async function lookupTitles() {
  const raw = document.getElementById('urls').value.trim();
  const urls = raw.split('\\n').map(u => u.trim()).filter(u => u.length > 0);
  const list = document.getElementById('bookList');
  if (!urls.length) { list.innerHTML = ''; return; }

  list.innerHTML = urls.map((u, i) =>
    '<div class="book-item"><span class="book-num">' + (i+1) + '.</span><span class="book-muted" id="bt-' + i + '">loading...</span></div>'
  ).join('');

  urls.forEach(async (url, i) => {
    try {
      const res = await fetch('/book-title', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({url: url})
      });
      const data = await res.json();
      const el = document.getElementById('bt-' + i);
      if (el) {
        el.textContent = data.title || '-- nazev nenalezen --';
        el.className = data.title ? 'book-title' : 'book-muted';
      }
    } catch(e) {
      const el = document.getElementById('bt-' + i);
      if (el) el.textContent = '-- chyba --';
    }
  });
}

window.addEventListener('beforeunload', function(e) {
  e.preventDefault();
  e.returnValue = '';
});

async function shutdown() {
  await fetch('/shutdown', {method: 'POST'});
}

window.addEventListener('unload', function() {
  navigator.sendBeacon('/shutdown');
});

async function pickFolder() {
  document.getElementById('btnPick').textContent = '...';
  try {
    const res = await fetch('/pick-folder', {method: 'POST'});
    const data = await res.json();
    if (data.path) document.getElementById('outputDir').value = data.path;
  } catch(e) { console.error(e); }
  document.getElementById('btnPick').textContent = '📁 Vybrat';
}

function setRunning(isRunning) {
  document.getElementById('btnStart').disabled = isRunning;
  document.getElementById('btnStop').style.display = isRunning ? 'inline-flex' : 'none';
  document.getElementById('btnPause').style.display = isRunning ? 'inline-flex' : 'none';
  if (!isRunning) { paused = false; document.getElementById('btnPause').textContent = '\u275a\u275a Pauza'; }
  document.getElementById('dot').className = isRunning ? 'dot' : 'dot idle';
  document.getElementById('statusText').textContent = isRunning ? 'Stahuje...' : 'Hotovo';
}

function flashTerminator() {
  const el = document.getElementById('terminator-flash');
  el.style.display = 'block';
  el.style.opacity = '0';
  let start = null;
  function animate(ts) {
    if (!start) start = ts;
    const p = (ts - start) / 3000;
    if (p < 0.3) { el.style.opacity = (p / 0.3).toFixed(2); }
    else if (p < 0.7) { el.style.opacity = '1'; }
    else if (p < 1) { el.style.opacity = (1 - (p - 0.7) / 0.3).toFixed(2); }
    else { el.style.display = 'none'; el.style.opacity = '0'; return; }
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
}

function start() {
  const raw = document.getElementById('urls').value.trim();
  const urls = raw.split('\\n').map(u => u.trim()).filter(u => u.length > 0);
  if (!urls.length) { alert('Vlo\u017ete pros\u00edm alespo\u0148 jednu URL.'); return; }

  const testMode = document.getElementById('chkTest').checked;
  const outputDir = document.getElementById('outputDir').value.trim();

  document.getElementById('log').innerHTML = '';
  setRunning(true);
  flashTerminator();

  fetch('/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({urls, test: testMode, outputDir, fast: document.getElementById('chkFast').checked})
  });

  if (evtSource) evtSource.close();
  evtSource = new EventSource('/stream');
  evtSource.onmessage = function(e) {
    const log = document.getElementById('log');
    const msg = e.data;

    if (msg === 'DONE') {
      setRunning(false);
      evtSource.close();
      return;
    }

    const line = document.createElement('div');
    line.className = 'log-line';
    if (msg.includes('\u2705') || msg.includes('\u2713')) line.className += ' ok';
    else if (msg.includes('\u274c') || msg.includes('\u2717')) line.className += ' err';
    else if (msg.includes('📖') || msg.includes('===')) line.className += ' head';
    else if (msg.includes('\u2192') || msg.includes('📚')) line.className += ' info';
    line.textContent = msg;
    log.appendChild(line);
    log.scrollTop = log.scrollHeight;

    document.getElementById('statusText').textContent = msg.replace(/[\u2705\u2713\u274c\u2717\u2192\u1f4d6\u1f4da\u23f3\u25a0\u25b6]/g, '').trim().slice(0, 60);
  };
}

let paused = false;

function togglePause() {
  paused = !paused;
  const btn = document.getElementById('btnPause');
  if (paused) {
    fetch('/pause', {method: 'POST'});
    btn.textContent = '\u25b6 Pokra\u010dovat';
  } else {
    fetch('/resume', {method: 'POST'});
    btn.textContent = '\u275a\u275a Pauza';
  }
}

function stop() {
  if (!confirm('P\u0159ejete si skute\u010dn\u011b zastavit screenov\u00e1n\u00ed?')) return;
  fetch('/stop', {method: 'POST'});
  document.getElementById('statusText').textContent = 'Zastavuji...';
}
</script>
</body>
</html>
"""

@app.route('/media/<path:filename>')
def media(filename):
    from flask import send_from_directory
    return send_from_directory(str(MEDIA_DIR), filename)

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/book-title', methods=['POST'])
def book_title():
    data = request.json
    url = data.get('url', '')
    m = re.search(r'uuid:[a-f0-9-]{36}', url, re.I)
    if not m:
        return jsonify({'title': None})
    uuid = m.group(0)
    slug_m = re.search(r'digitalniknihovna\.cz/([^/]+)/', url)
    slug = slug_m.group(1) if slug_m else 'mzk'
    try:
        api_url = f'https://kramerius.{slug}.cz/search/api/v5.0/item/{uuid}'
        with urllib.request.urlopen(api_url, timeout=5) as r:
            d = _json.loads(r.read())
            title = d.get('title') or (d.get('dc_title') or [None])[0]
            return jsonify({'title': title})
    except:
        return jsonify({'title': None})

@app.route('/open-login', methods=['POST'])
def open_login():
    profile_dir = str(Path.home() / '.kramerius_profile')
    lock = Path(profile_dir) / 'SingletonLock'
    if lock.exists():
        try: lock.unlink()
        except: pass
    def run_login():
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                ctx = p.chromium.launch_persistent_context(
                    user_data_dir=profile_dir, headless=False,
                    viewport={'width': 1200, 'height': 800},
                )
                page = ctx.new_page()
                page.goto('https://www.digitalniknihovna.cz')
                try: page.wait_for_event('close', timeout=300000)
                except: pass
                ctx.close()
        except Exception as e:
            print(f"Login error: {e}")
    threading.Thread(target=run_login, daemon=True).start()
    return jsonify({'ok': True})

@app.route('/toggle-fast', methods=['POST'])
def toggle_fast():
    fast_file = Path.home() / '.kramerius_fast'
    data = request.json
    if data.get('fast'):
        fast_file.touch()
    else:
        fast_file.unlink(missing_ok=True)
    return jsonify({'ok': True})

@app.route('/shutdown', methods=['POST'])
def shutdown():
    import os
    threading.Timer(0.5, lambda: os.kill(os.getpid(), signal.SIGTERM)).start()
    return jsonify({'ok': True})

@app.route('/pick-folder', methods=['POST'])
def pick_folder():
    import subprocess, platform
    system = platform.system()
    try:
        if system == "Darwin":
            script = 'tell application "Finder" to set f to choose folder\nreturn POSIX path of f'
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=60)
            path = result.stdout.strip()
        elif system == "Windows":
            result = subprocess.run([
                'powershell', '-Command',
                '[System.Reflection.Assembly]::LoadWithPartialName("System.windows.forms") | Out-Null; $f = New-Object System.Windows.Forms.FolderBrowserDialog; $f.ShowDialog() | Out-Null; $f.SelectedPath'
            ], capture_output=True, text=True, timeout=60)
            path = result.stdout.strip()
        else:  # Linux
            result = subprocess.run(
                ['zenity', '--file-selection', '--directory'],
                capture_output=True, text=True, timeout=60
            )
            path = result.stdout.strip()
        if path:
            return jsonify({'path': path})
    except Exception as e:
        pass
    return jsonify({'path': ''})

@app.route('/start', methods=['POST'])
def start():
    global running, current_proc
    data = request.json
    urls = data.get('urls', [])
    test_mode = data.get('test', False)
    output_dir = data.get('outputDir', '').strip()
    running = True

    def run():
        global current_proc, running
        script = Path(__file__).parent / 'kramerius_screenshot.py'
        python = sys.executable
        _test = test_mode
        _output_dir = output_dir

        for i, url in enumerate(urls):
            if not running:
                break
            log_queue.put(f"{'='*40}")
            log_queue.put(f"📖 Kniha {i+1}/{len(urls)}")
            log_queue.put(f"{'='*40}")
            extra = ["--test"] if _test else []
            if data.get('fast', False):
                extra.append("--fast")
            if _output_dir:
                extra += ["--outdir", _output_dir]
            current_proc = subprocess.Popen(
                [python, str(script), url] + extra,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in current_proc.stdout:
                log_queue.put(line.rstrip())
            current_proc.wait()
            current_proc = None

        log_queue.put("DONE")

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'ok': True})

@app.route('/pause', methods=['POST'])
def pause_route():
    global current_proc
    if current_proc:
        current_proc.send_signal(signal.SIGSTOP)
    return jsonify({'ok': True})

@app.route('/resume', methods=['POST'])
def resume_route():
    global current_proc
    if current_proc:
        current_proc.send_signal(signal.SIGCONT)
    return jsonify({'ok': True})

@app.route('/stop', methods=['POST'])
def stop_route():
    global running, current_proc
    running = False
    if current_proc:
        current_proc.send_signal(signal.SIGTERM)
    return jsonify({'ok': True})

@app.route('/stream')
def stream():
    def generate():
        while True:
            try:
                msg = log_queue.get(timeout=30)
                yield f"data: {msg}\n\n"
                if msg == "DONE":
                    break
            except:
                yield "data: \n\n"
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = 7432
    print(f"\n🌐 Otevři: http://localhost:{port}")
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(port=port, debug=False, threaded=True)
