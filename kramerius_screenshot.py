#!/usr/bin/env python3
"""
Kramerius Screenshot Downloader
Použití:
    python3 kramerius_screenshot.py <URL> [vystup.pdf] [--test]
"""

import sys
import hashlib
import re
import time
import signal
from pathlib import Path
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from playwright.sync_api import sync_playwright

PROFILE_DIR = str(Path.home() / ".kramerius_profile")

def clear_singleton_lock():
    """Smaže SingletonLock pokud existuje z předchozího pádu."""
    lock = Path(PROFILE_DIR) / "SingletonLock"
    if lock.exists():
        lock.unlink()
        print("→ Smazán SingletonLock z předchozího běhu")
def prevent_sleep():
    """Zabrání spánku zařízení během stahování."""
    import platform, subprocess
    system = platform.system()
    try:
        if system == "Darwin":
            proc = subprocess.Popen(["caffeinate", "-d", "-i"])
            print("→ Spořič obrazovky deaktivován (Mac)")
            return proc
        elif system == "Windows":
            subprocess.Popen([
                "powershell", "-WindowStyle", "Hidden", "-Command",
                "while($true) { [System.Windows.Forms.SendKeys]::SendWait('{F15}'); Start-Sleep -Seconds 30 }"
            ], creationflags=subprocess.CREATE_NO_WINDOW)
            print("→ Spořič obrazovky deaktivován (Windows)")
            return None
        elif system == "Linux":
            proc = subprocess.Popen(["systemd-inhibit", "--what=idle:sleep", "--who=KnihovnaScraper", "--why=Stahování", "sleep", "86400"])
            print("→ Spořič obrazovky deaktivován (Linux)")
            return proc
    except Exception as e:
        print(f"→ Nepodařilo se deaktivovat spořič: {e}")
    return None


def allow_sleep(proc):
    """Znovu povolí spánek."""
    if proc:
        try:
            proc.terminate()
            print("→ Spořič obrazovky opět povolen")
        except:
            pass


TEMP_DIR = Path.home() / ".kramerius_temp"
TEMP_DIR.mkdir(exist_ok=True)

# Signal pro graceful stop
stop_requested = False

def handle_stop(sig, frame):
    global stop_requested
    print("\n→ Zastavuji, ukládám co je hotové...")
    stop_requested = True

signal.signal(signal.SIGTERM, handle_stop)
signal.signal(signal.SIGINT, handle_stop)


def get_downloads_dir():
    home = Path.home()
    for candidate in [home / "Downloads", home / "Stažené", home / "Desktop"]:
        if candidate.exists():
            return str(candidate)
    return str(home)

def parse_args():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        url = sys.argv[1]
    else:
        print("\n📚 Vlož URL knihy z digitalniknihovna.cz:")
        url = input("URL: ").strip()
    test_mode = "--test" in sys.argv

    output_dir = None
    if "--outdir" in sys.argv:
        idx = sys.argv.index("--outdir")
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]

    if not output_dir:
        output_dir = get_downloads_dir()

    fast_mode = "--fast" in sys.argv
    return url, test_mode, output_dir, fast_mode


def get_page_uuids(page, url):
    m = re.search(r"uuid:[a-f0-9\-]{36}", url)
    if not m:
        print("❌ UUID nenalezeno v URL")
        sys.exit(1)
    doc_uuid = m.group(0)

    slug = "mzk"
    for s in ["nkp", "mzk", "cas", "cbvk", "cdk"]:
        if s in url:
            slug = s
            break

    for api_url in [
        f"https://kramerius.{slug}.cz/search/api/v5.0/item/{doc_uuid}/children",
        f"https://api.kramerius.{slug}.cz/search/api/client/v7.0/items/{doc_uuid}/children",
    ]:
        try:
            r = page.request.get(api_url)
            if r.ok:
                data = r.json()
                if data:
                    uuids = [item.get("pid") or item.get("uuid") or item.get("id") for item in data]
                    uuids = [u for u in uuids if u]
                    print(f"→ Nalezeno {len(uuids)} stránek")
                    return uuids, slug
        except Exception as e:
            print(f"  API: {e}")

    return [], slug


def screenshot_page(page, url, slug, page_uuid):
    base = url.split('?')[0]
    try:
        page.goto(f"{base}?page={page_uuid}", wait_until="networkidle", timeout=20000)
    except:
        page.goto(f"{base}?page={page_uuid}", wait_until="domcontentloaded", timeout=20000)
    fast = (Path.home() / ".kramerius_fast").exists()
    time.sleep(1.0 if fast else 2.5)

    for sel in [".reader-content", ".document-viewer", ".page-content", "main"]:
        try:
            el = page.query_selector(sel)
            if el:
                return el.screenshot()
        except:
            pass
    return page.screenshot(full_page=False)


