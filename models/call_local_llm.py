import subprocess
from typing import Iterator, Literal

ModelName = Literal["openchat", "mistral", "deepseek-coder:6.7b-instruct"]

def call_local_llm(model: ModelName, prompt: str) -> str:
    """Call a local Ollama model and return the full response."""
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
        print(f"[LLM Error] Model: {model} | Exit: {e.returncode}")
        print(e.stderr)
        return ""


def stream_local_llm(model: ModelName, prompt: str) -> Iterator[str]:
    """Stream LLM response char by char from Ollama model."""
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
        print(f"[Stream LLM Error] {e}")
        yield ""
