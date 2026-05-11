#!/bin/bash
cd "$(dirname "$0")"

PYTHON=""
for cmd in python3.11 python3.12 python3.10 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" -c "import sys; print(sys.version_info >= (3,10))" 2>/dev/null)
        if [ "$version" = "True" ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "→ Python nenalezen, instaluji..."
    if ! command -v brew &>/dev/null; then
        echo "→ Instaluji Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install python@3.11
    PYTHON="python3.11"
fi

echo "→ Používám: $($PYTHON --version)"

$PYTHON -c "import flask, playwright, PIL, reportlab" 2>/dev/null || {
    echo "→ Instaluji závislosti..."
    $PYTHON -m pip install flask playwright pillow reportlab -q
}

$PYTHON -m playwright install chromium 2>/dev/null || true

$PYTHON gui.py
