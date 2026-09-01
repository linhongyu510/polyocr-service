#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对 simple_dataset 中的每种语言 1 张图调用 16110 /v1/ocr，
计算简单准确率（是否至少包含目标语言关键短语/是否非空），并输出耗时等指标。
为了避免语言特定 GOLD 依赖，这里以“是否非空文本”为基础，
并返回原始结果供人工核对。
"""

import json
import os
import time
import argparse
from pathlib import Path
import requests

def call(server, img_path: Path, language: str, api_key: str, score: float):
    files = {
        'file': (img_path.name, open(img_path, 'rb'), 'image/jpeg')
    }
    data = {
        'language': language,
        'preprocess': 'true',
        'score': str(score)
    }
    headers = {"X-API-Key": api_key} if api_key else {}
    r = requests.post(f"{server}/v1/ocr", files=files, data=data, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://localhost:8000")
    ap.add_argument("--api-key", default=os.getenv("POLYOCR_API_KEY", ""))
    ap.add_argument('--dataset', default='benchmarks/simple_dataset/simple_manifest.json')
    ap.add_argument('--out', default='benchmarks/simple_results.json')
    ap.add_argument('--score', type=float, default=0.5)
    args = ap.parse_args()

    with open(args.dataset, 'r', encoding='utf-8') as f:
        items = json.load(f)

    results = []
    for it in items:
        lang = it['language']
        path = Path(it['path'])
        start = time.time()
        res = call(args.server, path, lang, args.api_key, args.score)
        elapsed = time.time() - start
        data = res.get('data', []) if isinstance(res, dict) else []
        texts = [d.get('text', '') for d in data if isinstance(d, dict)]
        non_empty = any(t.strip() for t in texts)
        results.append({
            'language': lang,
            'image': str(path),
            'elapsed': round(elapsed, 3),
            'non_empty': bool(non_empty),
            'texts': texts,
            'raw': res
        })

    # 简单“准确率”：非空比例
    total = len(results)
    acc = sum(1 for r in results if r['non_empty']) / max(total, 1)
    summary = {
        'total': total,
        'non_empty_rate': round(acc, 4),
        'avg_elapsed': round(sum(r['elapsed'] for r in results) / max(total, 1), 3)
    }

    out = Path(args.out)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'summary': summary, 'results': results}, f, ensure_ascii=False, indent=2)
    print('✅ 简单评测完成，结果写入', out)

if __name__ == '__main__':
    main()

