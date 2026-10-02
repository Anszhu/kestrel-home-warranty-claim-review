"""Project-relative paths and small helpers. No absolute paths anywhere."""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
CFG = ROOT / "src" / "model_config.json"
METRICS = ROOT / "validation" / "metrics.json"
REQUIRED_FILES = ["train.csv", "test_unlabelled.csv", "partners.csv", "products.csv"]

class MissingDataError(FileNotFoundError):
    pass

def missing_files(data_dir: Path = DATA, names=REQUIRED_FILES) -> list[str]:
    return [n for n in names if not (Path(data_dir) / n).exists()]

def require(names, data_dir: Path = DATA) -> None:
    miss = missing_files(data_dir, names)
    if miss:
        raise MissingDataError(
            "Private Kestrel input files are not present. Place these files in the "
            f"'data/' folder of the project: {', '.join(miss)}. See data/README.md."
        )

def load_env() -> None:
    """Tiny .env reader (KEY=VALUE); real environment variables win."""
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def api_base_url() -> str:
    load_env()
    return os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
