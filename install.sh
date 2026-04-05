#!/usr/bin/env bash
# ================================================================
#  install.sh  -  Local CLI Agent  |  Globale Installation (Linux/Mac)
#  Verwendung:  chmod +x install.sh && ./install.sh
# ================================================================

set -euo pipefail

# Wechsle in das Verzeichnis des Skripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Farben (nur wenn TTY) ────────────────────────────────────────
if [ -t 1 ]; then
    C_RESET="\033[0m"
    C_GREEN="\033[32m"
    C_YELLOW="\033[33m"
    C_RED="\033[31m"
    C_CYAN="\033[36m"
else
    C_RESET="" C_GREEN="" C_YELLOW="" C_RED="" C_CYAN=""
fi

ok()   { echo -e "  ${C_GREEN}[OK]${C_RESET}    $*"; }
info() { echo -e "  ${C_CYAN}[INFO]${C_RESET}  $*"; }
warn() { echo -e "  ${C_YELLOW}[WARN]${C_RESET}  $*"; }
err()  { echo -e "  ${C_RED}[ERROR]${C_RESET} $*"; }

echo ""
echo "  ================================================================"
echo "   Local CLI Agent  |  Globale Installation"
echo "  ================================================================"
echo ""


# ════════════════════════════════════════════════════════════════
#  SCHRITT 1: Python prüfen / installieren
# ════════════════════════════════════════════════════════════════

install_python_macos() {
    if command -v brew &>/dev/null; then
        info "Installiere Python 3 via Homebrew..."
        brew install python3
    else
        err "Homebrew nicht gefunden."
        echo "       Optionen:"
        echo "         1) Homebrew installieren: https://brew.sh"
        echo "         2) Python direkt laden:   https://www.python.org/downloads/"
        exit 1
    fi
}

install_python_linux() {
    if command -v apt-get &>/dev/null; then
        info "Installiere Python 3 via apt..."
        sudo apt-get update -qq && sudo apt-get install -y python3 python3-pip
    elif command -v dnf &>/dev/null; then
        info "Installiere Python 3 via dnf..."
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &>/dev/null; then
        info "Installiere Python 3 via pacman..."
        sudo pacman -S --noconfirm python python-pip
    else
        err "Kein bekannter Paketmanager gefunden (apt/dnf/pacman)."
        echo "       Bitte Python 3.8+ manuell installieren: https://www.python.org/downloads/"
        exit 1
    fi
}

if ! command -v python3 &>/dev/null; then
    err "python3 nicht gefunden."
    echo ""
    read -r -p "  Soll Python automatisch installiert werden? [j/n]: " INSTALL_PY
    echo ""

    if [[ "${INSTALL_PY,,}" == "j" ]]; then
        OS_TYPE="$(uname -s)"
        case "$OS_TYPE" in
            Darwin) install_python_macos ;;
            Linux)  install_python_linux ;;
            *)
                err "Unbekanntes Betriebssystem: $OS_TYPE"
                echo "       Python manuell installieren: https://www.python.org/downloads/"
                exit 1
                ;;
        esac
        # PATH für aktuelle Session aktualisieren
        export PATH="$PATH:/usr/local/bin:/opt/homebrew/bin"
    else
        info "Python manuell installieren: https://www.python.org/downloads/"
        exit 1
    fi
fi

# Python-Version prüfen (≥ 3.8)
PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]; }; then
    err "Python $PY_VER gefunden – mindestens 3.8 erforderlich."
    exit 1
fi

ok "Python $PY_VER gefunden"


# ════════════════════════════════════════════════════════════════
#  SCHRITT 2: pip prüfen / reparieren
# ════════════════════════════════════════════════════════════════

if ! python3 -m pip --version &>/dev/null; then
    info "pip nicht gefunden – wird installiert..."
    python3 -m ensurepip --upgrade 2>/dev/null || true
    if ! python3 -m pip --version &>/dev/null; then
        err "pip konnte nicht installiert werden."
        exit 1
    fi
fi
ok "pip gefunden"


# ════════════════════════════════════════════════════════════════
#  SCHRITT 3: Python Scripts-Verzeichnis im PATH prüfen
# ════════════════════════════════════════════════════════════════

SCRIPTS_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>/dev/null || echo "")

if [ -z "$SCRIPTS_DIR" ]; then
    warn "Scripts-Verzeichnis konnte nicht ermittelt werden."
