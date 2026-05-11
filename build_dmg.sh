#!/bin/bash
# Kramerius Screener - Mac DMG Builder
cd "$(dirname "$0")"

echo "→ Instaluji závislosti..."
/usr/local/bin/python3.11 -m pip install pyinstaller flask playwright pillow reportlab -q

echo "→ Stahuji Chromium..."
/usr/local/bin/python3.11 -m playwright install chromium

# Najdi Playwright Chromium cestu
CHROMIUM_PATH=$(/usr/local/bin/python3.11 -c "
from playwright.sync_api import sync_playwright
import os
p = sync_playwright().start()
browser = p.chromium.launch()
exe = browser.version
browser.close()
p.stop()
# Get chromium executable path
import subprocess
result = subprocess.run(['/usr/local/bin/python3.11', '-m', 'playwright', 'run-driver'], capture_output=True)
" 2>/dev/null || echo "")

echo "→ Buildím aplikaci..."
/usr/local/bin/python3.11 -m PyInstaller \
  --name "Kramerius Screener" \
  --windowed \
  --onedir \
  --add-data "media:media" \
  --add-data "kramerius_screenshot.py:." \
  --hidden-import flask \
  --hidden-import playwright \
  --hidden-import PIL \
  --hidden-import reportlab \
  gui.py

if [ -d "dist/Kramerius Screener.app" ]; then
  echo "→ Vytvářím DMG..."
  hdiutil create \
    -volname "Kramerius Screener" \
    -srcfolder "dist/Kramerius Screener.app" \
    -ov -format UDZO \
    "Kramerius_Screener.dmg"
  echo "✅ Hotovo! Kramerius_Screener.dmg"
else
  echo "❌ Build selhal"
fi
