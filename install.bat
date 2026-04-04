@echo off
setlocal EnableDelayedExpansion

:: ================================================================
::  install.bat  -  Local CLI Agent  |  Globale Installation (Windows)
::  Doppelklick aus Explorer ODER Aufruf aus CMD/PowerShell.
:: ================================================================

cd /d "%~dp0"

echo.
echo  ================================================================
echo   Local CLI Agent  ^|  Globale Installation
echo  ================================================================
echo.


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 1: Python prüfen / installieren
:: ════════════════════════════════════════════════════════════════

python --version >nul 2>&1
if not errorlevel 1 goto :python_ok

echo  [INFO]  Python wurde nicht gefunden.
echo.
set /p INSTALL_PY="  Soll Python automatisch installiert werden? [j/n]: "
echo.

if /i "!INSTALL_PY!"=="j" goto :install_python
echo  [INFO]  Bitte Python 3.8+ manuell installieren:
echo          https://www.python.org/downloads/
echo.
goto :fail

:install_python
echo  [INFO]  Prüfe ob winget verfügbar ist...
winget --version >nul 2>&1
if errorlevel 1 (
    echo  [WARN]  winget nicht gefunden.
    echo          Bitte Python manuell installieren:
    echo          https://www.python.org/downloads/
    echo.
    goto :fail
)
echo  [INFO]  Installiere Python 3 via winget...
winget install --id Python.Python.3 --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo  [ERROR] Python-Installation fehlgeschlagen.
    echo          Bitte manuell installieren: https://www.python.org/downloads/
    goto :fail
)
echo  [OK]    Python wurde installiert.
echo.
echo  [INFO]  Starte neues Terminal um PATH zu aktualisieren...
echo          Bitte install.bat danach erneut ausfuehren.
echo.
pause
goto :fail

:python_ok
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK]    Python !PY_VER! gefunden


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 2: pip prüfen / reparieren
:: ════════════════════════════════════════════════════════════════

python -m pip --version >nul 2>&1
if not errorlevel 1 goto :pip_ok

echo  [INFO]  pip nicht gefunden – wird installiert...
python -m ensurepip --upgrade >nul 2>&1
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] pip konnte nicht installiert werden.
    goto :fail
)

:pip_ok
echo  [OK]    pip gefunden


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 3: Python Scripts-Verzeichnis im PATH prüfen
:: ════════════════════════════════════════════════════════════════

:: Scripts-Pfad dynamisch ermitteln
for /f "delims=" %%p in ('python -c "import sysconfig; print(sysconfig.get_path(\"scripts\"))"') do set SCRIPTS_DIR=%%p

if not defined SCRIPTS_DIR (
    echo  [WARN]  Scripts-Verzeichnis konnte nicht ermittelt werden.
    goto :skip_path
)

:: Prüfen ob Scripts-Dir bereits im PATH ist (Groß-/Kleinschreibung ignorieren)
echo !PATH! | findstr /I /C:"!SCRIPTS_DIR!" >nul 2>&1
if not errorlevel 1 (
    echo  [OK]    Scripts-Verzeichnis ist im PATH: !SCRIPTS_DIR!
    goto :skip_path
)

echo.
echo  [WARN]  Das Python Scripts-Verzeichnis ist nicht im PATH:
echo          !SCRIPTS_DIR!
echo.
set /p FIX_PATH="  PATH automatisch korrigieren? [j/n]: "
echo.

if /i not "!FIX_PATH!"=="j" (
    echo  [INFO]  PATH wird nicht geaendert.
    echo          'local-cli' koennte nach der Installation nicht aufrufbar sein.
    goto :skip_path
)

:: PATH-Laenge prüfen - setx hat 1024-Zeichen-Limit, wir nutzen PowerShell
set PATH_LEN=0
for /f %%i in ('powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('PATH','User').Length"') do set PATH_LEN=%%i

if !PATH_LEN! GTR 4000 (
    echo  [WARN]  User-PATH ist sehr lang (!PATH_LEN! Zeichen).
    echo          Eine Bereinigung des PATH wird empfohlen.
)

