# Auris_v0

A voice-controlled PowerShell assistant. Speak naturally — the system transcribes your speech, resolves app paths from your Desktop, queries a local LLM, and executes the resulting PowerShell commands.

---

## Architecture

```
Microphone
    │
    ▼
stt.py              (RealtimeSTT / Whisper base model)
    │ transcribed text
    ▼
main.py :: on_speech()
    │
    ├──► app_index.py       (fuzzy match utterance against Desktop shortcuts)
    │         │ resolved path (name -> full path) or None
    │         ▼
    ├──► ollama_client.py   (stream prompt + optional path context to Ollama)
    │         │ streamed JSON response
    │         ▼
    └──► executor.py        (validate verbs, blacklist check, run via PowerShell)
```

---

## Modules

| File | Role |
|---|---|
| `main.py` | Entry point. Manages conversation history, STT loop, wires all modules. |
| `stt.py` | Thin wrapper around `RealtimeSTT`. Streams partial transcriptions, fires callback on complete utterance. |
| `app_index.py` | Scans Desktop for `.exe`, `.lnk`, `.url` files. Exposes fuzzy search via `rapidfuzz`. |
| `ollama_client.py` | REST wrapper for local Ollama instance. Supports streaming, injects resolved path context into last user message. |
| `executor.py` | Parses LLM JSON output. Validates commands against an allowlist of PowerShell verbs and a blacklist of dangerous patterns. Executes via `subprocess`. |

---

## Setup

### Requirements

Install:
```bash
pip install -r requirements.txt
```

### Ollama

1. Install [Ollama](https://ollama.com)
2. Pull the model:
```bash
ollama pull llama3.1:8b
```
3. Ollama must be running locally on `http://localhost:11434` before starting the app.

### Run

```bash
python main.py
```

---

## Security Model

The executor enforces a two-layer check on every command before running it:

**Allowlist** — only these PowerShell verbs are permitted

**Blacklist** — these patterns are always rejected regardless of verb

The system prompt sent to the LLM also includes the allowed verb list, so the model is guided to stay within bounds before execution even occurs.

---

## Known Limitations

- `SCAN_DIRS` only covers `~/Desktop` as of now. Apps without shortcuts there will not be resolved, and the LLM may hallucinate paths for them.
- Fuzzy match threshold is 40 (out of 100). Short or partial names like "scaling" for "Lossless Scaling" may fall below it.
- The LLM occasionally produces malformed JSON. These responses are caught, logged, and discarded from history.
- No TTS — responses are JSON only, printed to console.
- Windows only.

---

## Current State

> **Last updated:** 2026-03-03  
> **Status:** Working proof of concept — voice → STT → LLM → PowerShell execution is fully wired and functional.

### What works
- Single-instance startup (multiprocessing guard in place)
- Desktop app index built at `main.py` startup, fuzzy-matched per utterance
- Resolved paths injected into LLM prompt context
- Streamed LLM responses via Ollama REST API
- JSON validation before history append
- Executor with verb allowlist + pattern blacklist running commands via `subprocess`
- System prompt includes allowed verb list, sourced directly from `executor.ALLOWED_VERBS`

### Known bugs / immediate next tasks
- **Hallucinated paths for unindexed apps** — if an app has no Desktop shortcut, the LLM invents a path. Fix: extend `SCAN_DIRS` in `app_index.py` to cover Start Menu and common install dirs, or return an empty list when no index match is found.
- **Fuzzy threshold too strict** — "scaling" fails to match "lossless scaling". Lower threshold from 40 → x in `app_index.search()`.
- **No feedback on blocked commands** — executor prints to console but the user gets no voice/audio feedback. Future: add TTS for executor status.

### Suggested next features (in no specific order)
1. **TTS output** — read LLM responses or executor status aloud (e.g. `pyttsx3` or `edge-tts`)
2. **Extend app index scan dirs** — Start Menu (`%APPDATA%\Microsoft\Windows\Start Menu`) and `C:\ProgramData\Microsoft\Windows\Start Menu`
3. **Wake word** — only activate on "Hey Jarvis" or similar, rather than always-on
4. **Command history log** — persist executed commands to a local file for auditing
5. **Not limited to PowerShell** — Able to do more actions that are not constrainted by a command prompt, e.g. open a URL in the browser.
6. **Configurable LLM** — allow users to specify their own Ollama model or even a remote API endpoint
7. **Contextual awareness** — maintain a short-term memory of recent commands and their outcomes to enable follow-up commands like "open the folder I just created"
8. **Multistep instructions** —handling of LLM responses for complex tasks that require multiple commands, e.g. "create a new folder named 'new_app' on the Desktop and run `git init` inside it"