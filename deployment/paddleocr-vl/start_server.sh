#!/usr/bin/env bash
set -euo pipefail

for name in PADDLE_OCR_SERVER_HOST PADDLE_OCR_SERVER_PORT VLM_SERVER_URL; do
    if [ -z "${!name:-}" ]; then
        echo "错误: 必须设置 ${name}" >&2
        exit 1
    fi
done

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${script_dir}"
exec python3 app.py