:: Dauerhaft in User-PATH schreiben (PowerShell, kein 1024-Zeichen-Limit)
powershell -NoProfile -Command ^
  "$current = [Environment]::GetEnvironmentVariable('PATH','User');" ^
  "if ($current -notlike '*!SCRIPTS_DIR!*') {" ^
  "  [Environment]::SetEnvironmentVariable('PATH', $current + ';!SCRIPTS_DIR!', 'User');" ^
  "  Write-Host '  [OK]    PATH dauerhaft gesetzt (User-Ebene).'" ^
  "} else {" ^
  "  Write-Host '  [OK]    Pfad war bereits vorhanden (kein Duplikat).'" ^
  "}"

:: Auch in der laufenden Session setzen
set "PATH=!PATH!;!SCRIPTS_DIR!"
echo  [OK]    PATH fuer diese Session aktualisiert.

:skip_path


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 4: local-cli-agent installieren
:: ════════════════════════════════════════════════════════════════

echo.
echo  [INFO]  Installiere local-cli-agent aus "%~dp0" ...
echo.
python -m pip install .
if errorlevel 1 (
    echo.
    echo  [ERROR] pip install fehlgeschlagen.
    goto :fail
)
echo.
echo  [OK]    Paket erfolgreich installiert.


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 5: Installation verifizieren
:: ════════════════════════════════════════════════════════════════

where local-cli >nul 2>&1
if errorlevel 1 (
    echo  [WARN]  'local-cli' ist in diesem Terminal noch nicht im PATH.
    echo          Bitte ein neues Terminalfenster oeffnen und erneut pruefen.
    echo          Scripts-Verzeichnis: !SCRIPTS_DIR!
) else (
    echo  [OK]    'local-cli' Befehl ist verfuegbar.
)


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 6: API-Key prüfen / Setup starten
:: ════════════════════════════════════════════════════════════════

set API_KEY_FOUND=0

:: Prüfung 1: .env im Quellordner
if exist "%~dp0.env" (
    findstr /I "NVIDIA_API_KEY" "%~dp0.env" >nul 2>&1
    if not errorlevel 1 set API_KEY_FOUND=1
)

:: Prüfung 2: Umgebungsvariable
if defined NVIDIA_API_KEY (
    if not "!NVIDIA_API_KEY!"=="" set API_KEY_FOUND=1
)

:: Prüfung 3: .env in site-packages (non-editable install)
if !API_KEY_FOUND!==0 (
    for /f "delims=" %%s in ('python -c "import site; print(site.getsitepackages()[0])" 2^>nul') do set SITE_DIR=%%s
    if defined SITE_DIR (
        if exist "!SITE_DIR!\.env" (
            findstr /I "NVIDIA_API_KEY" "!SITE_DIR!\.env" >nul 2>&1
            if not errorlevel 1 set API_KEY_FOUND=1
        )
    )
)

if !API_KEY_FOUND!==1 (
    echo  [OK]    API-Key bereits konfiguriert.
) else (
    echo.
    echo  [INFO]  Kein API-Key gefunden. Setup-Assistent wird gestartet...
    echo          Kostenlosen Key erhalten: https://build.nvidia.com/moonshotai/kimi-k2.5
    echo.
    local-cli --setup
    if errorlevel 1 (
        echo  [WARN]  Setup mit Fehler beendet. Spaeter mit 'local-cli --setup' wiederholen.
    )
)


:: ════════════════════════════════════════════════════════════════
::  FERTIG
:: ════════════════════════════════════════════════════════════════

echo.
echo  ================================================================
echo   Installation abgeschlossen!
echo   Starte 'local-cli' in einem neuen Terminal.
echo  ================================================================
echo.
goto :end

:fail
echo.
echo  ================================================================
echo   Installation FEHLGESCHLAGEN. Fehler oben beheben und erneut
echo   ausfuehren.
echo  ================================================================
echo.
pause
exit /b 1

:end
endlocal
pause
