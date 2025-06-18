import logging
import subprocess
from typing import Iterator, Literal

# Configurazione del logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ModelName = Literal["mistral", "openchat", "deepseek-r1:14b"]

def _run_ollama(model: str, prompt: str) -> str:
    try:
        logger.info(f"Running model: {model} with prompt length: {len(prompt)} characters")
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"[{model}]: {result.stdout}...")  
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"[LLM Error] Model: {model} | Exit Code: {e.returncode}")
        logger.error(e.stderr)
        return ""
    except Exception as ex:
        logger.error(f"[Unexpected Error] Model: {model} | {ex}")
        return ""


def _stream_ollama(model: str, prompt: str) -> Iterator[str]:
    try:
        logger.info(f"Starting stream for model {model} with prompt length: {len(prompt)}")
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
                logger.debug(f"Streamed chunk: {chunk}")
                yield chunk

        proc.wait()

    except Exception as e:
        logger.error(f"[Stream Error] Model: {model} | {e}")
        yield ""


# === Public interface ===

def call_mistral(prompt: str) -> str:
    logger.info("Calling Mistral model.")
    return _run_ollama("mistral", prompt)

def call_openchat(prompt: str) -> str:
    logger.info("Calling OpenChat model.")
    return _run_ollama("openchat", prompt)

def call_deepseek(prompt: str) -> str:
    logger.info("Calling DeepSeek model.")
    return _run_ollama("deepseek-r1:14b", prompt)

def call_llama(prompt: str) -> str:
    logger.info("Calling DeepSeek model.")
    return _run_ollama("llama3:8b-instruct", prompt)

def stream_openchat(prompt: str) -> str:
    logger.info("Streaming OpenChat model.")
    return _stream_ollama("openchat", prompt)


# === Optional dynamic interface ===

def call_local_llm(model: ModelName, prompt: str) -> str:
    logger.info(f"Calling local LLM model: {model}")
    return _run_ollama(model, prompt)


def stream_local_llm(model: ModelName, prompt: str) -> Iterator[str]:
    logger.info(f"Streaming local LLM model: {model}")
    return _stream_ollama(model, prompt)