else
    if echo "$PATH" | grep -qF "$SCRIPTS_DIR"; then
        ok "Scripts-Verzeichnis ist im PATH: $SCRIPTS_DIR"
    else
        echo ""
        warn "Das Python Scripts-Verzeichnis ist nicht im PATH:"
        echo "       $SCRIPTS_DIR"
        echo ""
        read -r -p "  PATH automatisch korrigieren? [j/n]: " FIX_PATH
        echo ""

        if [[ "${FIX_PATH,,}" == "j" ]]; then
            PATH_LINE="export PATH=\"$SCRIPTS_DIR:\$PATH\""

            # ~/.bashrc
            if [ -f "$HOME/.bashrc" ]; then
                if ! grep -qF "$SCRIPTS_DIR" "$HOME/.bashrc"; then
                    echo "" >> "$HOME/.bashrc"
                    echo "# local-cli" >> "$HOME/.bashrc"
                    echo "$PATH_LINE" >> "$HOME/.bashrc"
                    ok "PATH zu ~/.bashrc hinzugefügt"
                else
                    info "Eintrag in ~/.bashrc bereits vorhanden."
                fi
            fi

            # ~/.zshrc
            if [ -f "$HOME/.zshrc" ]; then
                if ! grep -qF "$SCRIPTS_DIR" "$HOME/.zshrc"; then
                    echo "" >> "$HOME/.zshrc"
                    echo "# local-cli" >> "$HOME/.zshrc"
                    echo "$PATH_LINE" >> "$HOME/.zshrc"
                    ok "PATH zu ~/.zshrc hinzugefügt"
                else
                    info "Eintrag in ~/.zshrc bereits vorhanden."
                fi
            fi

            # ~/.profile (Fallback falls weder bashrc noch zshrc vorhanden)
            if [ ! -f "$HOME/.bashrc" ] && [ ! -f "$HOME/.zshrc" ]; then
                echo "" >> "$HOME/.profile"
                echo "# local-cli" >> "$HOME/.profile"
                echo "$PATH_LINE" >> "$HOME/.profile"
                ok "PATH zu ~/.profile hinzugefügt"
            fi

            # Für laufende Session sofort setzen
            export PATH="$SCRIPTS_DIR:$PATH"
            ok "PATH für diese Session aktualisiert."
        else
            info "PATH wird nicht geändert."
            info "'local-cli' könnte nach der Installation nicht direkt aufrufbar sein."
        fi
    fi
fi


# ════════════════════════════════════════════════════════════════
#  SCHRITT 4: local-cli-agent installieren
# ════════════════════════════════════════════════════════════════

echo ""
info "Installiere local-cli-agent aus \"$SCRIPT_DIR\" ..."
echo ""
python3 -m pip install .
echo ""
ok "Paket erfolgreich installiert."


# ════════════════════════════════════════════════════════════════
#  SCHRITT 5: Installation verifizieren
# ════════════════════════════════════════════════════════════════

if command -v local-cli &>/dev/null; then
    ok "'local-cli' Befehl ist verfügbar."
else
    warn "'local-cli' ist in dieser Shell noch nicht im PATH."
    echo "       Bitte ein neues Terminal öffnen oder 'source ~/.bashrc' ausführen."
    echo "       Alternativ direkt aufrufen: python3 -m local_cli_agent.cli"
fi


# ════════════════════════════════════════════════════════════════
#  SCHRITT 6: Modell-Backend einrichten
# ════════════════════════════════════════════════════════════════

echo ""
info "Lokale KI-Modelle via Ollama oder LM Studio:"
echo ""
echo "   OLLAMA (empfohlen – kostenlos, einfach):"
echo "     https://ollama.com installieren, dann:"
echo "       ollama pull llama3.2          # 2 GB, schnell"
echo "       ollama pull qwen2.5-coder     # 4.7 GB, Code"
echo ""
echo "   LM STUDIO (mit GUI, Modell-Browser):"
echo "     https://lmstudio.ai installieren,"
echo "     Modell laden + Tab \"Local Server\" → \"Start Server\""
echo ""

# Prüfe ob Ollama läuft
if curl -s --connect-timeout 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
    ok "Ollama läuft und ist bereit."
else
    info "Ollama läuft nicht – nach Installation: ollama pull llama3.2"
fi

# Prüfe ob LM Studio läuft
if curl -s --connect-timeout 2 http://localhost:1234/v1/models >/dev/null 2>&1; then
    ok "LM Studio Server läuft und ist bereit."
else
    info "LM Studio Server läuft nicht."
fi


# ════════════════════════════════════════════════════════════════
#  FERTIG
# ════════════════════════════════════════════════════════════════

echo ""
echo "  ================================================================"
echo "   Installation abgeschlossen!"
echo "   Starte 'local-cli' in einem neuen Terminal."
echo "  ================================================================"
echo ""
