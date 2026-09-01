from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_dockerfile_runs_factory_as_non_root_with_healthcheck() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "USER polyocr" in dockerfile
    assert "polyocr.main:create_app" in dockerfile
    assert '"--factory"' in dockerfile
    assert "/v1/health" in dockerfile


def test_compose_reads_api_key_from_environment() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()
    assert "POLYOCR_API_KEY" in compose
    assert "${POLYOCR_API_KEY" in compose
