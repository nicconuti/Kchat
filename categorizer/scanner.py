from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile

EXTS = {".pdf", ".docx", ".xlsx", ".txt", ".html", ".htm"}


def scan(path: Path) -> tuple[list[Path], TemporaryDirectory | None]:
    """Return relevant text files inside path or ZIP and a tmpdir if used."""
    if path.is_file() and path.suffix.lower() == ".zip":
        tmp = TemporaryDirectory()
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp.name)
        base = Path(tmp.name)
        return [p for p in base.rglob("*") if p.suffix.lower() in EXTS], tmp
    return [p for p in path.rglob("*") if p.suffix.lower() in EXTS], None
