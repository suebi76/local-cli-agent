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

:: Status-Flags fuer die abschliessende Zusammenfassung
set NEED_REOPEN_TERMINAL=0
set NEED_OLLAMA_MODEL=0
set NEED_LMS_SERVER=0


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 1: Python prüfen / installieren  (mind. 3.10 nötig)
:: ════════════════════════════════════════════════════════════════

python --version >nul 2>&1
if not errorlevel 1 goto :python_found

echo  [INFO]  Python wurde nicht gefunden.
echo.
set /p INSTALL_PY="  Soll Python automatisch installiert werden? [j/n]: "
echo.

if /i "!INSTALL_PY!"=="j" goto :install_python
echo  [INFO]  Bitte Python 3.10+ manuell installieren:
echo          https://www.python.org/downloads/
echo.
goto :fail

:install_python
winget --version >nul 2>&1
if errorlevel 1 (
    echo  [WARN]  winget nicht verfuegbar.
    echo          Bitte Python 3.10+ manuell installieren:
    echo          https://www.python.org/downloads/
    goto :fail
)
echo  [INFO]  Installiere Python 3 via winget...
winget install --id Python.Python.3 --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo  [ERROR] Python-Installation fehlgeschlagen.
    echo          Bitte manuell installieren: https://www.python.org/downloads/
    goto :fail
)
echo  [OK]    Python installiert.
echo.
echo  [INFO]  Neues Terminalfenster oeffnen und install.bat erneut ausfuehren.
echo.
pause
goto :fail

:python_found
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK]    Python !PY_VER! gefunden

:: Mindestversion 3.10 prüfen
for /f "tokens=1,2 delims=." %%a in ("!PY_VER!") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
set VERSION_OK=0
if !PY_MAJOR! GTR 3 set VERSION_OK=1
if !PY_MAJOR! EQU 3 if !PY_MINOR! GEQ 10 set VERSION_OK=1
if !VERSION_OK!==0 (
    echo.
    echo  [ERROR] Python 3.10 oder hoeher wird benoetigt. Gefunden: !PY_VER!
    echo          Update: https://www.python.org/downloads/
    echo.
    goto :fail
)


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 2: pip prüfen / reparieren
:: ════════════════════════════════════════════════════════════════

python -m pip --version >nul 2>&1
if not errorlevel 1 goto :pip_ok

echo  [INFO]  pip nicht gefunden – wird repariert...
python -m ensurepip --upgrade >nul 2>&1
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] pip konnte nicht installiert werden.
    goto :fail
)

:pip_ok
echo  [OK]    pip gefunden


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 3: Python Scripts-Verzeichnis im PATH sicherstellen
:: ════════════════════════════════════════════════════════════════

for /f "delims=" %%p in ('python -c "import sysconfig; print(sysconfig.get_path(\"scripts\"))"') do set SCRIPTS_DIR=%%p

if not defined SCRIPTS_DIR (
    echo  [WARN]  Scripts-Verzeichnis konnte nicht ermittelt werden.
    goto :skip_path
)

echo !PATH! | findstr /I /C:"!SCRIPTS_DIR!" >nul 2>&1
if not errorlevel 1 (
    echo  [OK]    Scripts-Verzeichnis im PATH: !SCRIPTS_DIR!
    goto :skip_path
)

echo.
echo  [WARN]  Python Scripts-Verzeichnis fehlt im PATH:
echo          !SCRIPTS_DIR!
echo.
set /p FIX_PATH="  PATH automatisch dauerhaft korrigieren? [j/n]: "
echo.

if /i not "!FIX_PATH!"=="j" (
    echo  [INFO]  PATH nicht geaendert. 'local-cli' koennte nicht aufrufbar sein.
    goto :skip_path
)

for /f %%i in ('powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('PATH','User').Length"') do set PATH_LEN=%%i
if !PATH_LEN! GTR 4000 (
    echo  [WARN]  User-PATH ist sehr lang ^(!PATH_LEN! Zeichen^). Bereinigung empfohlen.
)

powershell -NoProfile -Command ^
  "$cur = [Environment]::GetEnvironmentVariable('PATH','User');" ^
  "if ($cur -notlike '*!SCRIPTS_DIR!*') {" ^
  "  [Environment]::SetEnvironmentVariable('PATH', $cur + ';!SCRIPTS_DIR!', 'User');" ^
  "  Write-Host '  [OK]    PATH dauerhaft gesetzt.'" ^
  "} else {" ^
  "  Write-Host '  [OK]    Eintrag war bereits vorhanden.'" ^
  "}"

set "PATH=!PATH!;!SCRIPTS_DIR!"
echo  [OK]    PATH fuer diese Session aktualisiert.
set NEED_REOPEN_TERMINAL=1

:skip_path


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 4: local-cli-agent installieren / aktualisieren
:: ════════════════════════════════════════════════════════════════

echo.
echo  [INFO]  Installiere / aktualisiere local-cli-agent...
echo.
python -m pip install --upgrade .
if errorlevel 1 (
    echo.
    echo  [ERROR] Installation fehlgeschlagen.
    goto :fail
)
echo.
echo  [OK]    Paket erfolgreich installiert.


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 5: Befehl 'local-cli' prüfen
:: ════════════════════════════════════════════════════════════════

