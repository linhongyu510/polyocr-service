# PolyOCR Service

[简体中文](README.md)

A multilingual OCR API powered by PaddleOCR 3.x, with optional translation and a separate
PaddleOCR-VL deployment. This is a community project, not an official PaddleOCR component.

## Capabilities and boundaries

- Base OCR calls PaddleOCR 3.x `predict()` and normalizes both 3.x mapping/object results and
  legacy list results.
- 78 languages across the Han, Japanese, Hangul, Latin, Cyrillic, Arabic, Devanagari, Thai and
  Greek scripts. `language` accepts a language code, an English name, or a Chinese name
  (`fr` / `french` / `法文` all resolve to French).
- Languages are validated at the request boundary: an unknown language returns
  `422 unsupported_language` instead of failing later during model loading.
- Byte size, decoded pixel count, image validity, and score thresholds are checked before
  inference.
- Blocking inference runs in a worker pool behind a concurrency semaphore.
- Translation requests have item and total-character limits; provider output must preserve
  the input count.
- HTTP, authentication, validation, and domain failures share one `error` response shape.
- PaddleOCR-VL accepts uploaded content only, rejects URLs, requires a separate API key, and
  enforces an upload limit.
- Browser pages render remote results with `textContent`, never as executable HTML.

Fast tests neither download models nor access the public network. Real OCR downloads model
assets and runs only when its integration test is explicitly enabled. PaddleOCR-VL requires
a separately prepared, mutually compatible GPU, driver, CUDA, and inference stack.

## Installation

CI covers Python 3.10, 3.11, and 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,ocr]"
cp .env.example .env
```

Replace the sample API keys in `.env`, then start the service:

```bash
# Loopback only, recommended for local development
polyocr-service

# Or via uvicorn, with an explicit bind address
uvicorn polyocr.main:create_app --factory --host 127.0.0.1 --port 8000
```

The console script defaults to `127.0.0.1:8000` and also reads `POLYOCR_HOST` /
`POLYOCR_PORT`.

**On bind addresses**: `--host 0.0.0.0` publishes the service on every network
interface. A container needs that — otherwise the mapped port is unreachable, and the
Dockerfile sets it explicitly for that reason — but on a laptop or a shared network it
makes your instance reachable by anyone on the LAN. Widen it deliberately when you
actually want that:

```bash
POLYOCR_HOST=0.0.0.0 polyocr-service        # or polyocr-service --host 0.0.0.0
```

The `python main.py` compatibility entry point also defaults to `127.0.0.1`.

Open `http://localhost:8000/` for the web client or `/docs` for the API documentation.

## API

The health endpoint does not require authentication:

```bash
curl http://localhost:8000/v1/health
```

List supported languages, including PaddleOCR codes, scripts and accepted aliases:

```bash
curl http://localhost:8000/v1/languages
```

OCR accepts either `X-API-Key` or a Bearer token:

```bash
curl -X POST http://localhost:8000/v1/ocr \
  -H "X-API-Key: $POLYOCR_API_KEY" \
  -F "file=@benchmarks/simple_dataset/en.jpg" \
  -F "language=en" \
  -F "score_threshold=0.5"
```

`language` accepts a code, an English name, or a Chinese name. The response always echoes the
canonical code:

```json
{
  "code": 0,
  "message": "Recognition succeeded.",
  "request_id": "...",
  "cost_ms": 412.7,
  "language": "fr",
  "items": [{"text": "Bonjour", "score": 0.99, "bbox": [12, 8, 96, 34]}]
}
```

Translation:

```bash
curl -X POST http://localhost:8000/v2/translate \
  -H "X-API-Key: $POLYOCR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"texts":["Hello"],"target_language":"zh"}'
```

All failures use the same envelope:

```json
{
  "error": {
    "code": "invalid_image",
    "message": "Uploaded file could not be decoded as an image.",
    "request_id": "..."
  }
}
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `POLYOCR_AUTH_ENABLED` | `true` | Enables authentication for base business endpoints |
| `POLYOCR_API_KEY` | none | Required when base authentication is enabled |
| `POLYOCR_CORS_ORIGINS` | `http://localhost:8000` | Comma-separated allowed origins |
| `POLYOCR_MAX_UPLOAD_MB` | `10` | OCR upload byte limit |
| `POLYOCR_MAX_IMAGE_PIXELS` | `25000000` | Decoded image pixel limit |
| `POLYOCR_MAX_CONCURRENCY` | `2` | Concurrent OCR inference limit |
| `POLYOCR_OCR_WORKERS` | `2` | OCR worker thread count |
| `POLYOCR_MAX_TRANSLATION_ITEMS` | `50` | Translation item limit |
| `POLYOCR_MAX_TRANSLATION_CHARS` | `20000` | Translation total-character limit |
| `TRANSLATION_API_KEY` | none | OpenAI-compatible provider key |
| `TRANSLATION_BASE_URL` | OpenAI API | Translation provider base URL |
| `TRANSLATION_MODEL` | `gpt-4o-mini` | Translation model |
| `POLYOCR_VL_API_KEY` | none | Required key for the separate VL service |
| `POLYOCR_VL_MAX_UPLOAD_MB` | `20` | VL upload limit |

