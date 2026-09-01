FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 polyocr

WORKDIR /app
COPY . .
RUN python -m pip install ".[ocr]" && chown -R polyocr:polyocr /app

USER polyocr
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:8000/v1/health || exit 1

CMD ["uvicorn", "polyocr.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
