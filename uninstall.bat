@echo off
setlocal EnableDelayedExpansion

:: ================================================================
::  uninstall.bat  -  Local CLI Agent  |  Deinstallation (Windows)
:: ================================================================

cd /d "%~dp0"

echo.
echo  ================================================================
echo   Local CLI Agent  ^|  Deinstallation
echo  ================================================================
echo.

:: ════════════════════════════════════════════════════════════════
::  SCHRITT 1: Python / pip prüfen
:: ════════════════════════════════════════════════════════════════

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python nicht gefunden - Deinstallation nicht moeglich.
    goto :fail
)
echo  [OK]    Python gefunden.

python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] pip nicht gefunden - Deinstallation nicht moeglich.
    goto :fail
)


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 2: Paket deinstallieren
:: ════════════════════════════════════════════════════════════════

echo  [INFO]  Entferne local-cli-agent Paket...
python -m pip uninstall local-cli-agent -y
if errorlevel 1 (
    echo  [WARN]  pip uninstall meldete einen Fehler.
    echo          Das Paket war moeglicherweise nicht installiert.
) else (
    echo  [OK]    Paket entfernt.
)


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 3: Config-Dateien bereinigen (Quellordner)
:: ════════════════════════════════════════════════════════════════

echo.
echo  Folgende Config-Dateien koennen im Projektordner vorhanden sein:
echo    .env                  (API-Key)
echo    .kimi-memory.json     (gespeicherte Erinnerungen)
echo    .kimi-changelog.json  (Self-Improvement-Log)
echo.
set /p DEL_LOCAL="  Diese Dateien loeschen? [j/n]: "
echo.

if /i "!DEL_LOCAL!"=="j" (
    call :delete_if_exists "%~dp0.env" ".env"
    call :delete_if_exists "%~dp0.kimi-memory.json" ".kimi-memory.json"
    call :delete_if_exists "%~dp0.kimi-changelog.json" ".kimi-changelog.json"
    call :delete_if_exists "%~dp0kimi.py.pre-refactor" "kimi.py.pre-refactor"
) else (
    echo  [INFO]  Lokale Config-Dateien behalten.
)


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 4: Config-Dateien in site-packages prüfen
:: ════════════════════════════════════════════════════════════════

for /f "delims=" %%s in ('python -c "import site; print(site.getsitepackages()[0])" 2^>nul') do set SITE_DIR=%%s

if not defined SITE_DIR goto :skip_site

:: Prüfen ob überhaupt eine Config-Datei dort liegt
set SITE_HAS_FILES=0
for %%f in (.env .kimi-memory.json .kimi-changelog.json) do (
    if exist "!SITE_DIR!\%%f" set SITE_HAS_FILES=1
)

if !SITE_HAS_FILES!==0 goto :skip_site

echo.
echo  [INFO]  Config-Dateien in site-packages gefunden:
echo          !SITE_DIR!
echo.
set /p DEL_SITE="  Auch diese loeschen? [j/n]: "
echo.

if /i "!DEL_SITE!"=="j" (
    call :delete_if_exists "!SITE_DIR!\.env" "site-packages/.env"
    call :delete_if_exists "!SITE_DIR!\.kimi-memory.json" "site-packages/.kimi-memory.json"
    call :delete_if_exists "!SITE_DIR!\.kimi-changelog.json" "site-packages/.kimi-changelog.json"
) else (
    echo  [INFO]  site-packages Config-Dateien behalten.
)

:skip_site


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 5: Backup-Dateien bereinigen
:: ════════════════════════════════════════════════════════════════

set HAS_BACKUPS=0
for %%f in ("%~dp0kimi.py.backup.*") do set HAS_BACKUPS=1

if !HAS_BACKUPS!==1 (
    echo.
    echo  [INFO]  Backup-Dateien gefunden (kimi.py.backup.*):
    for %%f in ("%~dp0kimi.py.backup.*") do echo          %%f
    echo.
    set /p DEL_BACKUPS="  Backup-Dateien loeschen? [j/n]: "
    echo.
    if /i "!DEL_BACKUPS!"=="j" (
        del /f /q "%~dp0kimi.py.backup.*" >nul 2>&1
        echo  [OK]    Backup-Dateien geloescht.
    ) else (
        echo  [INFO]  Backup-Dateien behalten.
    )
)


:: ════════════════════════════════════════════════════════════════
::  FERTIG
:: ════════════════════════════════════════════════════════════════

echo.
echo  ================================================================
echo   Deinstallation abgeschlossen.
echo  ================================================================
echo.
goto :end


:: ── Hilfsfunktion: Datei löschen wenn vorhanden ─────────────────
:delete_if_exists
if exist "%~1" (
    del /f /q "%~1" >nul 2>&1
    if not errorlevel 1 (
        echo  [OK]    Geloescht: %~2
    ) else (
        echo  [WARN]  Konnte nicht loeschen: %~2
    )
) else (
    echo  [INFO]  Nicht gefunden: %~2
)
goto :eof


:fail
echo.
echo  ================================================================
echo   Deinstallation FEHLGESCHLAGEN.
echo  ================================================================
echo.
pause
exit /b 1

:end
endlocal
pause
