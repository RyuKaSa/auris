"""ollama_client.py -- Ollama REST API wrapper functions."""
import json
import requests

BASE_URL = "http://localhost:11434"
MODEL = "llama3.1:8b"


def _build_prompt(messages):
    prompt = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            prompt += f"System: {content}\n\n"
        elif role == "user":
            prompt += f"User: {content}\n"
        elif role == "assistant":
            prompt += f"Assistant: {content}\n"
    prompt += "Assistant: "
    return prompt


def get_available_models():
    response = requests.get(f"{BASE_URL}/api/tags", timeout=5)
    response.raise_for_status()
    return [m["name"] for m in response.json().get("models", [])]


def stream_chat(messages):
    prompt = _build_prompt(messages)
    response = requests.post(f"{BASE_URL}/api/generate", json={
        "model": MODEL,
        "prompt": prompt,
        "stream": True,
    }, timeout=60, stream=True)
    response.raise_for_status()
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            chunk = data.get("response", "")
            if chunk:
                yield chunk
            if data.get("done"):
                break


def stream_chat_with_context(messages, context):
    """Inject resolved path context into the last user message before sending."""
    messages = messages.copy()
    messages[-1] = {
        "role": "user",
        "content": messages[-1]["content"] + f"\n\nResolved paths:\n{context}"
    }
    yield from stream_chat(messages)