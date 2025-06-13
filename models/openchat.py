import subprocess

def call_openchat(prompt: str) -> str:
    cmd = ["ollama", "run", "openchat"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, _ = proc.communicate(prompt)
    return out.strip()
