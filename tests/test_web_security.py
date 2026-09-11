from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_web_uses_text_content_for_remote_results() -> None:
    paths = (
        ROOT / "src/polyocr/web/index.html",
        ROOT / "src/polyocr/web/translation.html",
        ROOT / "deployment/paddleocr-vl/static/index.html",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "textContent" in text
        assert "innerHTML" not in text


SCANNED_SUFFIXES = {".html", ".json", ".md", ".py", ".sh", ".yaml", ".yml"}

# Directories that are never ours to audit. Without these exclusions the scan below
# walked into `.venv` and read ~1735 dependency files (97% of everything it looked at,
# 24 MB), so any third-party file that merely mentioned one of the forbidden strings
# failed the build with a message pointing at this test rather than at the dependency.
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "site-packages",
    "build",
    "dist",
    "tests",
    ".eggs",
}


def repository_sources() -> list[Path]:
    """Files that belong to this project, excluding vendored and generated trees."""
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix in SCANNED_SUFFIXES
        and not any(part in EXCLUDED_DIRS for part in path.parts)
        and not any(part.endswith(".egg-info") for part in path.parts)
    ]


def test_secret_scan_does_not_reach_outside_the_project() -> None:
    """The scan must not audit dependencies, or it reports their content as our leak."""
    scanned = repository_sources()
    assert scanned, "the secret scan matched no files at all"
    stray = [
        path.relative_to(ROOT).as_posix()
        for path in scanned
        if any(part in {".venv", "venv", "site-packages", "node_modules"} for part in path.parts)
    ]
    assert not stray, f"scan reached vendored files: {stray[:5]}"


def test_legacy_entrypoints_do_not_contain_credentials_or_runtime_config_api() -> None:
    forbidden = (
        "PolyNex-" + "PolyOCR-" + "2025xm",
        "782b52f0-" + "d5b6-" + "488b-" + "9fdd-" + "0a9026d3a0c0",
        "183." + "250.90.218",
        "43." + "137.12.144",
        "10." + "206.0.6",
    )
    # Report the offending file rather than concatenating everything, so a hit is
    # actionable instead of just proving that something somewhere matched.
    offenders: list[str] = []
    for path in repository_sources():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for value in (*forbidden, "/v1/translation/config", "update_translation_config"):
            if value in text:
                offenders.append(f"{path.relative_to(ROOT).as_posix()} contains a forbidden value")
    assert not offenders, offenders

    assert not (ROOT / "index.html").exists()
    assert not (ROOT / "translation.html").exists()
    assert not (ROOT / "frontend_server.py").exists()
