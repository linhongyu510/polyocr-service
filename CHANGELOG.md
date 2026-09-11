# Changelog

All notable changes to this project are documented here. This project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Real photograph benchmark** (`benchmarks/run_photo_benchmark.py`) scoring genuine
  phone captures — 15 photographed receipts from CORD-v2 (CC-BY-4.0) with human
  word-level transcriptions — against order-independent word recall. Images are
  downloaded at runtime into a gitignored directory and never committed, with a test
  guarding that.

### Measured

- **The synthetic estimate is optimistic by ~13 points.** Real photographs score
  **0.841** mean word recall against 0.975 exact on synthetic fixtures. Previously this
  gap was only stated as a caveat; it is now measured. Four of fifteen images are read
  perfectly, nine score ≥0.727, and one badly faded thermal receipt scores 0.250.
- **The `preprocess` decision survives, with corrected reasoning.** On real photographs
  three of five pipelines have a *positive* mean, unlike on synthetic degradation.
  Bootstrap testing over 20 000 resamples shows every 95% CI includes zero, smallest
  p = 0.371. The best-looking candidate, `combined` (+0.029), falls to −0.018 once a
  single outlier image is excluded, and harmed 6 of 15 images including −0.357 on one
  that had been reading at 0.929.
- Two explanations for that outlier were tested and both failed: recall correlates with
  global ink contrast at only −0.262 (the lowest-contrast image scores 0.947) and with
  local text-to-background contrast at +0.027. No mechanism is claimed.

### Fixed

- **The `python main.py` compatibility entry point silently bound `0.0.0.0`**, publishing
  the service on every network interface, while the packaged `polyocr-service` console
  script deliberately defaults to `127.0.0.1`. Two entry points to the same product had
  opposite network exposure, and the wide one was the undocumented default. Both now
  default to loopback; `POLYOCR_HOST` / `POLYOCR_PORT` widen it deliberately. The
  container still binds `0.0.0.0` explicitly in its `CMD`, which is correct there.
- **The credential-scanning test audited third-party dependencies.** It walked
  `ROOT.rglob("*")` with no exclusion for virtual environments, so with a `.venv` in the
  repository it read 1735 dependency files — 97% of everything it scanned, 24 MB — and
  any dependency that merely mentioned a forbidden string failed the build with a message
  pointing at the test rather than the file. The scan is now limited to project sources
  and reports the offending path. Verified both ways: a planted dependency file no longer
  fails the build, a planted project file still does and is named.
- Suite runtime dropped from 6.9s to 1.8s as a side effect of not reading 24 MB of
  dependency source on every run.

### Added (tooling and docs)

- Contract tests pinning that no entry point defaults to `0.0.0.0`, that the container
  keeps binding it explicitly, that the root compatibility modules stay pure re-exports,
  and that the credential scan cannot reach outside the project.
- Both READMEs now explain when `0.0.0.0` is appropriate instead of showing it as the
  default invocation.

## [0.4.0] - 2026-09-05

### Fixed

- **`preprocess` was accepted and silently discarded.** `POST /v1/ocr` advertised a
  `preprocess` flag in its OpenAPI schema, returned HTTP 200, then dropped it with
  `del preprocess`. Callers had no way to tell that nothing happened, and three
  scripts in `benchmarks/` sent `preprocess=true`. It now returns
  `400 preprocess_unsupported` pointing at `docs/robustness.md`; `preprocess=false`
  and omitting the field behave as before.
- `benchmarks/run_benchmark.py` leaked a file handle per request by passing an
  unclosed `open()` into `requests.post`.
- Release guards no longer import `tomllib`, which is stdlib only from 3.11 while the
  project supports 3.10. A new AST-based check enforces the declared
  `requires-python` floor so this class of break is caught by tests rather than by a
  single failing CI job.

### Added

- **Robustness benchmark** (`benchmarks/run_robustness_benchmark.py`) measuring
  accuracy under 17 controlled degradations across three tiers — `moderate`, `severe`
  and `capture` — with `--compare-preprocess` to score candidate preprocessing
  pipelines. Findings in `docs/robustness.md`.
- `capture` tier modelling photograph and scan artifacts that global gaussian
  degradation does not reproduce: directional motion blur, projective skew,
  illumination gradients, soft shadows and correlated paper grain.
- `docs/robustness.md`: measured failure profile and the evidence behind not
  implementing `preprocess`.

### Measured

- PP-OCR is unaffected by geometry and lighting. Rotation, perspective skew, JPEG
  quality 5, uneven illumination, soft shadow and paper texture all score 0.950–1.000
  exact against a clean reference of 0.975. The combined photograph case (perspective +
  gradient + grain + compression) scores 1.000.
- Only loss of glyph detail breaks recognition: gaussian blur beyond ~σ2, and
  downscaling past ~25%.