The application automatically reads `.env` from its current directory. Never commit `.env`
or real secrets. The base service refuses to start when authentication is enabled without
`POLYOCR_API_KEY`; the VL service always requires `POLYOCR_VL_API_KEY`. Credentialed CORS
cannot use a wildcard origin.

## Docker

```bash
export POLYOCR_API_KEY='replace-with-a-secret'
docker compose up --build
```

The image pins a Python 3.10 baseline, runs as a non-root user, and includes a health check.
The first OCR request downloads model assets into the Compose cache volume.

## PaddleOCR-VL

See [`deployment/paddleocr-vl/README.md`](deployment/paddleocr-vl/README.md).
The VL endpoint does not fetch remote URLs. Clients upload a base64 file and provide the
separate VL credential.

## Tests and verification

```bash
python -m ruff format --check .
python -m ruff check .
python -m pytest -m "not integration"
python -m build
```

Run the fixed-image real OCR E2E explicitly:

```bash
POLYOCR_RUN_OCR_E2E=1 python -m pytest tests/integration/test_real_ocr.py -q
```

This command may download model assets. Container commands and observed results for this
revision are recorded in [`docs/verification.md`](docs/verification.md). CI runs only fast,
offline tests across Python 3.10–3.12.

### Language accuracy benchmark

Measures recognition accuracy per language against the labelled images in
`benchmarks/accuracy_dataset`:

```bash
# A subset; the first run downloads that language's model
python benchmarks/run_accuracy_benchmark.py --languages fr,de,ru

# All 32 labelled languages
python benchmarks/run_accuracy_benchmark.py

# Or exercise a running deployment over HTTP
python benchmarks/run_accuracy_benchmark.py --mode http --server http://localhost:8000
```

It reports `exact` (fraction of lines matched exactly) and `cer` (character error rate),
both independent of detection order. Both are kept because a single confusable character
can drop a line's `exact` to 0 while the text is otherwise correct. See
[`benchmarks/accuracy_dataset/README.md`](benchmarks/accuracy_dataset/README.md).

### Robustness benchmark

Measures accuracy under controlled degradation — blur, compression, rotation, downscaling,
noise and lighting, plus capture-realistic artifacts (directional motion blur, projective
skew, illumination gradients, soft shadows, paper grain):

```bash
python benchmarks/run_robustness_benchmark.py --languages en,fr,ru,zh
python benchmarks/run_robustness_benchmark.py --severity capture
python benchmarks/run_robustness_benchmark.py --compare-preprocess
```

Measured result: rotation, perspective skew, JPEG compression, brightness, contrast,
uneven illumination, soft shadows and paper texture are all essentially free — the
combined "photograph of a page" case (perspective + gradient + grain + compression)
scores 1.000. Only loss of glyph detail breaks recognition: blur beyond about σ2, and
downscaling past roughly 25%.

**Motion blur is the one unsafe failure.** At 15px of travel the service returns
confidently-scored nonsense rather than nothing (`Hello World` → `Heelco Ncotec`), which
a caller cannot distinguish from a correct result. Up to 9px it is unaffected.

`preprocess` is **not implemented**. Five candidate pipelines were measured across all 17
degradations and every one is net negative; autocontrast harmed 11 of 17 (soft shadow
−0.517, paper texture −0.450). Even a *local* `flatten` (divide by blurred background),
included specifically because a global operation cannot correct a lighting gradient, lost
— those cases already scored 0.975–1.000, so there was no headroom and only detail to
lose. `preprocess=true` therefore returns `400 preprocess_unsupported` rather than being
silently ignored. Full data in [`docs/robustness.md`](docs/robustness.md).

### Real photograph benchmark

Everything above is synthetic. This measures genuine phone captures — photographed
receipts from [CORD-v2](https://huggingface.co/datasets/naver-clova-ix/cord-v2)
(CC-BY-4.0) with human word-level transcriptions:

```bash
python benchmarks/run_photo_benchmark.py --limit 15 --compare-preprocess
```

| Metric | Synthetic | Real photographs |
| --- | --- | --- |
| mean score | 0.975 exact | **0.841 word recall** |

**The synthetic numbers are optimistic by roughly 13 points** — previously stated only as
a caveat, now measured. Four of fifteen images are read perfectly, nine score ≥0.727, and
one badly faded thermal receipt scores 0.250.

Three of five preprocessing pipelines have a *positive* mean on real photos, which looked
like it might overturn the decision. Bootstrap testing over 20 000 resamples shows
otherwise: **every 95% CI includes zero and the smallest p is 0.371**. The best-looking
candidate, `combined` (+0.029), drops to **−0.018** once the single outlier image is
excluded, and it harmed 6 of 15 images. The conclusion stands on a narrower basis: on real
photographs preprocessing shows no statistically detectable benefit. Images are downloaded
at runtime and never committed.

Attribution: CORD-v2 is CC-BY-4.0, © NAVER CLOVA IX.

## License

Licensed under the [Apache License 2.0](LICENSE), matching upstream PaddleOCR. Third-party
attribution is recorded in [`NOTICE`](NOTICE).

This repository is an independent, community-maintained service built on PaddleOCR. It is not
an official PaddleOCR component. PaddleOCR models are downloaded at runtime from their original
distributors and remain subject to their own licenses.