where local-cli >nul 2>&1
if errorlevel 1 (
    echo  [WARN]  'local-cli' noch nicht im PATH dieses Terminals.
    echo          Nach dem Schliessen dieses Fensters in einem neuen Terminal pruefen.
    set NEED_REOPEN_TERMINAL=1
) else (
    echo  [OK]    Befehl 'local-cli' ist aufrufbar.
)


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 6: Ollama prüfen
:: ════════════════════════════════════════════════════════════════

echo.
echo  [INFO]  Pruefe Ollama...

curl -s --connect-timeout 2 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo  [INFO]  Ollama laeuft nicht.
    echo          Starten: Ollama-App oeffnen (laeuft danach automatisch im Hintergrund^)
    echo          Modell:  ollama pull llama3.2
    set NEED_OLLAMA_MODEL=1
    goto :check_lms
)

echo  [OK]    Ollama laeuft.

:: Modell-Check: ollama list gibt Header + je Zeile ein Modell aus
set HAS_MODELS=0
ollama list >nul 2>&1
if not errorlevel 1 (
    for /f "skip=1 delims=" %%m in ('ollama list 2^>nul') do (
        if not "%%m"=="" set HAS_MODELS=1
    )
)
if !HAS_MODELS!==1 (
    echo  [OK]    Ollama-Modelle gefunden.
) else (
    echo  [WARN]  Kein Ollama-Modell installiert.
    echo          Empfehlung: ollama pull llama3.2        ^(2 GB, schnell^)
    echo          oder:       ollama pull qwen2.5-coder   ^(4.7 GB, besser fuer Code^)
    set NEED_OLLAMA_MODEL=1
)


:: ════════════════════════════════════════════════════════════════
::  SCHRITT 7: LM Studio prüfen
:: ════════════════════════════════════════════════════════════════

:check_lms
echo.
echo  [INFO]  Pruefe LM Studio...

curl -s --connect-timeout 2 http://localhost:1234/v1/models >nul 2>&1
if errorlevel 1 (
    echo  [INFO]  LM Studio Server laeuft nicht.
    echo          Zum Starten:
    echo            1. LM Studio oeffnen
    echo            2. Tab "Developer" ^(oder "Local Server"^) auswaehlen
    echo            3. Modell auswaehlen und laden
    echo            4. "Start Server" klicken
    set NEED_LMS_SERVER=1
) else (
    echo  [OK]    LM Studio Server laeuft und ist bereit.
)


:: ════════════════════════════════════════════════════════════════
::  FERTIG – Zusammenfassung
:: ════════════════════════════════════════════════════════════════

echo.
echo  ================================================================
echo   Installation abgeschlossen!
echo  ================================================================

:: Ausstehende Schritte ausgeben
set ACTIONS=0
if !NEED_OLLAMA_MODEL!==1 set ACTIONS=1
if !NEED_LMS_SERVER!==1 set ACTIONS=1

if !ACTIONS!==1 (
    echo.
    echo  Vor dem ersten Start noch erledigen:
    echo.
    if !NEED_OLLAMA_MODEL!==1 (
        echo   [Ollama] Modell laden ^(einmalig, im Terminal^):
        echo            ollama pull llama3.2
        echo.
    )
    if !NEED_LMS_SERVER!==1 (
        echo   [LM Studio] Server starten:
        echo            LM Studio oeffnen -^> Developer -^> Start Server
        echo.
    )
)

echo.
if !NEED_REOPEN_TERMINAL!==1 (
    echo   Schritt 1:  Dieses Fenster schliessen
    echo   Schritt 2:  Neues Terminal oeffnen  ^(CMD oder PowerShell^)
    echo   Schritt 3:  Eingeben:  local-cli
) else (
    echo   Jetzt starten:  local-cli
)
echo.
echo  ================================================================
echo   Was du mit dem Agenten machen kannst:
echo  ================================================================
echo.
echo   /profile          15 Agenten-Profile  ^(Vibe-Coder, Debugger,
echo                     Refactor, Security, Tester, Docs, ...^)
echo.
echo   /orchestrate      Master-Orchestrator: komplexe Aufgaben werden
echo                     automatisch in Spezialisten-Schritte aufgeteilt
echo                     ^(Architekt -> Backend -> Tester -> Security^)
echo.
echo   /mission          Mehrstufige Mission: Agent plant und fuehrt
echo                     eine Aufgabe Schritt fuer Schritt aus
echo.
echo   /autotest         Auto-Test-Loop: Tests nach jeder Dateiänderung
echo                     automatisch ausfuehren  ^(z.B. /autotest pytest tests/^)
echo.
echo   /watch            Verzeichnis beobachten, Agent reagiert auf
echo                     jede Dateiänderung automatisch
echo.
echo   /undo             Letzte Dateiänderungen rueckgaengig machen
echo                     ^(kein Git-Commit noetig^)
echo.
echo   Tipp: /help zeigt alle Befehle im laufenden Agenten.
echo.
echo  ================================================================
echo.

goto :end

:fail
echo.
echo  ================================================================
echo   Installation fehlgeschlagen. Bitte Fehler oben beheben
echo   und install.bat erneut ausfuehren.
echo  ================================================================
echo.
pause
exit /b 1

:end
endlocal
pause
