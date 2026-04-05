# Promotion Materials — local-cli-agent

Repository: https://github.com/suebi76/local-cli-agent

---

## Reddit — r/LocalLLaMA (highest impact)

**Title:**
> I built a self-improving terminal agent that runs 100% locally — Mission Mode, Orchestrator, Undo, Watch Mode, 15 profiles

**Body:**
> Hey r/LocalLLaMA,
>
> I've been building **local-cli-agent** — a coding assistant for the terminal that runs entirely on Ollama or LM Studio. No cloud, no API key, no data leaving your machine.
>
> What makes it different from other local agents:
>
> **🏗️ Orchestrator** — type a complex task, the agent auto-detects complexity, builds a specialist plan (Architect → Backend → Tester → Verification → Security → Docs) and executes it step by step. Each step runs with the right specialist profile. Verification is always inserted automatically.
>
> **⚡ 15 Agent Profiles** — switch personality per task: Vibe-Coder (just make it work), Refactor (split 800-line monoliths), Reviewer, Debugger, Frontend, Backend, Tester, Security, Docs, Performance, Architect, DevOps, Verifikation
>
> **↩️ Undo System** — every file change is snapshotted. `/undo` restores any previous state. No git commit required.
>
> **👁️ Watch Mode** — monitors a directory, triggers the agent on every file change. Great for AI-assisted TDD.
>
> **🧠 Project Memory** — auto-detects your project type and injects context (language, deps, git branch, last commit) into every prompt. Never have to explain your setup again.
>
> **🔁 Auto-Test Loop** — enable once, the agent runs your tests after every file write and self-corrects on failure.
>
> **🔧 Self-Improvement** — the agent can read and edit its own source code (with mandatory backup + syntax check before writing).
>
> Works with any Ollama or LM Studio model. `qwen2.5-coder:7b` is the sweet spot for tool-calling.
>
> GitHub: https://github.com/suebi76/local-cli-agent
>
> Would love feedback — especially on which models people are using and what features matter most.

---

## Reddit — r/Python

**Title:**
> local-cli-agent v2.4.0 — terminal AI agent with Orchestrator, 15 profiles, Undo, Watch Mode (Ollama/LM Studio, no API key)

**Body:**
> A Python terminal agent that orchestrates multiple specialist sub-agents for complex tasks.
>
> ```bash
> pip install local-cli-agent   # (once on PyPI)
> # or:
> git clone https://github.com/suebi76/local-cli-agent && ./install.bat
> ```
>
> New in v2.4: Master-Orchestrator — type a complex prompt, it auto-detects complexity, generates a specialist plan and executes it with the right AI persona per step (Architect, Backend, Tester, Security, Docs...). Verification step auto-inserted whenever code is written.
>
> Also: Undo system (snapshots before every file change), Watch Mode (fs polling triggers agent on change), 15 built-in profiles, Auto-Test Loop, Project Memory.
>
> 100% local — Ollama or LM Studio. No cloud, no API key, no subscriptions.
>
> https://github.com/suebi76/local-cli-agent

---

## Hacker News — Show HN

**Title:**
> Show HN: local-cli-agent – terminal AI agent with orchestrator, undo, watch mode (Ollama/LM Studio)

**Body:**
> I built a self-improving AI coding assistant for the terminal. It runs entirely on local models via Ollama or LM Studio — no API key, no cloud, no data leaving the machine.
>
> The interesting part is the Orchestrator: when you type a complex task, it auto-detects complexity, asks the LLM to produce a specialist plan (Architect → Backend → Tester → Verification → Security → Docs), and executes each step with the appropriate persona injected into the system prompt. Each step gets a context summary of all previous steps. Verification is always auto-inserted before docs when code steps are present.
>
> Other features that I haven't seen combined before:
> - Undo system: every write_file/edit_file auto-snapshots; /undo restores without git
> - Watch mode: polls via os.stat(), triggers agent on file change (no watchdog dep)
> - Project memory: scans cwd, injects project context (lang, deps, git, README) into every prompt
> - Auto-test loop: after every file write, runs your test command; agent sees failure and self-corrects
> - 15 agent profiles: each is a focused system-prompt extension (Vibe-Coder, Refactor, Reviewer, Debugger, Frontend, Backend, Tester, Security, Docs, Performance, Architect, DevOps, Verification)
> - Self-improvement: agent can edit its own .py source with mandatory backup + syntax check
>
> https://github.com/suebi76/local-cli-agent