def crop_to_document(img):
    w, h = img.size
    left = int(w * 0.22)
    right = int(w * 0.857)
    top = 30
    return img.crop((left, top, right, h))


def save_screenshot_temp(data, index, session_id):
    """Uloží screenshot na disk okamžitě."""
    path = TEMP_DIR / f"{session_id}_{index:04d}.jpg"
    img = Image.open(BytesIO(data))
    img = crop_to_document(img)
    img.convert("RGB").save(str(path), "JPEG", quality=92)
    return path


def assemble_pdf(session_id, output_path):
    """Sestaví PDF ze všech uložených screenshotů."""
    files = sorted(TEMP_DIR.glob(f"{session_id}_*.jpg"))
    if not files:
        print("❌ Žádné screenshoty k uložení.")
        return

    print(f"\n→ Sestavuji PDF ({len(files)} stránek): {output_path}")
    c = canvas.Canvas(output_path)
    for i, f in enumerate(files):
        try:
            img = Image.open(f)
            w, h = img.size
            pw = A4[0]
            ph = h * (pw / w)
            c.setPageSize((pw, ph))
            c.drawImage(str(f), 0, 0, width=pw, height=ph)
            c.showPage()
            print(f"  ✓ {i+1}/{len(files)}", end="\r")
        except Exception as e:
            print(f"  ✗ {i+1}: {e}")
    c.save()

    # Smaž temp soubory
    for f in files:
        f.unlink()

    mb = Path(output_path).stat().st_size / 1024 / 1024
    print(f"\n✅ Hotovo! {output_path} ({mb:.1f} MB)")


def main():
    global stop_requested
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url, test_mode, output_dir, fast_mode = parse_args()
    if not output_dir:
        output_dir = get_downloads_dir()

    # Session ID pro temp soubory
    session_id = hashlib.md5(url.encode()).hexdigest()[:8]

    # Smaž zámek profilu pokud existuje (zůstal po pádu)
    lock_file = Path(PROFILE_DIR) / "SingletonLock"
    if lock_file.exists():
        try:
            lock_file.unlink()
            print("→ Odstraněn starý zámek profilu")
        except:
            pass

    clear_singleton_lock()
    sleep_proc = prevent_sleep()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            viewport={"width": 1400, "height": 900},
        )
        page = context.new_page()

        print(f"→ Otevírám dokument...")
        page.goto(url, timeout=30000)
        try:
            page.wait_for_selector(".reader-content, .document-viewer, canvas", timeout=30000)
            time.sleep(2)
        except:
            time.sleep(3)

        # Název z metadat
        filename = "vystup.pdf"
        try:
            title_el = page.query_selector("h1, .metadata-title, .doc-title")
            doc_title = title_el.inner_text().strip() if title_el else None
            if doc_title:
                safe = re.sub(r"[^\w\s\-]", "", doc_title).strip().replace(" ", "_")[:60]
                filename = safe + ".pdf"
                print(f"→ Název souboru: {filename}")
        except:
            pass
        output = str(Path(output_dir) / filename)
        print(f"→ Ukládám do: {output}")

        page_uuids, slug = get_page_uuids(page, url)
        if not page_uuids:
            print("❌ Nepodařilo se načíst seznam stránek.")
            context.close()
            sys.exit(1)

        if test_mode:
            page_uuids = page_uuids[:2]
            print(f"→ Testovací režim: 2 stránky")

        count = 0
        for i, pid in enumerate(page_uuids):
            if stop_requested:
                print(f"\n→ Zastaveno na stránce {i+1}, ukládám {count} stránek...")
                break

            print(f"  Screenshot {i+1}/{len(page_uuids)}", end=" ", flush=True)
            try:
                ss = screenshot_page(page, url, slug, pid)
                save_screenshot_temp(ss, i, session_id)
                count += 1
                print("✓")
            except Exception as e:
                print(f"✗ ({e})")
            time.sleep(0.5 if fast_mode else 0.5)

        context.close()

    allow_sleep(sleep_proc)

    if count > 0:
        assemble_pdf(session_id, output)
    else:
        print("❌ Žádné screenshoty.")


if __name__ == "__main__":
    main()
