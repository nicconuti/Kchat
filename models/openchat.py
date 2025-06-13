import subprocess
from typing import Iterator

def call_openchat(prompt: str) -> str:
    cmd = ["ollama", "run", "openchat"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, _ = proc.communicate(prompt)
    return out.strip()


def stream_openchat(prompt: str) -> Iterator[str]:
    """Yield the OpenChat response incrementally."""
    cmd = ["ollama", "run", "openchat"]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None
    proc.stdin.write(prompt)
    proc.stdin.close()

    assert proc.stdout is not None
    while True:
        ch = proc.stdout.read(1)
        if not ch:
            break
        yield ch
    proc.wait()
