from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_LITERALS = (
    "PolyNex-PolyOCR-" + "2025xm",
    "782b52f0-d5b6-" + "488b-9fdd-0a9026d3a0c0",
    "43.137." + "12.144",
    "183.250." + "90.218",
    "10.206." + "0.6",
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


def test_tracked_files_do_not_contain_known_credentials_or_hosts() -> None:
    violations = []
    for path, text in tracked_text_files():
        if path.name == ".env.example":
            continue
        for literal in FORBIDDEN_LITERALS:
            if literal in text:
                violations.append(f"{path.relative_to(ROOT)}: {literal}")
        if ABSOLUTE_V1_FETCH.search(text):
            violations.append(f"{path.relative_to(ROOT)}: absolute HTTP v1 fetch")

    assert violations == []


def test_generated_artifacts_are_not_tracked() -> None:
    tracked = [path.relative_to(ROOT) for path, _ in tracked_text_files()]
    violations = [
        str(path)
        for path in tracked
        if path.suffix in {".log", ".pyc"}
        or "__pycache__" in path.parts
        or path.parts[:2] in {("accuracy_test", "reports"), ("accuracy_test", "results")}
    ]
    assert violations == []