- **Motion blur is the one unsafe failure mode.** At 15px of travel the service returns
  confidently-scored wrong text rather than an empty result (`Hello World` →
  `Heelco Ncotec`), which a caller cannot distinguish from success. Up to 9px is
  unaffected. This corrects the earlier claim that degradation past the limit always
  yields empty output.
- All five preprocessing pipelines are net negative over 17 degradations: autocontrast
  −0.166 mean Δexact (harmed 11/17), combined −0.124, flatten −0.024, upscale −0.022,
  sharpen −0.007. A *local* illumination-flattening pass was included specifically
  because a global operation cannot correct a lighting gradient; it still lost, because
  the cases it targets already scored 0.975–1.000.

## [0.3.0] - 2026-09-05

### Fixed

- **OCR failed for every Latin and Cyrillic language.** `fr`, `de`, `es`, `pt`, `it`,
  `nl`, `ru`, `be` and `uk` were mapped to `latin` / `cyrillic` and passed to
  `PaddleOCR(lang=...)`. Those are recognition-model prefixes, not language codes, so
  PaddleOCR raised `ValueError: No models are available for lang='latin'` and the API
  returned `503 model_unavailable` for every such request. All languages are now mapped
  to codes PaddleOCR accepts, verified against the installed build.
- **Serbian was unreachable by its ISO code.** The catalogue defined `sr-Latn` and
  `sr-Cyrl` but no bare `sr`, so `language=sr` returned `422`. PaddleOCR has no bare
  `sr` either, so it is now mapped explicitly to `rs_latin`, with `sr-Cyrl` still
  available for Cyrillic Serbian. Found by the new accuracy benchmark.
- An unknown `language` now returns `422 unsupported_language` at the request boundary
  instead of failing later during model loading.
- A misconfigured `POLYOCR_DEFAULT_LANGUAGE` now fails at startup instead of making
  every request that omits `language` fail.
- `benchmarks/evaluate_results.py` read `response["data"]`, which the API no longer
  returns, so it reported zero recognised text for every image. It now reads `items`
  and still accepts the older `data` shape.
- The Dockerfile did not copy `LICENSE` / `NOTICE`, which `pyproject.toml` declares as
  `license-files`. The image silently installed a distribution with no license or
  attribution text.

### Added

- Apache-2.0 `LICENSE` matching upstream PaddleOCR, plus a `NOTICE` file carrying the
  upstream attribution required by section 4(d). The repository previously shipped no
  license at all, which left redistribution rights undefined.
- Language coverage expanded from 12 to 78 languages across the Han, Japanese, Hangul,
  Latin, Cyrillic, Arabic, Devanagari, Thai, Greek, Georgian, Tamil and Telugu scripts.
- Language aliases: `fr`, `french` and `法文` all resolve to French. `GET /v1/languages`
  now returns each language's PaddleOCR code, script and accepted aliases.
- **Per-language accuracy benchmark** (`benchmarks/run_accuracy_benchmark.py`) scoring
  recognition against ground truth, reporting exact line match and character error
  rate independently of detection order. Runs in-process or over HTTP against a
  deployment. Current results: 32 languages, 64 images, 0 failures.
- 64 labelled images across 32 languages in `benchmarks/accuracy_dataset/`, recovered
  from `accuracy_test/` on `main` with portable relative paths. The dated one-off run
  reports that accompanied them were not carried over.
- `polyocr-service` console entry point, so an installed distribution can be started
  without the `--factory` uvicorn invocation.
- `py.typed` marker, so downstream type checkers use the package's annotations.
- Packaging metadata: license expression, keywords, trove classifiers and project URLs.
- 97 new tests (28 to 125), covering the language contract, boundary validation, the
  packaging contract, the container's license handling and the benchmark scorer. A new
  integration test checks the language catalogue against real PaddleOCR metadata
  without downloading model weights.
- CI: `twine check` on built distributions, an offline language-catalogue job, and a
  container smoke test that asserts `/v1/health` responds.

### Changed

- `__version__` is read from distribution metadata, making `pyproject.toml` the single
  source of truth. It was previously duplicated in three files.
- Removed the unused `error_schema()` helper and the `log_level` setting that nothing
  read. Log level is now a `polyocr-service --log-level` option.

## [0.2.0] - 2026-09-01

### Fixed

- Removed hardcoded API keys and translation credentials from the source tree.
- Replaced the wildcard CORS policy, which was unsafe with credentialed requests.
- Replaced silent `except` blocks that turned failures into empty successful responses.
- Added the OpenCV runtime libraries the image needs (`libgl1`, `libglib2.0-0`).

### Changed

- Restructured a flat script layout into the `src/polyocr` package with an installable
  `pyproject.toml`, split into API, core, services and schema layers.
- Unified all failures onto a single `error` response shape with a request ID.
- Moved blocking inference into a worker pool behind a concurrency semaphore.
- Added byte-size, pixel-count and image-validity limits ahead of inference.
- Rendered browser results with `textContent` instead of `innerHTML`.
