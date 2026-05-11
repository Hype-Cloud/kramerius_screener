@echo off
cd /d "%~dp0"

echo Hledam Python...
set PYTHON=
for %%p in (python3.11 python3.12 python3.10 python3 python) do (
    where %%p >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=*" %%v in ('%%p -c "import sys; print(sys.version_info >= (3,10))"') do (
            if "%%v"=="True" (
                set PYTHON=%%p
                goto found
            )
        )
    )
)

echo.
echo Python 3.10+ nenalezen.
echo Stahni Python z: https://www.python.org/downloads/
echo Pri instalaci zaškrtni "Add Python to PATH"
echo Po instalaci spust tento soubor znovu.
echo.
start https://www.python.org/downloads/
pause
exit /b 1

:found
echo Pouzivam: %PYTHON%

%PYTHON% -c "import flask, playwright, PIL, reportlab" 2>nul || (
    echo Instaluji zavislosti...
    %PYTHON% -m pip install flask playwright pillow reportlab -q
)

%PYTHON% -m playwright install chromium 2>nul

%PYTHON% gui.py
pause
