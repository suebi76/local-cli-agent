# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
model_selector.py – interactive model selection via Ollama / LM Studio backends.
"""
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style

from local_cli_agent.constants import RESET, BOLD, CYAN, YELLOW, GREEN, RED, DIM
from local_cli_agent import backends


_DIALOG_STYLE = Style.from_dict({
    "dialog":              "bg:#1e1e2e",
    "dialog.body":         "bg:#1e1e2e fg:#cdd6f4",
    "dialog frame.label":  "bg:#1e1e2e fg:#89b4fa bold",
    "button":              "bg:#313244 fg:#cdd6f4",
    "button.focused":      "bg:#89b4fa fg:#1e1e2e bold",
    "radio-checked":       "fg:#a6e3a1 bold",
    "radio":               "fg:#6c7086",
})


def _show_compatibility_warning(entry) -> None:
    """
    Option A: Warn if model name suggests it is unsuitable for agent tasks.
    Option B: Show recommended alternatives — ollama pull only for Ollama users,
              plain model names for LM Studio users.
    """
    check = backends.check_model_compatibility(entry)
    if check["ok"]:
        return

    print(f"\n  {YELLOW}⚠  Warnung:{RESET} {check['reason']}")
    print(f"  {DIM}Gewähltes Modell: {entry.name}{RESET}")
    print(f"\n  {CYAN}Empfohlene Alternativen für Agent-Tasks:{RESET}")

    if entry.backend == "ollama":
        # Show ollama pull commands — user can run them directly
        for model, size, desc in backends.RECOMMENDED_MODELS:
            print(f"    {DIM}ollama pull{RESET} {BOLD}{model:<28}{RESET}  {size}  {DIM}{desc}{RESET}")
        print(f"\n  {DIM}Befehl im Terminal ausführen, dann local-cli neu starten.{RESET}")
    else:
        # LM Studio: show model names to search for in LM Studio's model browser
        print(f"  {DIM}In LM Studio → Model Browser nach diesen Modellen suchen:{RESET}")
        for model, size, desc in backends.RECOMMENDED_MODELS:
            print(f"    {BOLD}{model:<28}{RESET}  {size}  {DIM}{desc}{RESET}")
        print(f"\n  {DIM}Modell laden → Local Server starten → local-cli neu starten.{RESET}")

    print()


def show_selector(last_model: str = None):
    """
    Discover models from Ollama and LM Studio, then show an interactive dialog.
    Returns the selected ModelEntry, or None if cancelled or no models found.

    last_model format: "ollama:llama3.2:3b" or "lmstudio:some-model-id"
    """
    models = backends.list_all_models()

    if not models:
        backends.print_no_service_help()
        return None

    # ── Auto-select when exactly one model is available (e.g. LM Studio) ──────
    if len(models) == 1:
        m = models[0]
        print(f"\n  {GREEN}Modell:{RESET} {BOLD}{m.name}{RESET}  {DIM}[{m.backend}]{RESET}")
        _show_compatibility_warning(m)
        return m

    # ── Build radiolist values ─────────────────────────────────────────────────
    values = []
    default = None
    for m in models:
        check = backends.check_model_compatibility(m)
        backend_tag = f"[{m.backend.capitalize():<9}]"
        size_str = f"{m.size_gb:5.1f} GB" if m.size_gb > 0 else "  ?.? GB"
        warn_tag = f"  {YELLOW}⚠{RESET}" if not check["ok"] else ""
        label = f"{backend_tag}  {m.name:<40} {size_str}   {m.description}{warn_tag}"
        values.append((m, label))

        # Pre-select the last used model
        if last_model:
            candidate = f"{m.backend}:{m.model_id}"
            if candidate == last_model or m.model_id == last_model:
                default = m

    if default is None:
        default = models[0]

    services = backends.detect_services()
    service_names = []
    if services.get("ollama"):
        service_names.append("Ollama")
    if services.get("lmstudio"):
        service_names.append("LM Studio")
    service_info = " + ".join(service_names) if service_names else "unbekannt"

    result = radiolist_dialog(
        title="Local CLI Agent – Modell wählen",
        text=(
            "Wähle ein Modell mit den Pfeiltasten und bestätige mit Enter.\n"
            f"Gefunden: {len(models)} Modell(e)  |  Backend: {service_info}"
            f"  |  {YELLOW}⚠{RESET} = für Agent-Tasks nicht empfohlen"
        ),
        values=values,
        default=default,
        style=_DIALOG_STYLE,
    ).run()

    if result is not None:
        _show_compatibility_warning(result)

    return result  # None if user pressed Escape / Cancel