# PolyOCR Service

English | [简体中文](README.md)

![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088ff)
![Python](https://img.shields.io/badge/Python-3.10--3.12-3776ab)

**Powered by PaddleOCR**

PolyOCR Service is a self-hosted OCR HTTP service with consistent responses, API-key
authentication, an optional translation adapter, and a small web interface. This is a community
project and **not an official PaddleOCR project**.

The repository owner has not selected a license, so this project does not display a license badge
or claim a specific open-source license.

## Preview

After startup, open `http://localhost:8000/` to upload an image and inspect structured results. The
translation page is at `http://localhost:8000/static/translation.html`. The UI sends the API key
from its password field only with the current request and never persists it in browser storage.

## Supported capabilities

- `POST /v1/ocr` recognizes one image with language, score-threshold, and preprocessing options.
- `GET /v1/languages` returns the supported language mapping.
- `GET /v1/health` checks service health without downloading a model.
- `POST /v2/translate` provides optional translation through an OpenAI-compatible provider.
- OCR models are cached by language; uploads are bounded and errors have a stable structure.

Fast tests do not download models. Real OCR inference requires the `ocr` extra and may download
PaddleOCR models on first use.

## Architecture

![PolyOCR architecture](docs/assets/architecture.svg)

See [Architecture](docs/architecture.md) for boundaries between the core API, translation provider,
and optional VL service.

## Installation matrix

| Scenario | Python | Command |
| --- | --- | --- |
| Development and fast tests | 3.10–3.12 | `pip install -e ".[dev]"` |
| Local OCR | 3.10–3.12 | `pip install -e ".[ocr]"` |
| Development with OCR | 3.10–3.12 | `pip install -e ".[dev,ocr]"` |
| CPU container | Docker | `docker compose up --build` |

Consult PaddlePaddle's official compatibility matrix for platform and architecture support.

## CPU Docker

```bash
export POLYOCR_API_KEY='replace-with-a-random-secret'
docker compose up --build
```

Compose has no real default secret and fails immediately when `POLYOCR_API_KEY` is missing. Models
are persisted in the `polyocr-models` named volume. The container runs as a non-root user and uses
`/v1/health` for its health check.

## Local startup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev,ocr]"
cp .env.example .env
uvicorn polyocr.main:create_app --factory --host 127.0.0.1 --port 8000
```

You may set `POLYOCR_AUTH_ENABLED=false` for local development. Enable authentication and use a
high-entropy secret before exposing the service.

## OCR example

```bash
curl --fail http://localhost:8000/v1/ocr \
  -H "X-API-Key: ${POLYOCR_API_KEY}" \
  -F "file=@sample.png" \
  -F "language=zh" \
  -F "score_threshold=0.5" \
  -F "preprocess=true"
```

A successful response contains a request ID, duration, language, and line-oriented `items`. The
service never echoes the API key in its response.

## Translation example

Translation is disabled by default. Configure an OpenAI-compatible endpoint before calling it:

```bash
export POLYOCR_TRANSLATION_API_KEY='provider-secret'
export POLYOCR_TRANSLATION_BASE_URL='http://localhost:8001/v1'
export POLYOCR_TRANSLATION_MODEL='your-model'

curl --fail http://localhost:8000/v2/translate \
  -H "X-API-Key: ${POLYOCR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"texts":["hello"],"target_language":"zh"}'
```

Without provider configuration, the endpoint returns `503` with `translation_not_configured` and
does not attempt a network request.

## Configuration

All settings use the `POLYOCR_` prefix:

| Variable | Default | Purpose |
| --- | --- | --- |
| `POLYOCR_AUTH_ENABLED` | `false` | Require an API key |
| `POLYOCR_API_KEY` | empty | Service access secret |
| `POLYOCR_CORS_ORIGINS` | `[]` | Allowed origins as JSON |
| `POLYOCR_MAX_UPLOAD_MB` | `10` | Maximum upload size |
| `POLYOCR_DEFAULT_LANGUAGE` | `zh` | Default OCR language |
| `POLYOCR_TRANSLATION_API_KEY` | empty | Enables translation when non-empty |
| `POLYOCR_TRANSLATION_BASE_URL` | local example | OpenAI-compatible endpoint |
| `POLYOCR_TRANSLATION_MODEL` | `change-me` | Translation model name |

## Security

Do not commit `.env` files, credentials, public or private deployment IPs, logs, caches, or model
files. Credentials previously committed to Git must be revoked and rotated at the provider; removing
them from the current tree does not remove history. See the [Security guide](docs/security.md).

## Testing

```bash
pip install -e ".[dev]"
python -m ruff format --check .
python -m ruff check .
python -m pytest -q
```

Tests use in-memory backends and `httpx.MockTransport`; the fast suite does not call external
services.

## Benchmarks

The fixed small dataset and reproduction command are documented in
[Benchmark guide](benchmarks/README.md). Benchmark output is generated data and must not be
committed. Do not report performance numbers unless the benchmark was actually run.

## VL deployment

PaddleOCR-VL is a separate optional service with its own variables and dependencies. See
[VL deployment](deployment/paddleocr-vl/README.md).

## Roadmap

- Validate end-to-end OCR with a fixed image on supported platforms.
- Add deployment examples for rate limiting, reverse proxies, and observability.
- Add release metadata after the repository owner selects a license.

## Contributing

Run Ruff, the full test suite, and repository hygiene tests before submitting changes. For behavior
changes, add a failing test first and then implement the smallest fix.

## License and attribution

The license is pending confirmation by the repository owner. PolyOCR Service uses PaddleOCR as an
optional OCR engine; the PaddleOCR name and project remain the property of their respective owners.
