from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_LITERALS = (
    "PolyNex-PolyOCR-2025xm",
    "782b52f0-d5b6-488b-9fdd-0a9026d3a0c0",
    "43.137.12.144",
    "183.250.90.218",
    "10.206.0.6",
)
ABSOLUTE_V1_FETCH = re.compile(r"""fetch\(\s*['"]http://[^'"]+/v1""")


def tracked_text_files() -> list[tuple[Path, str]]:
    names = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    files = []
    for raw_name in filter(None, names):
        path = ROOT / raw_name.decode()
        if not path.is_file():
            continue
        try:
            files.append((path, path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue
    return files


def test_tracked_web_files_do_not_contain_known_credentials_or_hosts() -> None:
    violations = []
    for path, text in tracked_text_files():
        relative = path.relative_to(ROOT)
        legacy_root_web = len(relative.parts) == 1 and relative.name in {
            "index.html",
            "translation.html",
            "frontend_server.py",
        }
        if relative.parts[0] != "web" and not legacy_root_web:
            continue
        if path.name == ".env.example":
            continue
        for literal in FORBIDDEN_LITERALS:
            if literal in text:
                violations.append(f"{relative}: {literal}")
        if ABSOLUTE_V1_FETCH.search(text):
            violations.append(f"{relative}: absolute HTTP v1 fetch")

    assert violations == []
