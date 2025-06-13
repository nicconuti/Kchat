import subprocess

def call_mistral(prompt: str) -> str:
    cmd = ["ollama", "run", "mistral"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, _ = proc.communicate(prompt)
    return out.strip()