---

## Twitter / X

**Tweet 1 (main):**
> 🤖 local-cli-agent v2.4 — AI coding assistant for the terminal, 100% local
>
> New: Master-Orchestrator
> Type a complex task → agent plans which specialist handles each step:
> 🏛️ Architect → ⚙️ Backend → 🧪 Tester → ✅ Verification → 🛡️ Security → 📝 Docs
>
> No cloud. No API key. Ollama or LM Studio.
>
> github.com/suebi76/local-cli-agent
>
> #LocalLLM #Ollama #AI #DevTools #OpenSource

**Tweet 2 (Undo feature):**
> Ever wanted Ctrl+Z for AI-generated code changes?
>
> local-cli-agent has a built-in Undo system: every file write auto-snapshots. /undo restores any previous state instantly — no git commit needed.
>
> /checkpoint before-big-refactor → /undo 5 later
>
> github.com/suebi76/local-cli-agent
> #AI #DevTools #LocalLLM

**Tweet 3 (Watch Mode):**
> AI-assisted TDD in your terminal:
>
> /autotest pytest tests/
> /watch ./src "run tests and fix what fails"
>
> Agent watches your files, runs tests after every change, self-corrects on failure. 100% local via Ollama/LM Studio.
>
> github.com/suebi76/local-cli-agent
> #TDD #AI #LocalLLM #DevTools

---

## Dev.to / Hashnode Article Title Ideas

- "I built a local AI orchestrator that assigns specialists per task — here's how it works"
- "Building a self-improving terminal agent with Ollama: Undo system, Watch Mode, and 15 profiles"
- "Why I stopped using cloud AI for coding and built my own local agent"

---

## Awesome Lists to Submit

Submit a PR to these repositories with a one-liner:

**awesome-python:**
> - [local-cli-agent](https://github.com/suebi76/local-cli-agent) - Self-improving AI coding assistant for the terminal with Ollama/LM Studio, orchestrator, undo system, watch mode and 15 agent profiles.

**awesome-llm / awesome-local-ai:**
> - [local-cli-agent](https://github.com/suebi76/local-cli-agent) - Terminal coding agent with master orchestrator, 15 specialist profiles, undo system and watch mode. Runs on Ollama or LM Studio. No API key.

**awesome-chatgpt:**
> - [local-cli-agent](https://github.com/suebi76/local-cli-agent) - Local alternative to cloud coding assistants. Full tool use, orchestrator, undo, watch mode.

Relevant awesome lists:
- https://github.com/vinta/awesome-python
- https://github.com/underlines/awesome-marketing-datascience/
- https://github.com/steven2358/awesome-generative-ai
- https://github.com/Hannibal046/Awesome-LLM
- https://github.com/ai-collection/ai-collection

---

## PyPI — Publish with one command

The package is built and ready in /dist/.
To publish (needs a free PyPI account + API token):

```bash
# 1. Register at https://pypi.org/account/register/
# 2. Create API token at https://pypi.org/manage/account/token/
# 3. Upload:
twine upload dist/*
# Enter: __token__ as username, your token as password
```

After publishing, users can install with:
```bash
pip install local-cli-agent
```

---

## GitHub Profile README Badge

```markdown
[![local-cli-agent](https://img.shields.io/github/stars/suebi76/local-cli-agent?style=social)](https://github.com/suebi76/local-cli-agent)
```

---

## One-liner description for all platforms

> Self-improving AI coding assistant for the terminal. Runs 100% locally via Ollama or LM Studio. Master orchestrator, 15 specialist profiles, undo system, watch mode, auto-test loop. No cloud, no API key.
