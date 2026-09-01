import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READMES = (ROOT / "README.md", ROOT / "README_EN.md")


def test_readmes_are_bilingual_and_state_project_status() -> None:
    chinese, english = (path.read_text() for path in READMES)
    assert "README_EN.md" in chinese
    assert "README.md" in english
    assert "非 PaddleOCR 官方项目" in chinese
    assert "not an official PaddleOCR project" in english
    assert 'pip install -e ".[dev]"' in chinese
    assert 'pip install -e ".[dev]"' in english
    assert "docker compose up --build" in chinese
    assert "docker compose up --build" in english


def test_local_markdown_links_exist() -> None:
    missing = []
    for readme in READMES:
        for target in re.findall(r"\[[^]]+]\(([^)]+)\)", readme.read_text()):
            if "://" in target or target.startswith("#"):
                continue
            path = ROOT / target.split("#", 1)[0]
            if not path.exists():
                missing.append(f"{readme.name}: {target}")
    assert missing == []


def test_documentation_is_covered_by_repository_hygiene() -> None:
    for readme in READMES:
        assert readme.resolve().is_relative_to(ROOT)
