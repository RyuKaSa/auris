"""main.py -- mic -> STT -> Ollama."""
import json

import stt
import ollama_client
import app_index
import executor

from executor import ALLOWED_VERBS

SYSTEM_PROMPT = (
    "You are a voice-controlled PowerShell assistant.\n"
    "Rules:\n"
    "- Respond with ONLY a valid JSON object. No markdown, no explanation, no extra text.\n"
    '- Format: {"powershell_instructions": ["command1", "command2"]}\n'
    "- If resolved paths are provided, you MUST use Start-Process with that exact path.\n"
    "- Example: {\"powershell_instructions\": [\"Start-Process 'C:\\\\path\\\\to\\\\app.lnk'\"]}\n"
    "- NEVER invent commands or paths. If no resolved path is given and the intent is unclear, return an empty list.\n"
    "- NEVER use raw CLI names like 'docker' or 'chrome' as commands."
    f"- You may ONLY use these PowerShell verbs: {', '.join(sorted(ALLOWED_VERBS))}\n"
    "- Any command using a verb not in that list will be rejected."
)

history = []
index = {}


def on_speech(text):
    text = text.strip()
    if not text:
        return

    print(f"\n[You] {text}")
    history.append({"role": "user", "content": text})

    match = app_index.search(text, index)
    context = f"{match[0]} -> {match[1]}" if match else ""
    if match:
        print(f"[index] matched: {match[0]} -> {match[1]}")

    print("[AI] ", end="", flush=True)
    reply = ""
    if context:
        gen = ollama_client.stream_chat_with_context(history, context)
    else:
        gen = ollama_client.stream_chat(history)

    for chunk in gen:
        print(chunk, end="", flush=True)
        reply += chunk
    print()

    try:
        json.loads(reply)
    except json.JSONDecodeError:
        print("[warn] LLM returned invalid JSON, discarding from history.")
        return

    history.append({"role": "assistant", "content": reply})
    executor.run(reply)


def main():
    global history, index
    index = app_index.build_index()
    print(f"[index] {len(index)} apps found on Desktop: {list(index.keys())}")
    recorder = stt.create_recorder()
    print("Ready. Speak naturally. Ctrl+C to stop.\n")
    try:
        while True:
            stt.get_next_utterance(recorder, on_speech)
    except KeyboardInterrupt:
        stt.shutdown_recorder(recorder)
        print("\nStopped.")


if __name__ == "__main__":
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    main()