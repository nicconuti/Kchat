from __future__ import annotations

import subprocess
from typing import Iterator, Literal, Callable

ModelName = Literal["mistral", "openchat", "deepseek-r1:14b"]


def _run_ollama(model: str, prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[LLM Error] Model: {model} | Exit Code: {e.returncode}")
        print(e.stderr)
        return ""
    except Exception as ex:
        print(f"[Unexpected Error] Model: {model} | {ex}")
        return ""


def _stream_ollama(model: str, prompt: str) -> Iterator[str]:
    try:
        proc = subprocess.Popen(
            ["ollama", "run", model],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        if proc.stdin:
            proc.stdin.write(prompt)
            proc.stdin.close()

        if proc.stdout:
            while True:
                chunk = proc.stdout.read(1)
                if not chunk:
                    break
                yield chunk

        proc.wait()

    except Exception as e:
        print(f"[Stream Error] Model: {model} | {e}")
        yield ""


# === Public interface ===

def call_mistral(prompt: str) -> str:
    return _run_ollama("mistral", prompt)

def call_openchat(prompt: str) -> str:
    return _run_ollama("openchat", prompt)

def call_deepseek(prompt: str) -> str:
    return _run_ollama("deepseek-coder:6.7b-instruct", prompt)

def stream_openchat(prompt: str) -> str:
    return _stream_ollama("openchat", prompt)
# === Optional dynamic interface ===

def call_local_llm(model: ModelName, prompt: str) -> str:
    return _run_ollama(model, prompt)


def stream_local_llm(model: ModelName, prompt: str) -> Iterator[str]:
    return _stream_ollama(model, prompt)
