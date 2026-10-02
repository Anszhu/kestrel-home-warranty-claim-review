import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = {".py", ".md", ".bat", ".json", ".txt", ".example"}
SKIP = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "data", "outputs"}

def _files():
    for p in ROOT.rglob("*"):
        if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP) and (p.suffix in TEXT or p.name == ".env.example"):
            yield p

def test_no_machine_specific_absolute_paths():
    pat = re.compile(r"(/mnt/|/home/|/Users/|[A-Za-z]:\\Users|[A-Za-z]:/Users)")
    bad = [str(p.relative_to(ROOT)) for p in _files()
           if p.name != "test_privacy.py" and pat.search(p.read_text(encoding="utf-8", errors="ignore"))]
    assert not bad, bad

def test_importing_modules_needs_no_private_data(tmp_path):
    code = "import src.paths, src.scorer, src.train, src.predict, src.validate, service; print('ok')"
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr

def test_gitignore_protects_private_material():
    g = (ROOT / ".gitignore").read_text()
    for needle in ["data/*", "outputs/*", "*.csv", "*.pdf", ".env", "__pycache__/", ".venv/"]:
        assert needle in g

def test_env_example_has_default_api_url_and_no_secret():
    t = (ROOT / ".env.example").read_text()
    assert "API_BASE_URL=http://127.0.0.1:8000" in t and "KEY" not in t.upper().replace("API_BASE", "")
