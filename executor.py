"""executor.py -- Parse and execute LLM-generated PowerShell commands."""
import json
import subprocess

ALLOWED_VERBS = {
    "start-process",
    "get-childitem",
    "get-location",
    "set-location",
    "get-date",
    "get-uptime",
    "get-process",
    "stop-process",
    "get-service",
    "clear-host",
}

BLOCKED_PATTERNS = [
    "invoke-expression", "iex",
    "invoke-command",
    "remove-item", "ri", "del", "rm",
    "format-",
    "new-object",
    "downloadstring", "downloadfile",
    "net user", "net localgroup",
    "reg ", "regedit",
    "set-executionpolicy",
    "disable-", "enable-",
    "out-file", "set-content", "add-content",
    "move-item", "copy-item", "rename-item",
]


def is_safe(command: str) -> bool:
    low = command.strip().lower()

    for pattern in BLOCKED_PATTERNS:
        if pattern in low:
            print(f"[executor] BLOCKED (blacklist match: '{pattern}'): {command}")
            return False

    first_token = low.split()[0] if low else ""
    if first_token not in ALLOWED_VERBS:
        print(f"[executor] BLOCKED (verb not whitelisted: '{first_token}'): {command}")
        return False

    return True


def run(reply: str):
    try:
        data = json.loads(reply)
    except json.JSONDecodeError:
        print("[executor] Invalid JSON, skipping.")
        return

    commands = data.get("powershell_instructions", [])
    if not commands:
        print("[executor] No commands to run.")
        return

    for cmd in commands:
        if not is_safe(cmd):
            continue
        print(f"[executor] Running: {cmd}")
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            print(f"[executor] Output:\n{result.stdout.strip()}")
        if result.stderr.strip():
            print(f"[executor] Error:\n{result.stderr.strip()}")