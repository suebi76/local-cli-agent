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
echo  Dieses Skript entfernt local-cli-agent vollstaendig.
echo  Ollama und LM Studio werden NICHT beruehrt.
echo.


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 1: Python / pip prüfen
:: ════════════════════════════════════════════════════════════════

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python nicht gefunden – Deinstallation nicht moeglich.
    goto :fail
)
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] pip nicht gefunden – Deinstallation nicht moeglich.
    goto :fail
)
echo  [OK]    Python und pip gefunden.


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 2: Paket deinstallieren
:: ════════════════════════════════════════════════════════════════

echo.
:: Prüfen ob das Paket überhaupt installiert ist
python -m pip show local-cli-agent >nul 2>&1
if errorlevel 1 (
    echo  [INFO]  local-cli-agent ist nicht installiert – nichts zu tun.
    goto :cleanup_data
)

echo  [INFO]  Entferne local-cli-agent...
python -m pip uninstall local-cli-agent -y
if errorlevel 1 (
    echo  [WARN]  pip uninstall meldete einen Fehler. Bitte manuell pruefen.
) else (
    echo  [OK]    Paket entfernt.
)


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 3: Benutzerdaten bereinigen
:: ════════════════════════════════════════════════════════════════
::
::  Bei globaler Installation (pip install .) liegen alle Daten in:
::    %USERPROFILE%\.local-cli-agent\
::    -> .env              (Einstellungen / Ports)
::    -> .local-cli-memory.json     (gespeicherte Erinnerungen)
::    -> .local-cli-changelog.json  (Self-Improvement-Log)
::
:: ════════════════════════════════════════════════════════════════

:cleanup_data
echo.
set USER_DATA=%USERPROFILE%\.local-cli-agent
if exist "!USER_DATA!\" (
    echo  [INFO]  Benutzerdaten gefunden: !USER_DATA!
    echo.
    echo          Enthaelt: .env, Erinnerungen, Self-Improvement-Log
    echo.
    set /p DEL_USERDATA="  Benutzerdaten loeschen? [j/n]: "
    echo.
    if /i "!DEL_USERDATA!"=="j" (
        rmdir /s /q "!USER_DATA!" >nul 2>&1
        if not errorlevel 1 (
            echo  [OK]    Benutzerdaten geloescht.
        ) else (
            echo  [WARN]  Konnte nicht vollstaendig loeschen: !USER_DATA!
            echo          Bitte manuell entfernen.
        )
    ) else (
        echo  [INFO]  Benutzerdaten behalten (in: !USER_DATA!^)
    )
) else (
    echo  [INFO]  Keine Benutzerdaten gefunden ^(!USER_DATA!^).
)


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 4: Projektordner-Dateien (nur bei Entwickler-Install)
:: ════════════════════════════════════════════════════════════════
::  Relevant wenn das Paket mit 'pip install -e .' installiert wurde.
::  Bei normalem 'pip install .' sind diese Dateien nicht vorhanden.
:: ════════════════════════════════════════════════════════════════

set DEV_FILES=0
for %%f in ("%~dp0.env" "%~dp0.local-cli-memory.json" "%~dp0.local-cli-changelog.json") do (
    if exist "%%~f" set DEV_FILES=1
)

if !DEV_FILES!==1 (
    echo.
    echo  [INFO]  Entwickler-Dateien im Projektordner gefunden:
    for %%f in (.env .local-cli-memory.json .local-cli-changelog.json) do (
        if exist "%~dp0%%f" echo          %%f
    )
    echo.
    set /p DEL_DEV="  Diese Dateien ebenfalls loeschen? [j/n]: "
    echo.
    if /i "!DEL_DEV!"=="j" (
        call :del_if_exists "%~dp0.env"                      ".env"
        call :del_if_exists "%~dp0.local-cli-memory.json"    ".local-cli-memory.json"
        call :del_if_exists "%~dp0.local-cli-changelog.json" ".local-cli-changelog.json"
    ) else (
        echo  [INFO]  Projektordner-Dateien behalten.
    )
)


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 5: Backup-Dateien bereinigen
:: ════════════════════════════════════════════════════════════════
::  Self-Improve erstellt *.backup.DATUM Dateien im Paketordner.
::  Nach einer globalen Installation liegen diese in site-packages.
::  pip uninstall (Schritt 2) entfernt sie automatisch mit.
::  Im Projektordner koennen noch Backup-Reste vorhanden sein:
:: ════════════════════════════════════════════════════════════════

set HAS_BACKUPS=0
for %%f in ("%~dp0*.backup.*") do set HAS_BACKUPS=1

if !HAS_BACKUPS!==1 (
    echo.
    echo  [INFO]  Backup-Dateien im Projektordner gefunden:
    for %%f in ("%~dp0*.backup.*") do echo          %%~nxf
    echo.
    set /p DEL_BACKUPS="  Backup-Dateien loeschen? [j/n]: "
    echo.
    if /i "!DEL_BACKUPS!"=="j" (
        del /f /q "%~dp0*.backup.*" >nul 2>&1
        echo  [OK]    Backup-Dateien geloescht.
    ) else (
        echo  [INFO]  Backup-Dateien behalten.
    )
)


:: ════════════════════════════════════════════════════════════════
::  HINWEIS: Was NICHT entfernt wird
:: ════════════════════════════════════════════════════════════════

echo.
echo  ================================================================
echo   Hinweise
echo  ================================================================
echo.
echo  Nicht entfernt (absichtlich):
echo.
echo   Python Scripts-Verzeichnis im PATH
echo     ^(wird von allen Python-Tools geteilt, nicht nur local-cli^)
echo.
echo   Ollama und LM Studio
echo     ^(separate Anwendungen – bitte manuell deinstallieren falls gewuenscht^)
echo.
echo   Gespeicherte Konversationen (session_*.md)
echo     ^(liegen im jeweiligen Arbeitsverzeichnis, bitte manuell loeschen^)


:: ════════════════════════════════════════════════════════════════
::  FERTIG
:: ════════════════════════════════════════════════════════════════

echo.
echo  ================================================================
echo   Deinstallation abgeschlossen.
echo  ================================================================
echo.
goto :end


:: ── Hilfsfunktion ────────────────────────────────────────────────
:del_if_exists
if exist "%~1" (
    del /f /q "%~1" >nul 2>&1
    if not errorlevel 1 (
        echo  [OK]    Geloescht: %~2
    ) else (
        echo  [WARN]  Konnte nicht loeschen: %~2
    )
) else (
    echo  [INFO]  Nicht gefunden ^(uebersprungen^): %~2
)
goto :eof


:fail
echo.
echo  ================================================================
echo   Deinstallation fehlgeschlagen.
echo  ================================================================
echo.
pause
exit /b 1

:end
endlocal
pause
