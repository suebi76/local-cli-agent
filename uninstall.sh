#!/usr/bin/env bash
# ================================================================
#  uninstall.sh  -  Local CLI Agent  |  Deinstallation (Linux/Mac)
#  Verwendung:  chmod +x uninstall.sh && ./uninstall.sh
# ================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
echo "   Local CLI Agent  |  Deinstallation"
echo "  ================================================================"
echo ""


# ════════════════════════════════════════════════════════════════
#  SCHRITT 1: Python / pip prüfen
# ════════════════════════════════════════════════════════════════

if ! command -v python3 &>/dev/null; then
    err "python3 nicht gefunden – Deinstallation nicht möglich."
    exit 1
fi
ok "Python gefunden."

if ! python3 -m pip --version &>/dev/null; then
    err "pip nicht gefunden – Deinstallation nicht möglich."
    exit 1
fi


# ════════════════════════════════════════════════════════════════
#  SCHRITT 2: Paket deinstallieren
# ════════════════════════════════════════════════════════════════

info "Entferne local-cli-agent Paket..."
if python3 -m pip uninstall local-cli-agent -y 2>/dev/null; then
    ok "Paket entfernt."
else
    warn "pip uninstall meldete einen Fehler. Das Paket war möglicherweise nicht installiert."
fi


# ════════════════════════════════════════════════════════════════
#  SCHRITT 3: Config-Dateien im Projektordner bereinigen
# ════════════════════════════════════════════════════════════════

echo ""
echo "  Folgende Config-Dateien können im Projektordner vorhanden sein:"
echo "    .env                       (Einstellungen)"
echo "    .local-cli-memory.json     (gespeicherte Erinnerungen)"
echo "    .local-cli-changelog.json  (Self-Improvement-Log)"
echo ""
read -r -p "  Diese Dateien löschen? [j/n]: " DEL_LOCAL
echo ""

if [[ "${DEL_LOCAL,,}" == "j" ]]; then
    for f in ".env" ".local-cli-memory.json" ".local-cli-changelog.json"; do
        fp="$SCRIPT_DIR/$f"
        if [ -f "$fp" ]; then
            rm -f "$fp" && ok "Gelöscht: $f" || warn "Konnte nicht löschen: $f"
        else
            info "Nicht gefunden: $f"
        fi
    done
else
    info "Lokale Config-Dateien behalten."
fi


# ════════════════════════════════════════════════════════════════
#  SCHRITT 4: User-Datenordner (~/.local-cli-agent/) prüfen
# ════════════════════════════════════════════════════════════════

USER_DATA="$HOME/.local-cli-agent"
if [ -d "$USER_DATA" ]; then
    echo ""
    info "User-Datenordner gefunden: $USER_DATA"
    echo ""
    read -r -p "  Auch diesen Ordner löschen? [j/n]: " DEL_USERDATA
    echo ""
    if [[ "${DEL_USERDATA,,}" == "j" ]]; then
        rm -rf "$USER_DATA" && ok "User-Datenordner gelöscht." || warn "Konnte nicht löschen: $USER_DATA"
    else
        info "User-Datenordner behalten."
    fi
fi


# ════════════════════════════════════════════════════════════════
#  SCHRITT 5: Backup-Dateien bereinigen
# ════════════════════════════════════════════════════════════════

BACKUP_FILES=$(find "$SCRIPT_DIR" -maxdepth 1 -name "*.backup.*" 2>/dev/null || true)
if [ -n "$BACKUP_FILES" ]; then
    echo ""
    info "Backup-Dateien gefunden:"
    echo "$BACKUP_FILES" | while read -r f; do echo "       $f"; done
    echo ""
    read -r -p "  Backup-Dateien löschen? [j/n]: " DEL_BACKUPS
    echo ""
    if [[ "${DEL_BACKUPS,,}" == "j" ]]; then
        find "$SCRIPT_DIR" -maxdepth 1 -name "*.backup.*" -delete
        ok "Backup-Dateien gelöscht."
    else
        info "Backup-Dateien behalten."
    fi
fi


# ════════════════════════════════════════════════════════════════
#  SCHRITT 6: PATH-Einträge aus Shell-Profilen entfernen
# ════════════════════════════════════════════════════════════════

SCRIPTS_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>/dev/null || echo "")

if [ -n "$SCRIPTS_DIR" ]; then
    PROFILE_CHANGED=0
    for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$RC_FILE" ] && grep -qF "$SCRIPTS_DIR" "$RC_FILE" 2>/dev/null; then
            echo ""
            info "PATH-Eintrag für local-cli in $RC_FILE gefunden."
            read -r -p "  Aus $RC_FILE entfernen? [j/n]: " DEL_PATH
            if [[ "${DEL_PATH,,}" == "j" ]]; then
                # Remove lines containing the scripts dir and the "# local-cli" comment above
                grep -v "# local-cli" "$RC_FILE" | grep -v "$SCRIPTS_DIR" > "${RC_FILE}.tmp" && mv "${RC_FILE}.tmp" "$RC_FILE"
                ok "PATH-Eintrag aus $RC_FILE entfernt."
                PROFILE_CHANGED=1
            fi
        fi
    done
    if [ "$PROFILE_CHANGED" -eq 1 ]; then
        info "Shell neu starten oder 'source ~/.bashrc' ausführen, damit PATH aktualisiert wird."
    fi
fi


# ════════════════════════════════════════════════════════════════
#  FERTIG
# ════════════════════════════════════════════════════════════════

echo ""
echo "  ================================================================"
echo "   Deinstallation abgeschlossen."
echo "  ================================================================"
echo ""
